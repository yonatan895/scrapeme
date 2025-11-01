# ScrapeMe - Selenium Automation Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Web scraping and automation framework built with Selenium.

## Important notes
- This implementation is far from complete, many parts are still missing, and some things may be redundant. I don't take any responsibility for any unintended behavior that might arise as a result of running this code, as well as legal issues from scraping sites without explicit permission and authorization. Use at your own discretion.
  
- The `docs/` should provide a basic understanding of the project. However, things can be out-dated as I don't update it much. For accurate information, always consult the actual source code.
- Suggestions and contributions related to core functionality are welcome, and I might take a look at them from time to time. However, refrain from styling-related suggestions, as I don't intend to be working on those any time soon.

- If there is a security concern, please let me know. But please don't submit AI slope reports. You won't claim a bounty for finding a vulnerability here.
  
- This has been mainly tested on Linux (`Ubuntu`), so it is recommended to run the project in a Linux/WSL based environment. It is discourged to use native Windows/MacOs, as there are minimal guarantees for it to be working.


## Quick start
```bash
make quickstart
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python runner.py --config config/sites.yaml --headless --out results.json
```

## Common make targets
```bash
- make venv / make venv-clear
- make install-all / make verify-install
- make format / make lint / make check / make test
- make deps-tree / make deps-outdated
- make load-run   # headless Locust; see docs/testing.md
- docker: make docker-build / docker-run / docker-shell
- compose: make compose-up / compose-down / compose-logs / compose-restart
```


Adjust environment via `.env` (see `.env.example`) and tune resource limits as needed.

## Observability
- Metrics on port `9090` (Prometheus format)
- Health endpoints via `infra/server.py`:
  - `/healthz` (liveness)
  - `/ready` (readiness)

## Project layout
- `core/`    — scraping, browser/session mgmt, waits, metrics
- `config/`  — typed config loader and models
- `infra/`   — logging, signals, health server
- `tests/`   — test suites
- `docs/`    — documentation
