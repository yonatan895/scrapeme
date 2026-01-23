# Docker Guide

This project uses multi-stage Docker builds to support development, testing, and production workflows efficiently.

## Build Targets

The unique Dockerfile supports multiple targets:

- **`runtime-base`**: Minimal python-slim base.
- **`deps-builder`**: Builds python wheels for dependencies (caches compilation).
- **`production`**: Slim final image with pre-built wheels and source code. Non-root user.
- **`dev`**: Full development environment with dev dependencies and tools (uv, git).
- **`test`**: Extends dev for running tests.

## Common Commands

The `Makefile` simplifies Docker operations:

### Building
```bash
make docker-build       # Build production image (scrapeme:latest)
make docker-build-dev   # Build dev image (scrapeme:dev)
make docker-test        # Build and run test image
```

### Development
```bash
make docker-shell       # Open bash shell in dev container
make compose-up         # Start full stack (App + Selenium + Prometheus + Grafana)
make compose-logs       # Tail logs
make compose-down       # Stop and remove containers
```

### Maintenance
```bash
make docker-clean       # Remove project images and dangling layers
make docker-scan        # Scan image for vulnerabilities (requires docker scan plugin)
```

## Production Image
The production image is optimized for size and security:
- **Base**: `python:3.12-slim`
- **User**: Runs as non-root `appuser` (UID 10001)
- **Deps**: Installed from wheels to avoid build tools in runtime
- **Entrypoint**: Uses `docker-entrypoint.sh` for proper signal handling (SIGTERM)

## Docker Compose
The `docker-compose.production.yaml` defines the full stack:
- **scrapeme**: Main application
- **selenium-hub**: Selenium Grid Hub
- **chrome/firefox**: Browser nodes
- **prometheus**: Metrics collection
- **grafana**: Visualization (optional)
- **kafka/zookeeper**: Message queue (if enabled)
- **redis**: Caching (if enabled)
- **postgres**: Database (if enabled)
