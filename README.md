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

## 🚀 Quick Start (no prompts)

```bash
# 1) Install UV (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2) Clone
git clone https://github.com/yonatan895/scrapeme.git
cd scrapeme

# 3) One-shot setup (no venv prompts)
make quickstart

# 4) Activate venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 5) Run example
python runner.py --config config/sites.yaml --headless --out results.json
```

If you need to rebuild the venv explicitly:

```bash
make venv-clear   # destructive; recreates .venv cleanly
```

## 🧰 Makefile commands (synced)

- Environment & deps
  - make venv               # create virtual environment if missing (no prompt)
  - make venv-clear         # force recreate venv (no prompt)
  - make install-all        # install all extras (dev, lint, security, load, docs)
  - make verify-install     # import smoke (selenium, tenacity, yaml)
  - make compile-requirements  # regenerate requirements*.txt from pyproject

- Development workflow
  - make format             # Black + isort
  - make lint               # Black check, isort check, mypy, pylint
  - make type-check         # mypy strict report
  - make check              # format + lint + unit tests (pre-commit style)

- Tests
  - make test               # all tests with coverage
  - make test-unit          # unit tests only
  - make test-integration   # integration tests
  - make test-e2e           # end-to-end tests
  - make test-property      # property-based tests
  - make test-load          # load marker (pytest)
  - make test-chaos         # chaos marker (pytest)

- Load testing (real Locust)
  - make load-run           # headless Locust (USERS=30 SPAWN=3 DURATION=1m LOAD_BASE_URL=...)

- Docker & Compose
  - make docker-prepare     # create results/artifacts/config (uses committed config/sites.yaml)
  - make docker-build       # production image
  - make docker-build-dev   # development image
  - make docker-test        # run tests in container
  - make docker-run         # run app container
  - make compose-up         # start stack (docker-compose.production.yaml)
  - make compose-logs       # tail logs
  - make compose-ps         # list services
  - make compose-down       # stop stack
  - make compose-clean      # stop and remove volumes

- Kubernetes
  - make k8s-deploy | k8s-status | k8s-logs | k8s-port-forward | k8s-delete

- Diagnostics
  - make info | make health-check | make diagnose

## 🔒 Security

- The "load" extra locks brotli==1.1.0 across the project for consistent, resolvable installs.

## 📊 Monitoring

- App exports Prometheus on 9090; docker-compose.production.yaml exposes Prometheus server on 9091, Grafana on 3000, Alertmanager on 9093.

## 🐳 Docker & ☸️ Kubernetes

Use the compose-* and k8s-* Make targets shown above. See docker-compose.production.yaml and k8s/ manifests.

## 📚 API Reference (selected)

- core.scraper.SiteScraper – orchestrates steps and extraction
- core.browser.BrowserManager – WebDriver lifecycle and pooling
- core.auth.AuthFlow – login flows using configured selectors

## 🔍 Troubleshooting

- No more venv prompts: venv is created only if missing; use make venv-clear to rebuild explicitly.
- If Locust is missing: make load-run installs [load] extras automatically via UV.
- If results/artifacts perms fail in Docker: chown to your UID/GID.
- Increase wait/page timeouts in sites.yaml for slow endpoints.
- Use --remote-url to target Selenium Grid.
