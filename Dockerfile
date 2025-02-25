FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

LABEL maintainer="loorisr"
LABEL repository="https://github.com/loorisr/playwright-scrape-api"
LABEL description="Simple scraping API based on patchright "
LABEL date="2025-02-24"

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

ENV PYTHONUNBUFFERED=1

ADD pyproject.toml pyproject.toml
ADD uv.lock uv.lock

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

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

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD app /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ARG PORT
ENV PORT=${PORT:-3000}

EXPOSE ${PORT}

# Command to run the application
CMD uvicorn app:app --host 0.0.0.0 --port $PORT