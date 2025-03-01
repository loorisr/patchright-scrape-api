FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Define an ARG for the build type
ARG BUILD_TYPE=default

LABEL maintainer="loorisr"
LABEL repository="https://github.com/loorisr/patchright-scrape-api"
LABEL description="Simple scraping API based on patchright"
LABEL date="2025-02-27"

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

# Install patchright with Chrome
RUN if [ "$BUILD_TYPE" != "lite" ]; then \
        patchright install chrome; \
    fi

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