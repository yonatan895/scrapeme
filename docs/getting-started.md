# Getting Started

## Prerequisites
- Python 3.12+
- uv (https://astral.sh/uv)
- make

## Install
```bash
make quickstart
# Or step-by-step
make venv
make install-all
make verify-install
```

## First run
```bash
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
python runner.py --config config/sites.yaml --headless --out results.json
```

## Common make targets
- make install-all — dev + lint + extras
- make check — format + lint + unit tests
- make test — all tests with coverage
- make deps-tree — dependency tree (installs pipdeptree if missing)
- make load-run — headless Locust (see running.md)
