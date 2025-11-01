# Development Guide

## Repo layout
- core/    — browser/session management, scraping, waits, metrics
- config/  — typed config models and loader
- infra/   — logging, signal handling, health server
- tests/   — unit/integration/e2e structure (markers supported)

## Environment
```bash
make install-dev   # dev & lint extras
make format        # black + isort
make lint          # black+isort+mypy+pylint
make test          # pytest (markers supported)
```

## Code quality
- black, isort, mypy (strict), pylint
- pre-commit supported: make pre-commit-install
- type-safe JSON via TypedDicts in infra/server.py

## Tips
- Prefer explicit waits (core/waits) over sleep
- Use core/metrics for every external call
- Leverage CircuitBreakerRegistry for flaky targets
