# ScrapeMe - Production-Grade Selenium Automation Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A robust, production-ready web scraping and automation framework built with Selenium, featuring comprehensive observability, fault tolerance, and enterprise-grade infrastructure support.

## ✨ Features

- Multi-site scraping with YAML configuration
- Authentication flows, artifact capture, smart waits, retries, rate limiting, and circuit breakers
- Structured logging, Prometheus metrics, health checks, and build info
- Docker/Kubernetes deploys, Selenium Grid integration, and comprehensive Makefile workflows

## 🚀 Quick Start

```bash
# Recommended (UV)
curl -LsSf https://astral.sh/uv/install.sh | sh   # Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

git clone https://github.com/yonatan895/scrapeme.git
cd scrapeme

make quickstart        # venv + all deps + basic verification
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Run example
python runner.py --config config/sites.yaml --headless --out results.json
```

## 📋 Configuration

Use config/sites.yaml for site definitions (example included). Environment variables for credentials follow the pattern {SITE_NAME_UPPER}_USERNAME/PASSWORD.

## 🧰 Makefile commands (updated)

These are the most common commands after recent changes. Run `make help` for the full list.

- Environment & deps
  - make quickstart: Create venv, install all extras, verify install
  - make venv | make install-all | make verify-install

- Code quality & tests
  - make check: Format, lint, and quick tests
  - make format | make lint | make type-check | make security-check | make test

- Load testing (new)
  - make load-run: Run Locust headless using tests/load/locustfile.py
    - Overrides: USERS=30 SPAWN=3 DURATION=1m LOAD_BASE_URL=http://quotes.toscrape.com
    - Auto-installs the "load" extra via UV if Locust is missing

- Docker
  - make docker-build | make docker-build-dev | make docker-test | make docker-run
  - make docker-prepare: Creates results, artifacts, config folders; notes to use committed config/sites.yaml

- Docker Compose (filename fixed to .yaml)
  - make compose-up: Start full stack (Selenium Hub + monitoring)
  - make compose-logs: Tail logs (uses docker-compose.production.yaml)
  - make compose-ps: Show processes
  - make compose-down: Stop stack (uses .yaml)
  - make compose-clean: Stop and remove volumes (uses .yaml)

- Kubernetes
  - make k8s-deploy | k8s-status | k8s-logs | k8s-port-forward | k8s-delete

- Diagnostics
  - make info | make health-check | make diagnose

## 🧪 Tests

- Unit tests live under tests/unit and include config models, rate limiter, URL utils, and a schema sanity test that loads all YAML under config/ with the project loader.
- Property, chaos, benchmarks folders exist; extend as needed.
- Load testing uses Locust at tests/load/locustfile.py (new real scenario).

Run examples:

```bash
make test             # coverage and reports
make load-run         # headless Locust (override USERS/SPAWN/DURATION)
```

## 📊 Monitoring

Expose Prometheus on port 9090 from the app, Prometheus server on 9091 via docker-compose.production.yaml, Grafana on 3000, Alertmanager on 9093.

## 🔒 Security

- The load extra pins brotli>=1.2.0 to ensure patched versions during load testing installation.

## 🐳 Docker & ☸️ Kubernetes

See docker-compose.production.yaml for services; use compose-* targets listed above. Kubernetes manifests are under k8s/ and controlled via k8s-* targets.

## 📚 API Reference (selected)

- core.scraper.SiteScraper: orchestrates steps and extraction
- core.browser.BrowserManager: manages WebDriver lifecycle and pooling
- core.auth.AuthFlow: performs login flows using configured selectors

## 🔍 Troubleshooting

- Permissions for results/artifacts in Docker: chown to your UID/GID
- Increase wait/page timeouts in sites.yaml for slow endpoints
- Use --remote-url with Selenium Grid

---

Run `make help` at any time to see all available targets with descriptions.
