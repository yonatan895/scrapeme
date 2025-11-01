# Docker

## Images
- production (default target): minimal runtime
- dev: full toolchain for development
- test: runs pytest

## Build & Run
```bash
make docker-build
make docker-run       # run latest image
make docker-shell     # bash inside dev image
```

Dockerfile uses a wheel-building stage for reproducible, network-minimized installs.

## References
- Dockerfile best practices: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- Docker Compose: https://docs.docker.com/compose/
- Selenium Grid (for integration tests when run via compose): https://www.selenium.dev/documentation/grid/
