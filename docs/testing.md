# Testing & QA

## Pytest
Markers:
- unit, integration, e2e, property, load, chaos

Commands:
```bash
make test          # coverage across core, config, infra
make test-unit
make test-integration
make test-e2e
```

## Security & Quality
```bash
make security-check  # bandit + safety
make deps-outdated
```

## Load testing (Locust)

The Makefile provides concrete load-testing targets with fixed users, spawn rates, and durations.
You may override LOAD_BASE_URL; other knobs (e.g., USERS, SPAWN, DURATION) are not read by these targets.

Quick alias:
- `make load-run`
  - Alias for `make load-test-health` (fixed parameters).

Core targets:
- `make load-test-health`
  - HealthUser, 10 users, spawn 2/s, 60s; host = LOAD_BASE_URL (default http://localhost:9090).
- `make load-test-stress`
  - StressUser, 50 users, spawn 10/s, 120s; host = LOAD_BASE_URL.
- `make load-test-mixed`
  - MixedUser, 30 users, spawn 5/s, 180s; host = LOAD_BASE_URL.
- `make load-test-fast`
  - FastHealthUser, 100 users, spawn 20/s, 60s; host = LOAD_BASE_URL.
- `make load-test-external`
  - ExternalUser, 20 users, spawn 3/s, 300s; host http://quotes.toscrape.com (ENABLE_EXTERNAL_TARGETS=true).
- `make load-test-ci`
  - HealthUser, 5 users, spawn 2/s, 30s; host = LOAD_BASE_URL.
- `make load-test-production`
  - 200 users, spawn 50/s, 600s; host = LOAD_BASE_URL.

Results:
- Reports are written to `artifacts/load_tests` (HTML, CSV). Summarize with:
  - `make load-test-results`.

### Real application load testing

These targets start the application if needed (via `make load-test-app-start`), then run Locust against the running app.
Defaults are defined in the Makefile:
- `APP_BASE_URL=http://localhost:8000`
- `METRICS_URL=http://localhost:9090`
- `APP_CONFIG=config/test_sites.yaml` (a minimal `sites: []` is created if missing)

Targets:
- `make load-test-real-app`
  - RealMixedUser, 20 users, spawn 3/s, 300s; host = APP_BASE_URL.
- `make load-test-real-scraping`
  - RealScrapingUser, 10 users, spawn 2/s, 180s; host = APP_BASE_URL.
- `make load-test-real-monitoring`
  - RealMonitoringUser, 15 users, spawn 5/s, 120s; host = APP_BASE_URL.
- `make load-test-real-browser`
  - BrowserStressUser, 5 users, spawn 1/s, 180s; host = APP_BASE_URL.

Utilities:
- Start/stop the app used by real-app tests:
  - `make load-test-app-start` / `make load-test-app-stop`.
- Clean artifacts and stop app:
  - `make load-test-clean`.
