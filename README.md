# ScrapeMe - Production-Grade Selenium Automation Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A robust, production-ready web scraping and automation framework built with Selenium, featuring comprehensive observability, fault tolerance, and enterprise-grade infrastructure support.

## 🚀 Quick Start

```bash
make quickstart
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python runner.py --config config/sites.yaml --headless --out results.json
```

## 🧰 Makefile changes (colors & load-run)

- Colors are now portable and only enabled when stdout is a TTY using tput. If your terminal does not support colors or output is piped, messages fall back to plain text.
- load-run now passes the base host to Locust automatically. Set a custom target with:

```bash
LOAD_BASE_URL=http://quotes.toscrape.com make load-run
# Or
make load-run USERS=50 SPAWN=5 DURATION=2m LOAD_BASE_URL=http://quotes.toscrape.com
```

If LOAD_BASE_URL is omitted, load-run defaults to http://quotes.toscrape.com.

## Common commands

- make venv / make venv-clear
- make install-all / make verify-install
- make format / make lint / make check / make test
- make load-run (headless Locust)
- make compose-up / compose-down

Colors should render correctly on Ubuntu/WSL2 terminals now, and Locust no longer fails due to a missing --host argument.
