import os
import asyncio
import requests
import re
import subprocess
import json
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union
from dotenv import load_dotenv
#from playwright.async_api import async_playwright, Browser, BrowserContext, Route, Request as PlaywrightRequest
from patchright.async_api import async_playwright, Browser, BrowserContext, Route, Request as PlaywrightRequest
#from playwright_stealth import stealth_async
from fake_useragent import UserAgent

#import html2text
import markdownify
from html_sanitizer import Sanitizer
sanitizer = Sanitizer()  # default configuration

# Load environment variables
load_dotenv()

RESOURCES_EXCLUDED = ['image', 'stylesheet', 'media', 'font','other']

# Configuration from environment
ADS_BLOCKED_DOMAINS = json.loads(os.getenv('ADS_BLOCKED_DOMAINS', []))
ADS_BLOCKLIST_URL = os.getenv('ADS_BLOCKLIST_URL')
ADS_BLOCKLIST_PATH = os.getenv('ADS_BLOCKLIST_PATH')

BLOCK_MEDIA = os.getenv('BLOCK_MEDIA', 'False').upper() == 'TRUE'
PROXY_SERVER = os.getenv('PROXY_SERVER')
PROXY_USERNAME = os.getenv('PROXY_USERNAME')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')

# Global browser and context instances
browser: Browser = None
context: BrowserContext = None

class FirecrawlScape(BaseModel):
    url: str
    formats: list[str] = ["markdown"]
    onlyMainContent: bool = True
    includeTags: list[str] = None
    excludeTags: list[str] = None
    headers: dict = None
    waitFor: int = 0
    mobile: bool = False
    skipTlsVerification: bool = False
    timeout: int = 30000
    jsonOptions: dict = None
    actions: list[dict] = None
    location: dict = {"country": "US", "languages":""}
    removeBase64Images: bool = False
    blockAds: bool = True


class UrlModel(BaseModel):
    url: str
    wait_after_load: int = 0
    timeout: int = 15000
    headers: dict = None

class MultipleUrlModel(BaseModel):
    urls: Union[str, list[str]]
    wait_after_load: int = 0
    timeout: int = 15000
    headers: dict = None

def is_valid_url(url: str) -> bool:
    pattern = r'^(http|https):\/\/([\w.-]+)(\.[\w.-]+)+([\/\w\.-]*)*\/?$'
    return bool(re.match(pattern, url))


def get_error(status_code: int) -> str:
    if 400 <= status_code < 500:
        return "Client error"
    elif 500 <= status_code < 600:
        return "Server error"
    return "Unknown error"


def update_ads_blocklist_from_url():
    try:
        # Download the blocklist
        response = requests.get(ADS_BLOCKLIST_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Split the content by lines and add each line to the list
        to_block = response.text.splitlines()

        # Split the content by lines and filter out lines starting with #
        to_block = [
            line.strip() for line in response.text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        global ADS_BLOCKED_DOMAINS
        ADS_BLOCKED_DOMAINS.extend(to_block)

        print(f"Blocklist: {ADS_BLOCKLIST_URL} downloaded. {len(ADS_BLOCKED_DOMAINS)} domains blocked.")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the blocklist: {e}")

def update_ads_blocklist_from_file():
    try:
    # Open the file and read its contents
        with open(ADS_BLOCKLIST_PATH, "r") as file:
            # Read all lines and filter out lines starting with #
            to_block = [
                line.strip() for line in file.readlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        
        global ADS_BLOCKED_DOMAINS
        ADS_BLOCKED_DOMAINS.extend(to_block)

        print(f"Blocklist: {ADS_BLOCKLIST_PATH} updated. {len(ADS_BLOCKED_DOMAINS)} domains blocked.")
    except FileNotFoundError:
        print(f"Error: The file '{ADS_BLOCKLIST_PATH}' was not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
    

@asynccontextmanager
async def lifespan(app: FastAPI):
    global browser, context

    # Startup logic
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    )
    
    user_agent = UserAgent(browsers=['Chrome']).random
    
    viewport = {'width': 1920, 'height': 1080}
    context_options = {'user_agent': user_agent, 'viewport': viewport}

    if PROXY_SERVER:
        print(f"Using proxy server {PROXY_SERVER}")
        context_options['proxy'] = {
            'server': PROXY_SERVER,
            **({'username': PROXY_USERNAME, 'password': PROXY_PASSWORD} 
               if PROXY_USERNAME and PROXY_PASSWORD else {})
        }
    else:
        print("⚠️ WARNING: No proxy server provided")

    context = await browser.new_context(**context_options)

    if BLOCK_MEDIA:
        print("Blocking medias enabled")
    else:
        print("Blocking medias disabled")
    
    if ADS_BLOCKLIST_PATH:
        update_ads_blocklist_from_file()
    elif ADS_BLOCKLIST_URL:
        update_ads_blocklist_from_url()
    else:
        print("Ads blocking disabled.")

    async def block_elements(route: Route, request: PlaywrightRequest):
        hostname = urlparse(request.url).hostname
        #if any(domain in hostname for domain in ADS_BLOCKED_DOMAINS):
        if hostname in ADS_BLOCKED_DOMAINS:
            #print(f"{hostname} blocked")
            await route.abort()
        elif BLOCK_MEDIA:
            if request.resource_type in RESOURCES_EXCLUDED:
                await route.abort()
                #print(f"{request.resource_type} blocked")
            else:
                await route.continue_()
        else:
            await route.continue_()

    await context.route("**/*", block_elements)

    yield  # App is running

    # Shutdown logic
    if context:
        await context.close()
    if browser:
        await browser.close()


def html2markdown(html: str): # uses https://github.com/JohannesKaufmann/html-to-markdown
    process = subprocess.Popen(
        ['html2markdown'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Pass the HTML content to html2markdown
    stdout, stderr = process.communicate(input=html)
    
    # Check for errors
    if process.returncode != 0:
        print(f"Error: {stderr}")
    else:
        # Output the Markdown content
        return stdout
    

app = FastAPI(lifespan=lifespan)

# Firecrawl compatible scrape API
@app.post("/v1/scrape")
async def scrape_single_firecrawl(request_model: FirecrawlScape):
    request_model_scrape= UrlModel(
            url=request_model.url,
            wait_after_load=request_model.waitFor,
            timeout=request_model.timeout,
            headers=request_model.headers if request_model.headers else {}  # Use {} if None
        )
    
    scrapped_result =  await scrape_page(request_model_scrape)
    rawHtml = scrapped_result['content']
    result = {}
    result['success'] = True
    result['data'] = {}
    result['metadata'] = {}
    result['metadata']['url'] = request_model.url
    result['metadata']['statusCode'] = scrapped_result['pageStatusCode']
    
    if 'markdown' in request_model.formats:
        #markdown = html2text.html2text(content)
        #with open("html2text.txt", "w") as text_file:
        #    text_file.write(markdown)
        #result["markdown"] = content_html2text
        markdown = markdownify.markdownify(rawHtml)
        #with open("markdownify.txt", "w") as text_file:
        #    text_file.write(markdown)
        #markdown = html2markdown(content)
        #with open("html2markdown.txt", "w") as text_file:
         #   text_file.write(markdown)
        result['data']['markdown'] = markdown

    if 'rawHtml' in request_model.formats:
        result['data']['rawHtml'] = rawHtml

    if 'html' in request_model.formats:
        html = sanitizer.sanitize(rawHtml)
        result['data']['html'] = html

        # with open("html.txt", "w") as text_file:
        #     text_file.write(html)
        # with open("rawHtml.txt", "w") as text_file:
        #     text_file.write(rawHtml)
        # with open("html-markdownify.txt", "w") as text_file:
        #     text_file.write(markdownify.markdownify(html))
    return result


@app.post("/scrape")
async def scrape_single_page_endpoint(request_model: UrlModel):

    return await scrape_page(request_model)

async def scrape_page(request_model):
    url = request_model.url
    if not url or not is_valid_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")

    print(f"\n{'='*20} Scrape Request {'='*20}")
    print(f"URL: {url}")
    print(f"Wait After Load: {request_model.wait_after_load}ms")
    print(f"Timeout: {request_model.timeout}ms")
    print(f"Headers: {request_model.headers or 'None'}")
    print('='*50)


    page = await context.new_page()
    ####await stealth_async(page)
    try:
        if request_model.headers:
            await page.set_extra_http_headers(request_model.headers)

        # Strategy 1: Load event
        try:
            print("Attempting strategy 1: Normal load")
            response = await page.goto(
                url, 
                wait_until="load",
                timeout=request_model.timeout
            )
        except Exception as e:
            print(f"Strategy 1 failed: {str(e)}")
            # Strategy 2: Network idle
            print("Attempting strategy 2: Network idle")
            response = await page.goto(
                url,
                wait_until="networkidle",
                timeout=request_model.timeout
            )

        if request_model.wait_after_load > 0:
            await asyncio.sleep(request_model.wait_after_load / 1000)

        content = await page.content()
        status_code = response.status if response else None
        page_error = get_error(status_code) if status_code != 200 else None


        if not page_error:
            print("✅ Scrape successful!")
        else:
            print(f"🚨 Scrape failed with status code: ${page_error}")
                        
        return {
            "content": content,
            "pageStatusCode": status_code,
            **({"pageError": page_error} if page_error else {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await page.close()


@app.post("/scrape_multiple")
async def scrape_multiple_page_endpoint(request_model: MultipleUrlModel):
    urls = request_model.urls

    for url in urls:
        if not is_valid_url(url):
            raise HTTPException(status_code=400, detail="Invalid URL")

    url_models = [
        UrlModel(
            url=url,
            wait_after_load=request_model.wait_after_load,
            timeout=request_model.timeout,
            headers=request_model.headers if request_model.headers else {}  # Use {} if None
        ) for url in urls
    ]

    results = await asyncio.gather(
        *(scrape_page(page, url_models) for url_models in url_models)
    )
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv('PORT', 3003)))