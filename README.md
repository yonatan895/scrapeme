# ScrapeMe - Selenium Automation Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Production-ready web scraping and automation framework built with Selenium, featuring comprehensive observability, fault tolerance, and cloud-native deployment capabilities.

## Features

**Core Automation**
- Selenium-based web scraping with Chrome and Firefox support
- Smart waiting strategies with configurable timeouts
- Frame navigation and multi-step workflows
- Authentication handling with credential management

**Production Ready**
- Circuit breakers and rate limiting for fault tolerance
- Prometheus metrics and structured logging
- Health checks for Kubernetes deployment
- Artifact capture (screenshots, HTML) for debugging

**Developer Experience**
- Comprehensive test suite (unit, integration, load, chaos)
- Docker support with multi-stage builds
- Load testing with Locust integration
- Extensive Make-based workflow automation

## Quick Start

```bash
# Setup environment
make quickstart
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Run with example configuration
python runner.py --config config/sites.yaml --headless --out results.json
```

## Configuration

Define scraping workflows in YAML:

```yaml
sites:
  - name: example_site
    base_url: "https://example.com"
    page_load_timeout_sec: 30
    wait_timeout_sec: 10
    steps:
      - name: extract_data
        goto_url: "/page"
        fields:
          - name: title
            xpath: "//h1"
          - name: content
            xpath: "//div[@class='content']"
            attribute: "textContent"
```

## Usage Examples

```bash
# Basic scraping
python runner.py --config sites.yaml --headless

# With custom output and artifacts
python runner.py --config sites.yaml --out data.json --artifact-dir ./captures

# Parallel execution
python runner.py --config sites.yaml --max-workers 8

# Streaming JSONL output
python runner.py --config sites.yaml --jsonl --out results.jsonl

# Daemon mode for Kubernetes
python runner.py --config sites.yaml --daemon --metrics-port 9090
```

## Development

```bash
# Development environment setup
make dev

# Code quality checks
make format lint type-check test

# Run specific test suites
make test-unit test-integration test-load

# Load testing
make load-run

# Docker development
make docker-build-dev docker-shell
```

## Deployment

**Docker**
```bash
# Production build
make docker-build

# Run container
docker run -v $(pwd)/config:/app/config:ro scrapeme \
  --config /app/config/sites.yaml --headless --daemon
```

**Docker Compose**
```bash
make compose-up    # Start services
make compose-logs  # View logs
make compose-down  # Stop services
```

## Observability

- **Metrics**: Prometheus format on port 9090 (`/metrics`)
- **Health checks**: Liveness (`/healthz`) and readiness (`/ready`)
- **Structured logging**: JSON format with correlation IDs
- **Artifact capture**: Screenshots and HTML snapshots on failures

## Project Structure

```
core/           # Core scraping engine and browser management
config/         # Configuration models and loaders
infra/          # Infrastructure components (logging, health, signals)
tests/          # Comprehensive test suites
docs/           # Documentation
monitoring/     # Observability configurations
infra/          # Kubernetes manifests and deployment configs
```

## Important Notes

- This implementation is actively developed but may have incomplete features
- Users are responsible for complying with website terms of service and legal requirements
- Primarily tested on Linux (Ubuntu); Windows/macOS support not guaranteed
- For production use, thorough testing in your environment is recommended
- Security concerns should be reported responsibly

## Contributing

Contributions focusing on core functionality are welcome. Please:
- Follow the existing code style and patterns
- Add tests for new functionality
- Ensure `make check` passes before submitting
- Provide clear descriptions in pull requests

## License

MIT License - see [LICENSE](LICENSE) file for details.
