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
```bash
LOAD_BASE_URL=http://quotes.toscrape.com make load-run
# or
make load-run USERS=50 SPAWN=5 DURATION=2m LOAD_BASE_URL=http://quotes.toscrape.com
```
