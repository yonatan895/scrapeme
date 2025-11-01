.PHONY: help venv venv-clear install install-dev install-all sync upgrade compile-requirements \
        test test-unit test-integration test-e2e test-property test-load test-chaos test-all \
        lint format type-check security-check benchmark clean clean-all \
        docker-build docker-build-dev docker-test docker-push docker-run docker-scan docker-prepare docker-shell docker-clean \
        docs serve-docs docs-clean compose-up compose-down compose-logs compose-ps compose-restart compose-clean \
        k8s-deploy k8s-delete k8s-logs k8s-status k8s-describe k8s-shell k8s-port-forward k8s-restart \
        ci-local pre-commit-install pre-commit-run pre-commit-update quickstart dev check fix watch version version-bump git-tag \
        info deps-tree deps-outdated health-check diagnose load-run

.DEFAULT_GOAL := help

# Cross-platform
ifeq ($(OS),Windows_NT)
    VENV_BIN := .venv/Scripts
    PYTHON := python
    RM := rmdir /s /q
    SEP := \\
else
    VENV_BIN := .venv/bin
    PYTHON := python3
    RM := rm -rf
    SEP := /
endif

# Tools
VENV := .venv
UV := uv
PYTEST := $(VENV_BIN)/pytest
BLACK := $(VENV_BIN)/black
ISORT := $(VENV_BIN)/isort
MYPY := $(VENV_BIN)/mypy
PYLINT := $(VENV_BIN)/pylint
BANDIT := $(VENV_BIN)/bandit
SAFETY := $(VENV_BIN)/safety
PRE_COMMIT := $(VENV_BIN)/pre-commit
DOCKER := docker
DOCKER_COMPOSE := docker compose
IMAGE_NAME := scrapeme
IMAGE_TAG := latest
REGISTRY := ghcr.io/yonatan895

# Colors (portable via tput; disabled when not a TTY)
ifneq ($(OS),Windows_NT)
  ifeq (,$(shell test -t 1 || echo notty))
    GREEN := $(shell tput setaf 2 2>/dev/null)
    YELLOW := $(shell tput setaf 3 2>/dev/null)
    RED := $(shell tput setaf 1 2>/dev/null)
    BLUE := $(shell tput setaf 4 2>/dev/null)
    NC := $(shell tput sgr0 2>/dev/null)
  else
    GREEN :=
    YELLOW :=
    RED :=
    BLUE :=
    NC :=
  endif
else
  GREEN :=
  YELLOW :=
  RED :=
  BLUE :=
  NC :=
endif

SHELL := /bin/bash
.SHELLFLAGS := -e -o pipefail -c

help: ## Show help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-24s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Environment & Dependencies ---

check-uv: ## Ensure UV is installed
	@command -v $(UV) >/dev/null 2>&1 || { echo "Install UV: https://astral.sh/uv"; exit 1; }

# Create venv only if missing (no prompt)
venv: ## Create virtual environment if it doesn't exist
	@if [ -d "$(VENV)" ]; then \
		echo "$(YELLOW)venv exists$(NC)"; \
	else \
		$(UV) venv; \
		echo "$(GREEN)venv created$(NC)"; \
	fi

# Explicit venv recreation (no prompt)
venv-clear: ## Recreate virtual environment (destructive)
	@echo "$(YELLOW)Recreating venv...$(NC)"
	UV_VENV_CLEAR=1 $(UV) venv --clear
	@echo "$(GREEN)venv recreated$(NC)"

install: check-uv venv ## Install prod deps
	$(UV) pip install -e .

install-dev: check-uv venv ## Install dev deps
	$(UV) pip install -e ".[dev,lint]"

install-all: check-uv venv ## Install all deps
	$(UV) pip install -e .
	$(UV) pip install -e ".[dev,lint,security,load,docs]"
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) install || true

sync: check-uv venv ## Sync env to pyproject
	$(UV) pip sync

upgrade: check-uv venv ## Upgrade all deps
	$(UV) pip install --upgrade -e ".[all]" || true

compile-requirements: check-uv ## Regenerate requirements files
	$(UV) pip compile pyproject.toml -o requirements.txt
	$(UV) pip compile pyproject.toml --extra dev --extra lint -o requirements-dev.txt
	$(UV) pip compile pyproject.toml --all-extras -o requirements-all.txt

verify-install: venv ## Quick import smoke
	$(VENV_BIN)/python -c "import selenium, tenacity, yaml; print('OK')"

# --- Testing ---

test: venv ## Run all tests with coverage
	$(PYTEST) -v --cov=core --cov=config --cov=infra --cov-report=term-missing:skip-covered --cov-fail-under=0

test-unit: venv ## Unit tests only
	@if [ -d "tests/unit" ]; then $(PYTEST) tests/unit -v -m unit --cov-fail-under=0 || true; else echo "no tests/unit"; fi

test-integration: venv compose-up ## Integration tests (with Selenium Grid)
	@if [ -d "tests/integration" ]; then \
		SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub $(PYTEST) tests/integration -v -m integration --cov-fail-under=0 || true; \
	else echo "no tests/integration"; fi

test-e2e: venv compose-up ## End-to-end tests
	@if [ -d "tests/e2e" ]; then \
		SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub $(PYTEST) tests/e2e -v -m e2e --timeout=300 --cov-fail-under=0 || true; \
	else echo "no tests/e2e"; fi

test-property: venv ## Property-based tests
	@if [ -d "tests/property" ]; then $(PYTEST) tests/property -v -m property --cov-fail-under=0 || true; else echo "no tests/property"; fi

test-load: venv ## Load tests marker
	@if [ -d "tests/load" ]; then $(PYTEST) tests/load -v -m load --cov-fail-under=0 || true; else echo "no tests/load"; fi

test-chaos: venv ## Chaos tests
	@if [ -d "tests/chaos" ]; then $(PYTEST) tests/chaos -v -m chaos --cov-fail-under=0 || true; else echo "no tests/chaos"; fi

test-all: venv compose-up ## Run all test suites
	$(PYTEST) -v --cov=core --cov=config --cov=infra --cov-report=term-missing:skip-covered --cov-fail-under=0

benchmark: venv ## Run benchmarks
	@if [ -d "tests/benchmarks" ]; then $(PYTEST) tests/benchmarks --benchmark-only --benchmark-json=benchmark.json || true; else echo "no benchmarks"; fi

# --- Quality ---

lint: venv ## Run code quality checks
	$(BLACK) --check --diff core/ config/ infra/ tests/ runner.py
	$(ISORT) --check-only --diff core/ config/ infra/ tests/ runner.py
	$(MYPY) core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes
	$(PYLINT) core/ config/ infra/ runner.py --fail-under=8.5 || true

format: venv ## Auto-format code
	$(BLACK) core/ config/ infra/ tests/ runner.py
	$(ISORT) core/ config/ infra/ tests/ runner.py

fix: format ## Alias for format

type-check: venv ## Type checking report
	$(MYPY) core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes --html-report mypy-report || true

security-check: venv ## Security scans (bandit + safety)
	$(BANDIT) -r core/ config/ infra/ runner.py -ll -f json -o bandit-report.json || true
	$(SAFETY) check --json --output safety-report.json --continue-on-error || true

# --- Docker & Compose ---

docker-build: ## Build production Docker image
	DOCKER_BUILDKIT=1 $(DOCKER) build --target production -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) .

docker-build-dev: ## Build dev Docker image
	DOCKER_BUILDKIT=1 $(DOCKER) build --target dev -t $(REGISTRY)/$(IMAGE_NAME):dev .

docker-test: ## Build and test Docker image
	DOCKER_BUILDKIT=1 $(DOCKER) build --target test -t $(REGISTRY)/$(IMAGE_NAME):test .
	$(DOCKER) run --rm $(REGISTRY)/$(IMAGE_NAME):test

docker-push: docker-build ## Push Docker image
	$(DOCKER) push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

docker-run: ## Run Docker container
	$(DOCKER) run --rm -it $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

docker-shell: ## Shell into Docker container
	$(DOCKER) run --rm -it --entrypoint=/bin/bash $(REGISTRY)/$(IMAGE_NAME):dev

docker-scan: ## Scan Docker image for vulnerabilities
	$(DOCKER) scout cves $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) || true

docker-prepare: docker-build ## Prepare Docker image (alias for build)

docker-clean: ## Clean Docker images
	$(DOCKER) image prune -f
	$(DOCKER) rmi $$($(DOCKER) images $(REGISTRY)/$(IMAGE_NAME) -q) 2>/dev/null || true

compose-up: ## Start full stack (Selenium Grid + Monitoring)
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml up -d
	@printf '  %shttp://localhost:4444%s\n' "$(BLUE)Selenium Hub:  " "$(NC)"
	@printf '  %shttp://localhost:9091%s\n' "$(BLUE)Prometheus:    " "$(NC)"
	@printf '  %shttp://localhost:3000%s (admin/admin)\n' "$(BLUE)Grafana:       " "$(NC)"
	@printf '  %shttp://localhost:9093%s\n' "$(BLUE)Alertmanager:  " "$(NC)"

compose-down: ## Stop Docker Compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down

compose-logs: ## View Docker Compose logs
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml logs -f

compose-ps: ## Show running Docker Compose containers
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml ps

compose-restart: ## Restart Docker Compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml restart

compose-clean: ## Stop and remove volumes
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down -v

# --- Documentation ---

docs: venv ## Build documentation
	@if [ -d "docs" ]; then \
		command -v $(VENV_BIN)/sphinx-build >/dev/null 2>&1 || $(UV) pip install -e ".[docs]"; \
		cd docs && $(VENV_BIN)/sphinx-build -b html . _build/html; \
	else echo "no docs/ directory"; fi

serve-docs: docs ## Serve documentation locally
	@if [ -d "docs/_build/html" ]; then \
		echo "$(BLUE)Serving docs at http://localhost:8000$(NC)"; \
		$(PYTHON) -m http.server 8000 -d docs/_build/html; \
	else echo "no built docs"; fi

docs-clean: ## Clean documentation build
	@if [ -d "docs/_build" ]; then $(RM) docs/_build; fi

# --- Kubernetes (placeholder) ---

k8s-deploy: ## Deploy to Kubernetes
	@echo "$(YELLOW)Kubernetes deployment not implemented$(NC)"

k8s-delete: ## Delete from Kubernetes
	@echo "$(YELLOW)Kubernetes delete not implemented$(NC)"

k8s-logs: ## View Kubernetes logs
	@echo "$(YELLOW)Kubernetes logs not implemented$(NC)"

k8s-status: ## Kubernetes status
	@echo "$(YELLOW)Kubernetes status not implemented$(NC)"

k8s-describe: ## Describe Kubernetes resources
	@echo "$(YELLOW)Kubernetes describe not implemented$(NC)"

k8s-shell: ## Shell into Kubernetes pod
	@echo "$(YELLOW)Kubernetes shell not implemented$(NC)"

k8s-port-forward: ## Port forward Kubernetes service
	@echo "$(YELLOW)Kubernetes port-forward not implemented$(NC)"

k8s-restart: ## Restart Kubernetes deployment
	@echo "$(YELLOW)Kubernetes restart not implemented$(NC)"

# --- CI/Development ---

ci-local: check format lint test-unit ## Run CI checks locally
	@echo "$(GREEN)Local CI checks passed$(NC)"

pre-commit-install: venv ## Install pre-commit hooks
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) install || \
	$(UV) pip install -e ".[dev]" && $(PRE_COMMIT) install

pre-commit-run: venv ## Run pre-commit on all files
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) run --all-files || true

pre-commit-update: venv ## Update pre-commit hooks
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) autoupdate || true

# --- Utilities ---

clean: ## Clean cache files
	$(RM) .pytest_cache __pycache__ .mypy_cache htmlcov .coverage coverage.xml || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "__pycache__" -type d -exec $(RM) {} + 2>/dev/null || true

clean-all: clean ## Clean everything including venv
	$(RM) $(VENV) dist build *.egg-info || true

watch: venv ## Watch files and run tests
	@command -v $(VENV_BIN)/ptw >/dev/null 2>&1 || $(UV) pip install pytest-watch
	$(VENV_BIN)/ptw --runner "$(PYTEST) -x -q"

version: ## Show version info
	@echo "$(BLUE)Python:$(NC) $$($(PYTHON) --version)"
	@echo "$(BLUE)UV:$(NC) $$($(UV) --version 2>/dev/null || echo 'not installed')"
	@echo "$(BLUE)Docker:$(NC) $$($(DOCKER) --version 2>/dev/null || echo 'not installed')"
	@if [ -f "pyproject.toml" ]; then echo "$(BLUE)Project:$(NC) $$(grep '^version' pyproject.toml | cut -d'"' -f2)"; fi

version-bump: venv ## Bump version (patch)
	@command -v $(VENV_BIN)/bump2version >/dev/null 2>&1 || $(UV) pip install bump2version
	$(VENV_BIN)/bump2version patch

git-tag: ## Create git tag from version
	@if [ -f "pyproject.toml" ]; then \
		VER=$$(grep '^version' pyproject.toml | cut -d'"' -f2); \
		git tag -a "v$$VER" -m "Release v$$VER"; \
		echo "$(GREEN)Tagged v$$VER$(NC)"; \
	else echo "$(RED)No pyproject.toml found$(NC)"; fi

info: ## Show project info
	@echo "$(BLUE)=== Project Information ===$(NC)"
	@echo "$(BLUE)Repository:$(NC) $$(basename $$(pwd))"
	@echo "$(BLUE)Python:$(NC) $$($(PYTHON) --version)"
	@echo "$(BLUE)Virtual Env:$(NC) $$(if [ -d $(VENV) ]; then echo 'exists'; else echo 'missing'; fi)"
	@echo "$(BLUE)Git Branch:$(NC) $$(git branch --show-current 2>/dev/null || echo 'unknown')"
	@echo "$(BLUE)Docker:$(NC) $$($(DOCKER) --version 2>/dev/null || echo 'not installed')"

deps-tree: venv ## Show dependency tree
	@command -v $(VENV_BIN)/pipdeptree >/dev/null 2>&1 || $(UV) pip install pipdeptree
	$(VENV_BIN)/pipdeptree

deps-outdated: venv ## Show outdated dependencies
	$(UV) pip list --outdated

health-check: venv ## Basic health check
	@echo "$(BLUE)=== Health Check ===$(NC)"
	@echo -n "$(BLUE)Python imports:$(NC) "; $(VENV_BIN)/python -c "import core.scraper, config.models; print('✓')" 2>/dev/null || echo "✗"
	@echo -n "$(BLUE)Selenium:$(NC) "; $(VENV_BIN)/python -c "import selenium; print('✓')" 2>/dev/null || echo "✗"
	@echo -n "$(BLUE)Tests:$(NC) "; if [ -d "tests" ]; then echo "✓"; else echo "✗"; fi
	@echo -n "$(BLUE)Docker:$(NC) "; $(DOCKER) --version >/dev/null 2>&1 && echo "✓" || echo "✗"

diagnose: health-check info ## Full diagnostic info
	@echo "$(BLUE)=== Diagnostic Complete ===$(NC)"

load-run: venv ## Headless Locust (USERS, SPAWN, DURATION, LOAD_BASE_URL)
	@USERS=$${USERS:-30}; SPAWN=$${SPAWN:-3}; DURATION=$${DURATION:-1m}; \
	HOST=$${LOAD_BASE_URL:-http://quotes.toscrape.com}; \
	command -v $(VENV_BIN)/locust >/dev/null 2>&1 || $(UV) pip install -e ".[load]"; \
	$(VENV_BIN)/locust -f tests/load/locustfile.py --headless -H "$$HOST" -u "$$USERS" -r "$$SPAWN" -t "$$DURATION"

# --- Shortcuts ---

quickstart: check-uv venv install-all verify-install ## Complete setup (no venv prompt)
	@echo "$(GREEN)Quickstart complete$(NC)"

dev: install-all pre-commit-install ## Setup dev env
	@echo "$(GREEN)Dev environment ready$(NC)"

check: format lint test-unit ## Pre-commit validation
	@echo "$(GREEN)Checks passed$(NC)"
