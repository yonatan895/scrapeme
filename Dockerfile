# syntax=docker/dockerfile:1.7-labs
ARG PYTHON_VERSION=3.12

############################
# Base runtime image
############################
FROM python:${PYTHON_VERSION}-slim AS runtime-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONHASHSEED=0
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

############################
# Dependency builder (wheels)
############################
FROM runtime-base AS deps-builder
# Copy lock/descriptor files only to maximize cache hits
COPY requirements.txt requirements.txt
COPY requirements-all.txt requirements-all.txt
COPY pyproject.toml pyproject.toml
# Prebuild wheels using pip (uv has no 'wheel' subcommand)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-cache-dir -r requirements.txt -w /wheels

############################
# Production image (slim)
############################
FROM runtime-base AS production
# Non-root user
RUN useradd -m -u 10001 appuser
WORKDIR /app
# Install from prebuilt wheels (no network / no compile)
COPY --from=deps-builder /wheels /wheels
COPY requirements.txt requirements.txt
RUN pip install --no-index --find-links /wheels -r requirements.txt
# Copy runtime sources only
COPY core core
COPY config config
COPY infra infra
COPY runner.py runner.py
USER appuser
ENTRYPOINT ["python", "runner.py"]

############################
# Development image
############################
FROM deps-builder AS dev
WORKDIR /app
COPY . .
# Optional: use uv for faster editable installs (no wheel usage)
RUN pip install uv && \
    UV_LINK_MODE=copy uv pip install -e ".[dev,lint,security,load,docs]"

############################
# Test image
############################
FROM dev AS test
CMD ["pytest", "-q"]
