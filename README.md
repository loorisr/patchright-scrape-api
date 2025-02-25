# Patchright Scrape API

Simple scraping API based on patchright.
It creates a REST API scrape endpoint to return the content of a page.

It runs in docker.

It is inspired from the Typescript version of [Firecrawl](https://github.com/mendableai/firecrawl/tree/main/apps/playwright-service-ts) and it is 100% compatible with it. You just have to replace `build: apps/playwright-service-ts` by `image: loorisr/patchright-scrape-api` in your docker-compose

Features:
* uses https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python instead of playwright
* better domain blocking handling
* better media blocking handling
* scrape multiple pages in parallel
* scrape endpoint compatible with Firecrawl API
* return cleaned html and markdow
* temporary or persistent context
* lightweight: 1.2 Go

Available on Docker hub: `docker pull loorisr/patchright-scrape-api:latest`

## Env vars
* `DOMAIN_BLOCKED_DOMAINS`: list of domains to block. For example ["url1.com", "url2.com"].
* `DOMAIN_BLOCKLIST_URL`: url of a domain blocklist. For example: https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/light.txt
  
  *It is better to use a small list otherwise it will slow down the page loading time. This light list has already 154 000 entries!*
  
  *The best is to block the domain at the **DNS level**.*
  
* `DOMAIN_BLOCKLIST_PATH`: local path to a domain blocklist. For example blocklist.txt
* `RESOURCES_EXCLUDED`: list of type of content to block. [] to disable. Default : ['image', 'stylesheet', 'media', 'font','other']. See https://playwright.dev/python/docs/api/class-request#request-resource-type

* `PROXY_SERVER`: adress of the proxy server
* `PROXY_USERNAME`: username of the proxy server
* `PROXY_PASSWORD`: password of the proxy server

* `PORT`: port to run the app. Default: 3000

* `PERSISTENT_CONTEXT`: To enable persistent context. If true, a volume needs to be mounted at /context. Default: False

## Endpoints
* `/scrape`
  - **url**: url to scrape : http://www.domain.tld
  - or **urls**: a list of urls to scrape: ["http://www.domain1.tld", "http://www.domain2.tld"]
  - **wait_after_load**: time in ms to wait after the page is loaded. Default: 0
  - **timeout**: time in ms before timeout. Default: 15000
  - **headers**: Specific headers to add = Default: None
* `/v1/scrape`
  - **url**: url to scrape : http://www.domain.tld
  - **waitFor**: time in ms to wait after the page is loaded. Default: 0
  - **timeout**: time in ms before timeout. Default: 15000
  - **headers**: Specific headers to add = Default: None
  - **formats**: List of formats to include in the output: markdown, html, rawHtml : Default : ["markdown"]
