# ScrapeMe - Production-Grade Selenium Automation Framework

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A robust, production-ready web scraping and automation framework built with Selenium, featuring comprehensive observability, fault tolerance, and developer‑friendly tooling.

- Docs: see docs/README.md


## Quick start
```bash
make quickstart
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python runner.py --config config/sites.yaml --headless --out results.json
```

## Common make targets
- make venv / make venv-clear
- make install-all / make verify-install
- make format / make lint / make check / make test
- make deps-tree / make deps-outdated
- make load-run   # headless Locust; see docs/testing.md
- docker: make docker-build / docker-run / docker-shell
- compose: make compose-up / compose-down / compose-logs / compose-restart


Adjust environment via .env (see .env.example) and tune resource limits as needed.

## Observability
- Metrics on port 9090 (Prometheus format)
- Health endpoints via infra/server.py:
  - /healthz (liveness)
  - /ready (readiness)

## Project layout
- core/    — scraping, browser/session mgmt, waits, metrics
- config/  — typed config loader and models
- infra/   — logging, signals, health server
- tests/   — test suites
- docs/    — documentation
