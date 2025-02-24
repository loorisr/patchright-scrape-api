FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

LABEL maintainer="loorisr"
LABEL repository="https://github.com/loorisr/playwright-scrape-api"
LABEL description="Simple scraping API based on patchright "
LABEL date="2025-02-24"

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Install patchright
RUN patchright install chrome

# Install Playwright dependencies. Uses less space than playwright install --with-deps chromium
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# copy the application
COPY app .

ARG PORT
ENV PORT=${PORT:-3000}

EXPOSE ${PORT}

# Command to run the application
CMD uvicorn app:app --host 0.0.0.0 --port $PORT