.PHONY: help venv venv-clear install install-dev install-all sync upgrade compile-requirements \
        test test-unit test-integration test-e2e test-property test-load test-chaos test-all \
        lint format type-check security-check benchmark clean clean-all \
        docker-build docker-build-dev docker-test docker-push docker-run docker-scan docker-prepare docker-shell docker-clean \
        docs serve-docs docs-clean compose-up compose-down compose-logs compose-ps compose-restart compose-clean \
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

# (the rest of the file remains unchanged until Docker & Compose section)

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

