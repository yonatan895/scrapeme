.PHONY: help venv venv-clear install install-dev install-all sync upgrade compile-requirements \
        test test-unit test-integration test-e2e test-property test-load test-chaos test-all \
        lint format type-check security-check benchmark clean clean-all \
        docker-build docker-build-dev docker-test docker-push docker-run docker-scan docker-prepare docker-shell docker-clean \
        docs serve-docs docs-clean compose-up compose-down compose-logs compose-ps compose-restart compose-clean \
        k8s-deploy k8s-delete k8s-logs k8s-status k8s-describe k8s-shell k8s-port-forward k8s-restart \
        ci-local pre-commit-install pre-commit-run pre-commit-update quickstart dev check fix watch version version-bump git-tag \
        info deps-tree deps-outdated health-check diagnose load-run verify-python \
        load-test-health load-test-stress load-test-mixed load-test-fast load-test-external load-test-ci load-test-production \
        load-test-install load-test-clean load-test-results

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
LOCUST := $(VENV_BIN)/locust
DOCKER := docker
DOCKER_COMPOSE := docker compose
IMAGE_NAME := scrapeme
IMAGE_TAG := latest
REGISTRY := ghcr.io/yonatan895

# Load testing configuration
LOAD_BASE_URL ?= http://localhost:9090
LOAD_RESULTS_DIR ?= artifacts/load_tests
LOCUST_FILE := tests/load/locustfile.py

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

venv: ## Create virtual environment if it doesn't exist
	@if [ -d "$(VENV)" ]; then \
		echo "$(YELLOW)venv exists$(NC)"; \
	else \
		$(UV) venv; \
		echo "$(GREEN)venv created$(NC)"; \
	fi

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

verify-install: venv ## Quick import smoke test
	$(VENV_BIN)/python -c "import selenium, tenacity, yaml; print('OK')"

# --- Testing ---

test: venv ## Run all tests with coverage
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	$(PYTEST) -v --cov=core --cov=config --cov=infra --cov-report=term-missing:skip-covered

test-unit: venv ## Unit tests only
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@if [ -d "tests/unit" ]; then $(PYTEST) tests/unit -v -m unit || true; else echo "no tests/unit"; fi

test-integration: venv ## Integration tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@if [ -d "tests/integration" ]; then $(PYTEST) tests/integration -v -m integration || true; else echo "no tests/integration"; fi

test-e2e: venv ## End-to-end tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@if [ -d "tests/e2e" ]; then $(PYTEST) tests/e2e -v -m e2e --timeout=300 || true; else echo "no tests/e2e"; fi

test-property: venv ## Property-based tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@if [ -d "tests/property" ]; then $(PYTEST) tests/property -v -m property || true; else echo "no tests/property"; fi

test-load: venv ## Load tests marker
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@if [ -d "tests/load" ]; then $(PYTEST) tests/load -v -m load || true; else echo "no tests/load"; fi

test-chaos: venv ## Chaos tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@if [ -d "tests/chaos" ]; then $(PYTEST) tests/chaos -v -m chaos || true; else echo "no tests/chaos"; fi

# --- Enhanced Load Testing ---

load-test-install: venv ## Install load testing dependencies
	@if [ ! -x "$(LOCUST)" ]; then \
		echo "$(BLUE)Installing load testing dependencies...$(NC)"; \
		$(UV) pip install -e ".[load]"; \
	fi
	@mkdir -p $(LOAD_RESULTS_DIR)
	@echo "$(GREEN)Load testing setup complete$(NC)"

load-test-health: load-test-install ## Run health check load tests (quick validation)
	@echo "$(BLUE)Running health check load tests...$(NC)"
	LOAD_TEST_MODE=health LOAD_BASE_URL=$(LOAD_BASE_URL) \
	$(LOCUST) -f $(LOCUST_FILE) HealthUser \
		--users 10 --spawn-rate 2 --run-time 60s \
		--host $(LOAD_BASE_URL) --headless \
		--html $(LOAD_RESULTS_DIR)/health_test_report.html \
		--csv $(LOAD_RESULTS_DIR)/health_test
	@echo "$(GREEN)Health load tests completed$(NC)"

load-test-stress: load-test-install ## Run stress tests (performance limits)
	@echo "$(BLUE)Running stress load tests...$(NC)"
	LOAD_TEST_MODE=stress LOAD_BASE_URL=$(LOAD_BASE_URL) \
	$(LOCUST) -f $(LOCUST_FILE) StressUser \
		--users 50 --spawn-rate 10 --run-time 120s \
		--host $(LOAD_BASE_URL) --headless \
		--html $(LOAD_RESULTS_DIR)/stress_test_report.html \
		--csv $(LOAD_RESULTS_DIR)/stress_test
	@echo "$(GREEN)Stress load tests completed$(NC)"

load-test-mixed: load-test-install ## Run mixed scenario tests
	@echo "$(BLUE)Running mixed scenario load tests...$(NC)"
	LOAD_TEST_MODE=mixed LOAD_BASE_URL=$(LOAD_BASE_URL) \
	$(LOCUST) -f $(LOCUST_FILE) MixedUser \
		--users 30 --spawn-rate 5 --run-time 180s \
		--host $(LOAD_BASE_URL) --headless \
		--html $(LOAD_RESULTS_DIR)/mixed_test_report.html \
		--csv $(LOAD_RESULTS_DIR)/mixed_test
	@echo "$(GREEN)Mixed scenario load tests completed$(NC)"

load-test-fast: load-test-install ## Run high-performance tests with FastHttpUser
	@echo "$(BLUE)Running high-performance load tests...$(NC)"
	LOAD_TEST_MODE=health LOAD_BASE_URL=$(LOAD_BASE_URL) \
	$(LOCUST) -f $(LOCUST_FILE) FastHealthUser \
		--users 100 --spawn-rate 20 --run-time 60s \
		--host $(LOAD_BASE_URL) --headless \
		--html $(LOAD_RESULTS_DIR)/fast_test_report.html \
		--csv $(LOAD_RESULTS_DIR)/fast_test
	@echo "$(GREEN)High-performance load tests completed$(NC)"

load-test-external: load-test-install ## Run external target tests (requires internet)
	@echo "$(BLUE)Running external target load tests...$(NC)"
	LOAD_TEST_MODE=mixed LOAD_BASE_URL=http://quotes.toscrape.com ENABLE_EXTERNAL_TARGETS=true \
	$(LOCUST) -f $(LOCUST_FILE) ExternalUser \
		--users 20 --spawn-rate 3 --run-time 300s \
		--host http://quotes.toscrape.com --headless \
		--html $(LOAD_RESULTS_DIR)/external_test_report.html \
		--csv $(LOAD_RESULTS_DIR)/external_test
	@echo "$(GREEN)External target load tests completed$(NC)"

load-test-ci: load-test-install ## Run CI/CD pipeline tests (quick validation)
	@echo "$(BLUE)Running CI/CD load tests...$(NC)"
	LOAD_TEST_MODE=health LOAD_BASE_URL=$(LOAD_BASE_URL) \
	$(LOCUST) -f $(LOCUST_FILE) HealthUser \
		--users 5 --spawn-rate 2 --run-time 30s \
		--host $(LOAD_BASE_URL) --headless \
		--html $(LOAD_RESULTS_DIR)/ci_test_report.html \
		--csv $(LOAD_RESULTS_DIR)/ci_test
	@echo "$(GREEN)CI/CD load tests completed$(NC)"

load-test-production: load-test-install ## Run production-like load tests
	@echo "$(BLUE)Running production-like load tests...$(NC)"
	LOAD_TEST_MODE=mixed LOAD_BASE_URL=$(LOAD_BASE_URL) \
	$(LOCUST) -f $(LOCUST_FILE) \
		--users 200 --spawn-rate 50 --run-time 600s \
		--host $(LOAD_BASE_URL) --headless \
		--html $(LOAD_RESULTS_DIR)/production_test_report.html \
		--csv $(LOAD_RESULTS_DIR)/production_test
	@echo "$(GREEN)Production load tests completed$(NC)"

load-test-results: ## Show load test results summary
	@echo "$(BLUE)=== Load Test Results Summary ===$(NC)"
	@if [ -d "$(LOAD_RESULTS_DIR)" ]; then \
		echo "$(BLUE)Results directory:$(NC) $(LOAD_RESULTS_DIR)"; \
		echo "$(BLUE)HTML Reports:$(NC)"; \
		ls -la $(LOAD_RESULTS_DIR)/*.html 2>/dev/null || echo "  No HTML reports found"; \
		echo "$(BLUE)CSV Data:$(NC)"; \
		ls -la $(LOAD_RESULTS_DIR)/*.csv 2>/dev/null || echo "  No CSV data found"; \
		echo "$(BLUE)JSON Results:$(NC)"; \
		ls -la $(LOAD_RESULTS_DIR)/*.json 2>/dev/null || echo "  No JSON results found"; \
		if [ -f "load_test_results.json" ]; then \
			echo "$(BLUE)Latest Summary:$(NC)"; \
			cat load_test_results.json | python3 -m json.tool; \
		fi; \
	else \
		echo "$(YELLOW)No load test results found. Run 'make load-test-health' first.$(NC)"; \
	fi

load-test-clean: ## Clean load test results
	@echo "$(YELLOW)Cleaning load test results...$(NC)"
	@$(RM) $(LOAD_RESULTS_DIR) 2>/dev/null || true
	@$(RM) load_test_results.json 2>/dev/null || true
	@echo "$(GREEN)Load test results cleaned$(NC)"

load-run: load-test-health ## Alias for quick load testing

# --- Quality ---

lint: venv ## Run code quality checks
	@if [ ! -x "$(BLACK)" ] || [ ! -x "$(ISORT)" ] || [ ! -x "$(MYPY)" ] || [ ! -x "$(PYLINT)" ]; then $(UV) pip install -e ".[dev,lint]"; fi
	$(BLACK) --check --diff core/ config/ infra/ tests/ runner.py
	$(ISORT) --check-only --diff core/ config/ infra/ tests/ runner.py
	$(MYPY) core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes
	$(PYLINT) core/ config/ infra/ runner.py --fail-under=8.5

format: venv ## Auto-format code
	@if [ ! -x "$(BLACK)" ] || [ ! -x "$(ISORT)" ]; then $(UV) pip install -e ".[dev,lint]"; fi
	$(BLACK) core/ config/ infra/ tests/ runner.py
	$(ISORT) core/ config/ infra/ tests/ runner.py

type-check: venv ## Type checking report
	@if [ ! -x "$(MYPY)" ]; then $(UV) pip install -e ".[dev,lint]"; fi
	$(MYPY) core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes

security-check: venv ## Security scans (bandit + safety)
	@if [ ! -x "$(BANDIT)" ]; then $(UV) pip install -e ".[security]"; fi
	$(BANDIT) -r core/ config/ infra/ runner.py -ll -f json -o bandit-report.json || true
	@if [ ! -x "$(SAFETY)" ]; then $(UV) pip install -e ".[security]"; fi
	$(SAFETY) check --json --output safety-report.json --continue-on-error || true

# --- Docker & Compose (extended) ---

docker-build: ## Build production Docker image
	DOCKER_BUILDKIT=1 $(DOCKER) build --target production -t $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) .

docker-build-dev: ## Build dev Docker image
	DOCKER_BUILDKIT=1 $(DOCKER) build --target dev -t $(REGISTRY)/$(IMAGE_NAME):dev .

docker-test: ## Build and run test image
	DOCKER_BUILDKIT=1 $(DOCKER) build --target test -t $(REGISTRY)/$(IMAGE_NAME):test .
	$(DOCKER) run --rm $(REGISTRY)/$(IMAGE_NAME):test

docker-push: ## Push Docker image to registry
	@if ! $(DOCKER) info >/dev/null 2>&1; then echo "Docker not available"; exit 1; fi
	$(DOCKER) push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

docker-run: ## Run container with args (use ARGS="--config /app/config/sites.yaml ...")
	$(DOCKER) run --rm -it \
		-v $(PWD)/config:/app/config:ro \
		-v $(PWD)/artifacts:/app/artifacts \
		$(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) \
		$(ARGS)

docker-shell: ## Shell into dev image
	$(DOCKER) run --rm -it --entrypoint=/bin/bash $(REGISTRY)/$(IMAGE_NAME):dev

docker-scan: ## CVE scan (non-fatal)
	@if command -v docker >/dev/null 2>&1 && docker --help | grep -q "scan"; then \
		docker scan $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) || true; \
	else \
		echo "$(YELLOW)Docker scan not available; skipping$(NC)"; \
	fi

docker-prepare: docker-build ## Alias: prepare == build

docker-clean: ## Prune and remove images safely
	$(DOCKER) image prune -f || true
	@IMGS=$$($(DOCKER) images $(REGISTRY)/$(IMAGE_NAME) -q); \
	if [ -n "$$IMGS" ]; then $(DOCKER) rmi $$IMGS 2>/dev/null || true; fi

compose-up: ## Start production compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml up -d

compose-down: ## Stop compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down

compose-logs: ## Tail compose logs
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml logs -f --tail=200

compose-ps: ## Show compose services
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml ps

compose-restart: ## Restart compose services
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml restart

compose-clean: ## Remove stopped containers and dangling resources
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down --remove-orphans

# --- Documentation ---

docs: venv ## Build Sphinx docs (if present)
	@if [ -d "docs" ] && [ -f "docs/conf.py" ]; then \
		command -v $(VENV_BIN)/sphinx-build >/dev/null 2>&1 || $(UV) pip install -e ".[docs]"; \
		cd docs && $(VENV_BIN)/sphinx-build -b html . _build/html; \
	else echo "no Sphinx docs/ found"; fi

serve-docs: docs ## Serve docs locally (http://localhost:8000)
	@if [ -d "docs/_build/html" ]; then \
		echo "$(BLUE)Serving docs at http://localhost:8000$(NC)"; \
		$(PYTHON) -m http.server 8000 -d docs/_build/html; \
	else echo "no built docs under docs/_build/html"; fi

docs-clean: ## Clean docs build
	@if [ -d "docs/_build" ]; then $(RM) docs/_build; fi

# --- CI/Development Utilities ---

ci-local: ## Run local CI checks (format + lint + unit)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test-unit
	@echo "$(GREEN)Local CI checks passed$(NC)"

pre-commit-run: venv ## Run pre-commit hooks (non-fatal)
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) run --all-files || true

pre-commit-update: venv ## Update pre-commit hooks (non-fatal)
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) autoupdate || true

fix: format ## Alias to auto-format

# --- Project Info & Diagnostics ---

version: ## Show version info
	@echo "$(BLUE)Python:$(NC) $$($(PYTHON) --version)"
	@echo "$(BLUE)UV:$(NC) $$($(UV) --version 2>/dev/null || echo 'not installed')"
	@echo "$(BLUE)Docker:$(NC) $$($(DOCKER) --version 2>/dev/null || echo 'not installed')"
	@if [ -f "pyproject.toml" ]; then \
		VER=$$(grep '^version' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/'); \
		echo "$(BLUE)Project:$(NC) $$VER"; \
	fi

version-bump: venv ## Bump version (patch)
	@command -v $(VENV_BIN)/bump2version >/dev/null 2>&1 || $(UV) pip install bump2version
	$(VENV_BIN)/bump2version patch

git-tag: ## Create annotated git tag from pyproject version
	@if [ -f "pyproject.toml" ]; then \
		VER=$$(grep '^version' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/'); \
		git tag -a "v$$VER" -m "Release v$$VER"; \
		echo "$(GREEN)Tagged v$$VER$(NC)"; \
	else echo "$(RED)No pyproject.toml found$(NC)"; fi

info: ## Show project/environment info
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
	@echo -n "$(BLUE)Tests dir:$(NC) "; if [ -d "tests" ]; then echo "✓"; else echo "✗"; fi
	@echo -n "$(BLUE)Docker:$(NC) "; $(DOCKER) --version >/dev/null 2>/dev/null && echo "✓" || echo "✗"

diagnose: health-check info ## Full diagnostics

# --- Shortcuts ---

quickstart: check-uv venv install-all verify-install ## Complete setup (no venv prompt)
	@echo "$(GREEN)Quickstart complete$(NC)"

dev: install-all pre-commit-install ## Setup dev env
	@echo "$(GREEN)Dev environment ready$(NC)"

check: format lint test-unit ## Pre-commit validation
	@echo "$(GREEN)Checks passed$(NC)"

pre-commit-install: venv ## Install pre-commit hooks
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) install || true
