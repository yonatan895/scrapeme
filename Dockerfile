# syntax=docker/dockerfile:1.7-labs
ARG PYTHON_VERSION=3.12

############################
# Base runtime image
############################
FROM python:${PYTHON_VERSION}-slim AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONHASHSEED=0 \
    DEBIAN_FRONTEND=noninteractive

# Install base OS deps and libs commonly required by remote Selenium sessions
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg \
      # Useful runtime tools and libs used by headless browser containers
      wget unzip \
      libnss3 libgssapi-krb5-2 libxss1 libasound2 libxshmfence1 \
      libgbm1 libgtk-3-0 libxi6 libxrandr2 libxrender1 \
      fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Ensure consistent working dir
WORKDIR /app

############################
# Dependency builder (wheels)
############################
FROM runtime-base AS deps-builder
# Copy lock/descriptor files only to maximize cache hits
COPY requirements.txt requirements.txt
COPY requirements-all.txt requirements-all.txt
COPY pyproject.toml pyproject.toml
# Prebuild wheels using pip cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-cache-dir -r requirements.txt -w /wheels

############################
# Production image (runtime only; no Chrome inside)
############################
FROM runtime-base AS production

# Create non-root user and group
RUN groupadd -g 10001 appuser && useradd -m -u 10001 -g 10001 appuser

# Create application directories with proper ownership
RUN mkdir -p /app /app/artifacts /app/output /home/appuser/.cache /home/appuser/downloads \
    && chown -R appuser:appuser /app /home/appuser

# Precreate selenium cache dir for remote sessions/plugins and give access
RUN mkdir -p /home/appuser/.cache/selenium \
    && chown -R appuser:appuser /home/appuser/.cache

WORKDIR /app

# Install from prebuilt wheels (no network / no compile)
COPY --from=deps-builder /wheels /wheels
COPY requirements.txt requirements.txt
RUN pip install --no-index --find-links /wheels -r requirements.txt \
    && rm -rf /wheels

# Copy runtime sources only
COPY core core
COPY config config
COPY infra infra
COPY runner.py runner.py

# Drop privileges
USER appuser

# Default output dir env for convenience
ENV SCRAPEME_OUTPUT_DIR=/app/output

# By default, expect running against remote Selenium (Selenium Grid/Chrome in docker-compose)
# Example in README will pass: --remote-url http://selenium:4444/wd/hub
ENTRYPOINT ["python", "runner.py"]

############################
# Development image
############################
FROM deps-builder AS dev
WORKDIR /app
COPY . .
RUN pip install uv && \
    UV_LINK_MODE=copy uv pip install --system -e ".[dev,lint,security,load,docs]"

############################
# Test image
############################
FROM dev AS test
CMD ["pytest", "-q"]
