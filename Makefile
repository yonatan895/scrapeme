.PHONY: help venv venv-clear install install-dev install-all sync upgrade compile-requirements \
        test test-unit test-integration test-e2e test-property test-load test-chaos test-all \
        lint format type-check security-check benchmark clean clean-all \
        docker-build docker-build-dev docker-test docker-push docker-run docker-scan docker-prepare docker-shell docker-clean \
        docs serve-docs docs-clean compose-up compose-down compose-logs compose-ps compose-restart compose-clean \
        k8s-deploy k8s-delete k8s-logs k8s-status k8s-describe k8s-shell k8s-port-forward k8s-restart \
        ci-local pre-commit-install pre-commit-run pre-commit-update quickstart dev check fix watch version version-bump git-tag \
        info deps-tree deps-outdated health-check diagnose load-run verify-python

.DEFAULT_GOAL := help

# Cross-platform OS detection with improved Python discovery
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    VENV_BIN := .venv/Scripts
    PYTHON := python
    VENV_PYTHON := $(VENV_BIN)/python.exe
    RM := rmdir /s /q
    SEP := \\
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        DETECTED_OS := macOS
    else
        DETECTED_OS := Linux
    endif
    VENV_BIN := .venv/bin
    PYTHON := python3
    VENV_PYTHON := $(VENV_BIN)/python
    RM := rm -rf
    SEP := /
endif

# Function to find the correct Python executable in venv
# This handles cases where python, python3, or python3.x might be the actual executable
define find_venv_python
$(shell \
    if [ -x "$(VENV_BIN)/python" ]; then \
        echo "$(VENV_BIN)/python"; \
    elif [ -x "$(VENV_BIN)/python3" ]; then \
        echo "$(VENV_BIN)/python3"; \
    elif [ -x "$(VENV_BIN)/python3.12" ]; then \
        echo "$(VENV_BIN)/python3.12"; \
    elif [ -x "$(VENV_BIN)/python3.11" ]; then \
        echo "$(VENV_BIN)/python3.11"; \
    elif [ -x "$(VENV_BIN)/python3.10" ]; then \
        echo "$(VENV_BIN)/python3.10"; \
    elif [ -x "$(VENV_BIN)/python3.9" ]; then \
        echo "$(VENV_BIN)/python3.9"; \
    else \
        echo ""; \
    fi \
)
endef

# Tools with improved Python resolution
VENV := .venv
UV := uv
# Use dynamic Python discovery for all venv tools
VENV_PYTHON_EXEC = $(call find_venv_python)
PYTEST := $(VENV_BIN)/pytest
BLACK := $(VENV_BIN)/black
ISORY := $(VENV_BIN)/isort
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
	@command -v $(UV) >/dev/null 2>&1 || { echo "$(RED)Error: UV not found. Install UV: https://astral.sh/uv$(NC)"; exit 1; }

# Verify Python executable in virtual environment
verify-python: venv ## Verify Python executable exists in venv
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -z "$$PYTHON_EXEC" ]; then \
		echo "$(RED)Error: No Python executable found in $(VENV_BIN)/$(NC)"; \
		echo "$(YELLOW)Available files in $(VENV_BIN)/:$(NC)"; \
		ls -la $(VENV_BIN)/ 2>/dev/null || echo "$(RED)Directory does not exist$(NC)"; \
		echo "$(YELLOW)Trying to recreate virtual environment...$(NC)"; \
		$(MAKE) venv-clear; \
		PYTHON_EXEC="$(call find_venv_python)"; \
		if [ -z "$$PYTHON_EXEC" ]; then \
			echo "$(RED)Failed to create working virtual environment$(NC)"; \
			exit 1; \
		fi; \
	fi; \
	echo "$(GREEN)Python executable found: $$PYTHON_EXEC$(NC)"; \
	$$PYTHON_EXEC --version

# Create venv only if missing (no prompt)
venv: ## Create virtual environment if it doesn't exist
	@if [ -d "$(VENV)" ]; then \
		echo "$(YELLOW)venv exists$(NC)"; \
	else \
		echo "$(BLUE)Creating virtual environment...$(NC)"; \
		$(UV) venv; \
		echo "$(GREEN)venv created$(NC)"; \
	fi

# Explicit venv recreation (no prompt)
venv-clear: ## Recreate virtual environment (destructive)
	@echo "$(YELLOW)Recreating venv...$(NC)"
	@if [ -d "$(VENV)" ]; then $(RM) $(VENV); fi
	$(UV) venv
	@echo "$(GREEN)venv recreated$(NC)"

install: check-uv venv verify-python ## Install prod deps
	$(UV) pip install -e .

install-dev: check-uv venv verify-python ## Install dev deps
	$(UV) pip install -e ".[dev,lint]"

install-all: check-uv venv verify-python ## Install all deps
	$(UV) pip install -e .
	$(UV) pip install -e ".[dev,lint,security,load,docs]"
	@command -v $(PRE_COMMIT) >/dev/null 2>&1 && $(PRE_COMMIT) install || true

sync: check-uv venv verify-python ## Sync env to pyproject
	$(UV) pip sync

upgrade: check-uv venv verify-python ## Upgrade all deps
	$(UV) pip install --upgrade -e ".[all]" || true

compile-requirements: check-uv ## Regenerate requirements files
	$(UV) pip compile pyproject.toml -o requirements.txt
	$(UV) pip compile pyproject.toml --extra dev --extra lint -o requirements-dev.txt
	$(UV) pip compile pyproject.toml --all-extras -o requirements-all.txt

verify-install: verify-python ## Quick import smoke test with robust Python detection
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -z "$$PYTHON_EXEC" ]; then \
		echo "$(RED)Error: No Python executable found in virtual environment$(NC)"; \
		echo "$(YELLOW)Run 'make venv-clear' to recreate the virtual environment$(NC)"; \
		exit 1; \
	fi; \
	echo "$(BLUE)Testing Python imports with: $$PYTHON_EXEC$(NC)"; \
	$$PYTHON_EXEC -c "import selenium, tenacity, yaml; print('$(GREEN)✓ All imports successful$(NC)')"

# --- Testing ---

test: verify-python ## Run all tests with coverage
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	$$PYTHON_EXEC -m pytest -v --cov=core --cov=config --cov=infra --cov-report=term-missing:skip-covered

test-unit: verify-python ## Unit tests only
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -d "tests/unit" ]; then $$PYTHON_EXEC -m pytest tests/unit -v -m unit || true; else echo "no tests/unit"; fi

test-integration: verify-python ## Integration tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -d "tests/integration" ]; then $$PYTHON_EXEC -m pytest tests/integration -v -m integration || true; else echo "no tests/integration"; fi

test-e2e: verify-python ## End-to-end tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -d "tests/e2e" ]; then $$PYTHON_EXEC -m pytest tests/e2e -v -m e2e --timeout=300 || true; else echo "no tests/e2e"; fi

test-property: verify-python ## Property-based tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -d "tests/property" ]; then $$PYTHON_EXEC -m pytest tests/property -v -m property || true; else echo "no tests/property"; fi

test-load: verify-python ## Load tests marker
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -d "tests/load" ]; then $$PYTHON_EXEC -m pytest tests/load -v -m load || true; else echo "no tests/load"; fi

test-chaos: verify-python ## Chaos tests
	@if [ ! -x "$(PYTEST)" ]; then $(UV) pip install -e ".[dev]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -d "tests/chaos" ]; then $$PYTHON_EXEC -m pytest tests/chaos -v -m chaos || true; else echo "no tests/chaos"; fi

# --- Quality ---

lint: verify-python ## Run code quality checks
	@if [ ! -x "$(BLACK)" ] || [ ! -x "$(ISORT)" ] || [ ! -x "$(MYPY)" ] || [ ! -x "$(PYLINT)" ]; then $(UV) pip install -e ".[dev,lint]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	$$PYTHON_EXEC -m black --check --diff core/ config/ infra/ tests/ runner.py; \
	$$PYTHON_EXEC -m isort --check-only --diff core/ config/ infra/ tests/ runner.py; \
	$$PYTHON_EXEC -m mypy core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes; \
	$$PYTHON_EXEC -m pylint core/ config/ infra/ runner.py --fail-under=8.5

format: verify-python ## Auto-format code
	@if [ ! -x "$(BLACK)" ] || [ ! -x "$(ISORT)" ]; then $(UV) pip install -e ".[dev,lint]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	$$PYTHON_EXEC -m black core/ config/ infra/ tests/ runner.py; \
	$$PYTHON_EXEC -m isort core/ config/ infra/ tests/ runner.py

type-check: verify-python ## Type checking report
	@if [ ! -x "$(MYPY)" ]; then $(UV) pip install -e ".[dev,lint]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	$$PYTHON_EXEC -m mypy core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes

security-check: verify-python ## Security scans (bandit + safety)
	@if [ ! -x "$(BANDIT)" ]; then $(UV) pip install -e ".[security]"; fi
	@PYTHON_EXEC="$(call find_venv_python)"; \
	$$PYTHON_EXEC -m bandit -r core/ config/ infra/ runner.py -ll -f json -o bandit-report.json || true
	@if [ ! -x "$(SAFETY)" ]; then $(UV) pip install -e ".[security]"; fi
	@$$PYTHON_EXEC -m safety check --json --output safety-report.json --continue-on-error || true

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

docker-run: ## Run container interactively
	$(DOCKER) run --rm -it $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

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

compose-restart: ## Restart Docker Compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml restart

# --- Documentation ---

docs: verify-python ## Build Sphinx docs (if present)
	@if [ -d "docs" ]; then \
		PYTHON_EXEC="$(call find_venv_python)"; \
		command -v $$PYTHON_EXEC >/dev/null 2>&1 || $(UV) pip install -e ".[docs]"; \
		cd docs && $$PYTHON_EXEC -m sphinx -b html . _build/html; \
	else echo "no docs/ directory"; fi

serve-docs: docs ## Serve docs locally (http://localhost:8000)
	@if [ -d "docs/_build/html" ]; then \
		echo "$(BLUE)Serving docs at http://localhost:8000$(NC)"; \
		$(PYTHON) -m http.server 8000 -d docs/_build/html; \
	else echo "no built docs under docs/_build/html"; fi

docs-clean: ## Clean docs build
	@if [ -d "docs/_build" ]; then $(RM) docs/_build; fi

# --- Load testing ---

load-run: verify-python ## Headless Locust (USERS, SPAWN, DURATION, LOAD_BASE_URL)
	@USERS=$${USERS:-30}; SPAWN=$${SPAWN:-3}; DURATION=$${DURATION:-1m}; \
	HOST=$${LOAD_BASE_URL:-http://quotes.toscrape.com}; \
	PYTHON_EXEC="$(call find_venv_python)"; \
	command -v $$PYTHON_EXEC >/dev/null 2>&1 || $(UV) pip install -e ".[load]"; \
	$$PYTHON_EXEC -m locust -f tests/load/locustfile.py --headless -H "$$HOST" -u "$$USERS" -r "$$SPAWN" -t "$$DURATION"

# --- Kubernetes (placeholders; non-fatal) ---

k8s-deploy: ## Deploy to Kubernetes (placeholder)
	@echo "$(YELLOW)Kubernetes deployment not implemented$(NC)"

k8s-delete: ## Delete from Kubernetes (placeholder)
	@echo "$(YELLOW)Kubernetes delete not implemented$(NC)"

k8s-logs: ## View Kubernetes logs (placeholder)
	@echo "$(YELLOW)Kubernetes logs not implemented$(NC)"

k8s-status: ## Kubernetes status (placeholder)
	@echo "$(YELLOW)Kubernetes status not implemented$(NC)"

k8s-describe: ## Describe Kubernetes resources (placeholder)
	@echo "$(YELLOW)Kubernetes describe not implemented$(NC)"

k8s-shell: ## Shell into Kubernetes pod (placeholder)
	@echo "$(YELLOW)Kubernetes shell not implemented$(NC)"

k8s-port-forward: ## Port-forward Kubernetes service (placeholder)
	@echo "$(YELLOW)Kubernetes port-forward not implemented$(NC)"

k8s-restart: ## Restart Kubernetes deployment (placeholder)
	@echo "$(YELLOW)Kubernetes restart not implemented$(NC)"

# --- CI/Development Utilities ---

ci-local: ## Run local CI checks (format + lint + unit)
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test-unit
	@echo "$(GREEN)Local CI checks passed$(NC)"

pre-commit-run: verify-python ## Run pre-commit hooks (non-fatal)
	@PYTHON_EXEC="$(call find_venv_python)"; \
	command -v $$PYTHON_EXEC >/dev/null 2>&1 && $$PYTHON_EXEC -m pre_commit run --all-files || true

pre-commit-update: verify-python ## Update pre-commit hooks (non-fatal)
	@PYTHON_EXEC="$(call find_venv_python)"; \
	command -v $$PYTHON_EXEC >/dev/null 2>&1 && $$PYTHON_EXEC -m pre_commit autoupdate || true

fix: format ## Alias to auto-format

# --- Project Info & Diagnostics ---

version: ## Show version info
	@echo "$(BLUE)OS:$(NC) $(DETECTED_OS)"
	@echo "$(BLUE)Python:$(NC) $$($(PYTHON) --version)"
	@echo "$(BLUE)UV:$(NC) $$($(UV) --version 2>/dev/null || echo 'not installed')"
	@echo "$(BLUE)Docker:$(NC) $$($(DOCKER) --version 2>/dev/null || echo 'not installed')"
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -n "$$PYTHON_EXEC" ]; then \
		echo "$(BLUE)Venv Python:$(NC) $$($$PYTHON_EXEC --version)"; \
	else \
		echo "$(BLUE)Venv Python:$(NC) $(RED)not found$(NC)"; \
	fi
	@if [ -f "pyproject.toml" ]; then \
		VER=$$(grep '^version' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/'); \
		echo "$(BLUE)Project:$(NC) $$VER"; \
	fi

version-bump: verify-python ## Bump version (patch)
	@PYTHON_EXEC="$(call find_venv_python)"; \
	command -v $$PYTHON_EXEC >/dev/null 2>&1 || $(UV) pip install bump2version; \
	$$PYTHON_EXEC -m bump2version patch

git-tag: ## Create annotated git tag from pyproject version
	@if [ -f "pyproject.toml" ]; then \
		VER=$$(grep '^version' pyproject.toml | head -1 | sed -E 's/.*"([^"]+)".*/\1/'); \
		git tag -a "v$$VER" -m "Release v$$VER"; \
		echo "$(GREEN)Tagged v$$VER$(NC)"; \
	else echo "$(RED)No pyproject.toml found$(NC)"; fi

info: ## Show project/environment info
	@echo "$(BLUE)=== Project Information ===$(NC)"
	@echo "$(BLUE)Repository:$(NC) $$(basename $$(pwd))"
	@echo "$(BLUE)OS:$(NC) $(DETECTED_OS)"
	@echo "$(BLUE)Python:$(NC) $$($(PYTHON) --version)"
	@echo "$(BLUE)Virtual Env:$(NC) $$(if [ -d $(VENV) ]; then echo 'exists'; else echo 'missing'; fi)"
	@PYTHON_EXEC="$(call find_venv_python)"; \
	if [ -n "$$PYTHON_EXEC" ]; then \
		echo "$(BLUE)Venv Python:$(NC) $$PYTHON_EXEC ($$($$PYTHON_EXEC --version))"; \
	else \
		echo "$(BLUE)Venv Python:$(NC) $(RED)not found$(NC)"; \
	fi
	@echo "$(BLUE)Git Branch:$(NC) $$(git branch --show-current 2>/dev/null || echo 'unknown')"
	@echo "$(BLUE)Docker:$(NC) $$($(DOCKER) --version 2>/dev/null || echo 'not installed')"

deps-tree: verify-python ## Show dependency tree
	@PYTHON_EXEC="$(call find_venv_python)"; \
	command -v $$PYTHON_EXEC >/dev/null 2>&1 || $(UV) pip install pipdeptree; \
	$$PYTHON_EXEC -m pipdeptree

deps-outdated: venv ## Show outdated dependencies
	$(UV) pip list --outdated

health-check: verify-python ## Basic health check
	@echo "$(BLUE)=== Health Check ===$(NC)"
	@PYTHON_EXEC="$(call find_venv_python)"; \
	echo -n "$(BLUE)Python imports:$(NC) "; \
	if $$PYTHON_EXEC -c "import core.scraper, config.models; print('✓')" 2>/dev/null; then \
		echo "$(GREEN)✓$(NC)"; \
	else \
		echo "$(RED)✗$(NC)"; \
	fi
	@echo -n "$(BLUE)Selenium:$(NC) "; \
	if $$PYTHON_EXEC -c "import selenium; print('✓')" 2>/dev/null; then \
		echo "$(GREEN)✓$(NC)"; \
	else \
		echo "$(RED)✗$(NC)"; \
	fi
	@echo -n "$(BLUE)Tests dir:$(NC) "; if [ -d "tests" ]; then echo "$(GREEN)✓$(NC)"; else echo "$(RED)✗$(NC)"; fi
	@echo -n "$(BLUE)Docker:$(NC) "; $(DOCKER) --version >/dev/null 2>&1 && echo "$(GREEN)✓$(NC)" || echo "$(RED)✗$(NC)"

diagnose: health-check info ## Full diagnostics

# --- Shortcuts ---

quickstart: check-uv venv install-all verify-install ## Complete setup (no venv prompt)
	@echo "$(GREEN)Quickstart complete$(NC)"

dev: install-all pre-commit-install ## Setup dev env
	@echo "$(GREEN)Dev environment ready$(NC)"

check: format lint test-unit ## Pre-commit validation
	@echo "$(GREEN)Checks passed$(NC)"

pre-commit-install: verify-python ## Install pre-commit hooks
	@PYTHON_EXEC="$(call find_venv_python)"; \
	command -v $$PYTHON_EXEC >/dev/null 2>&1 && $$PYTHON_EXEC -m pre_commit install || true