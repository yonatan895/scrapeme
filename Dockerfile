# syntax=docker/dockerfile:1.4

#############################################
# Stage 1: Base with system dependencies
#############################################
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libxi6 \
    libglib2.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

#############################################
# Stage 2: Python dependencies builder
#############################################
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements for layer caching
COPY requirements.txt .

# Install Python dependencies to /install
RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt

#############################################
# Stage 3: Development environment
#############################################
FROM base AS development

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Install dev dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Install in editable mode
RUN pip install -e .

# Create non-root user for development
RUN useradd -m -u 1000 developer && \
    chown -R developer:developer /app

USER developer

CMD ["pytest", "-v", "--cov"]

#############################################
# Stage 4: Test runner
#############################################
FROM development AS test

USER root

# Run all tests with coverage
RUN pytest tests/ \
    --cov=core \
    --cov=config \
    --cov=infra \
    --cov-report=xml \
    --cov-report=html \
    --cov-report=term-missing \
    --junitxml=test-results/junit.xml \
    -v || true

# Run security checks
RUN pip install safety bandit && \
    safety check --json --output safety-report.json || true && \
    bandit -r core/ config/ infra/ runner.py -f json -o bandit-report.json || true

#############################################
# Stage 5: Production image (minimal)
#############################################
FROM base AS production

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy only application code (no tests, docs, etc.)
COPY config/ ./config/
COPY core/ ./core/
COPY infra/ ./infra/
COPY runner.py .

# Create non-root user FIRST
RUN useradd -m -u 1000 -s /bin/bash scraper

# Create directories and set ownership
RUN mkdir -p /app/artifacts /app/results && \
    chown -R scraper:scraper /app

# Copy and make entrypoint executable
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh && \
    chown scraper:scraper /app/docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9090/metrics').read()" || exit 1

# Default configuration
ENV METRICS_PORT=9090 \
    LOG_LEVEL=INFO

EXPOSE 9090

# Switch to non-root user
USER scraper

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["--config", "sites.yaml", "--browser", "chrome", "--headless", "--metrics-port", "9090", "--out", "/app/results/results.json"]

#############################################
# Stage 6: Security scanning
#############################################
FROM production AS security-scan

USER root

# Install security scanners
RUN pip install --no-cache-dir safety bandit[toml]

# Copy source for scanning
COPY --from=builder /app /app

# Run security scans
RUN safety check --json --output /app/results/safety-report.json || true
RUN bandit -r /app/core /app/config /app/infra /app/runner.py \
    -f json -o /app/results/bandit-report.json || true

#############################################
# Stage 7: Documentation builder
#############################################
FROM base AS docs

COPY --from=builder /install /usr/local

# Install documentation tools
RUN pip install --no-cache-dir sphinx sphinx-rtd-theme sphinx-autodoc-typehints

COPY . .

# Build documentation
RUN cd docs && make html || true

#############################################
# Stage 8: Benchmark runner
#############################################
FROM development AS benchmark

USER root

# Install benchmark tools
RUN pip install --no-cache-dir pytest-benchmark locust

COPY tests/load/ ./tests/load/ || true

CMD ["pytest", "tests/benchmarks/", "--benchmark-only", "--benchmark-json=benchmark.json"]

