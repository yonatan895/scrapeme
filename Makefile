.PHONY: help venv install install-dev install-all sync upgrade compile-requirements \
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

# Colors (no-op on Windows)
ifneq ($(OS),Windows_NT)
    GREEN := \033[0;32m
    YELLOW := \033[0;33m
    RED := \033[0;31m
    BLUE := \033[0;34m
    NC := \033[0m
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

venv: check-uv ## Create virtual environment via UV
	@if [ -d "$(VENV)" ]; then echo "$(YELLOW)venv exists$(NC)"; exit 0; fi
	$(UV) venv
	@echo "$(GREEN)venv created$(NC)"

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
	$(PYTEST) -v --cov=core --cov=config --cov=infra --cov-report=term-missing:skip-covered

test-unit: venv ## Unit tests only
	@if [ -d "tests/unit" ]; then $(PYTEST) tests/unit -v -m unit || true; else echo "no tests/unit"; fi

test-integration: venv ## Integration tests
	@if [ -d "tests/integration" ]; then $(PYTEST) tests/integration -v -m integration || true; else echo "no tests/integration"; fi

test-e2e: venv ## End-to-end tests
	@if [ -d "tests/e2e" ]; then $(PYTEST) tests/e2e -v -m e2e --timeout=300 || true; else echo "no tests/e2e"; fi

test-property: venv ## Property-based tests
	@if [ -d "tests/property" ]; then $(PYTEST) tests/property -v -m property || true; else echo "no tests/property"; fi

test-load: venv ## Load tests marker
	@if [ -d "tests/load" ]; then $(PYTEST) tests/load -v -m load || true; else echo "no tests/load"; fi

test-chaos: venv ## Chaos tests
	@if [ -d "tests/chaos" ]; then $(PYTEST) tests/chaos -v -m chaos || true; else echo "no tests/chaos"; fi

# --- Quality ---

lint: venv ## Run code quality checks
	$(BLACK) --check --diff core/ config/ infra/ tests/ runner.py
	$(ISORT) --check-only --diff core/ config/ infra/ tests/ runner.py
	$(MYPY) core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes
	$(PYLINT) core/ config/ infra/ runner.py --fail-under=8.5

format: venv ## Auto-format code
	$(BLACK) core/ config/ infra/ tests/ runner.py
	$(ISORT) core/ config/ infra/ tests/ runner.py

type-check: venv ## Type checking report
	$(MYPY) core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes

security-check: venv ## Security scans (bandit + safety)
	$(BANDIT) -r core/ config/ infra/ runner.py -ll -f json -o bandit-report.json || true
	$(SAFETY) check --json --output safety-report.json --continue-on-error || true

# --- Docker & Compose (unchanged compose-up kept) ---

compose-up: ## Start full stack (Selenium Grid + Monitoring)
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml up -d
	@printf '  Selenium Hub:  $(BLUE)http://localhost:4444$(NC)\n'
	@printf '  Prometheus:    $(BLUE)http://localhost:9091$(NC)\n'
	@printf '  Grafana:       $(BLUE)http://localhost:3000$(NC) (admin/admin)\n'
	@printf '  Alertmanager:  $(BLUE)http://localhost:9093$(NC)\n'

compose-down: ## Stop Docker Compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down

compose-logs: ## View Docker Compose logs
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml logs -f

compose-ps: ## Show running Docker Compose containers
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml ps

compose-clean: ## Stop and remove volumes
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml down -v

# --- Load testing ---

load-run: venv ## Headless Locust (USERS, SPAWN, DURATION, LOAD_BASE_URL)
	@USERS=$${USERS:-30}; SPAWN=$${SPAWN:-3}; DURATION=$${DURATION:-1m}; \
	command -v $(VENV_BIN)/locust >/dev/null 2>&1 || $(UV) pip install -e ".[load]"; \
	$(VENV_BIN)/locust -f tests/load/locustfile.py --headless -u "$$USERS" -r "$$SPAWN" -t "$$DURATION"

# --- Shortcuts ---

quickstart: venv install-all verify-install ## Complete setup
	@echo "$(GREEN)Quickstart complete$(NC)"

dev: install-all pre-commit-install ## Setup dev env
	@echo "$(GREEN)Dev environment ready$(NC)"

check: format lint test-unit ## Pre-commit validation
	@echo "$(GREEN)Checks passed$(NC)"

pre-commit-install: venv ## Install pre-commit hooks
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) install || true
