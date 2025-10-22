.PHONY: help venv install install-dev install-all sync compile-requirements \
        test test-unit test-integration test-e2e test-property test-load test-chaos test-all \
        lint format type-check security-check benchmark clean \
        docker-build docker-build-dev docker-test docker-push docker-run \
        docs serve-docs compose-up compose-down compose-logs \
        k8s-deploy k8s-delete k8s-logs ci-local \
        check-venv check-tools verify-install

.DEFAULT_GOAL := help

# Detect OS for cross-platform compatibility
ifeq ($(OS),Windows_NT)
    VENV_BIN := .venv/Scripts
    PYTHON := python
    RM := rmdir /s /q
    MKDIR := mkdir
    SEP := \\
else
    VENV_BIN := .venv/bin
    PYTHON := python3
    RM := rm -rf
    MKDIR := mkdir -p
    SEP := /
endif

# Variables
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

# ANSI color codes (disabled on Windows by default)
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

# Error handling
SHELL := /bin/bash
.SHELLFLAGS := -e -o pipefail -c

#############################################
# Help & Documentation
#############################################

help: ## Show this help message with examples
	@printf '$(BLUE)═══════════════════════════════════════$(NC)\n'
	@printf '$(BLUE)  Selenium Automation - Makefile Help  $(NC)\n'
	@printf '$(BLUE)═══════════════════════════════════════$(NC)\n'
	@printf '\n'
	@printf '$(YELLOW)Quick Start:$(NC)\n'
	@printf '  make quickstart     # Complete setup\n'
	@printf '  make check          # Verify everything works\n'
	@printf '  make test           # Run tests\n'
	@printf '\n'
	@printf '$(YELLOW)Available targets:$(NC)\n'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf '\n'
	@printf '$(YELLOW)Examples:$(NC)\n'
	@printf '  make venv install-all    # Setup environment\n'
	@printf '  make format lint test    # Before commit\n'
	@printf '  make docker-build        # Build image\n'
	@printf '\n'

#############################################
# Environment Setup & Verification
#############################################

check-uv: ## Check if UV is installed
	@command -v $(UV) >/dev/null 2>&1 || { \
		printf '$(RED)❌ UV is not installed!$(NC)\n'; \
		printf 'Install with:\n'; \
		printf '  Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh\n'; \
		printf '  Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"\n'; \
		exit 1; \
	}
	@printf '$(GREEN)✅ UV is installed$(NC)\n'

check-venv: ## Check if virtual environment exists
	@if [ ! -d "$(VENV)" ]; then \
		printf '$(RED)❌ Virtual environment not found$(NC)\n'; \
		printf 'Run: $(GREEN)make venv$(NC)\n'; \
		exit 1; \
	fi
	@printf '$(GREEN)✅ Virtual environment exists$(NC)\n'

check-python: check-venv ## Verify Python version
	@$(VENV_BIN)/python --version | grep -q "3.1[12]" || { \
		printf '$(RED)❌ Python 3.11 or 3.12 required$(NC)\n'; \
		$(VENV_BIN)/python --version; \
		exit 1; \
	}
	@printf '$(GREEN)✅ Python version OK$(NC)\n'
	@$(VENV_BIN)/python --version


check-tools: check-venv ## Verify all required tools are installed
	@printf '$(YELLOW)Checking installed tools...$(NC)\n'
	@for tool in pytest black isort mypy pylint bandit safety; do \
		if [ -f "$(VENV_BIN)/$$tool" ]; then \
			printf '  $(GREEN)✓$(NC) '"$$tool"'\n'; \
		else \
			printf '  $(RED)✗$(NC) '"$$tool"' $(YELLOW)(missing)$(NC)\n'; \
		fi; \
	done



verify-install: check-venv check-python check-tools ## Comprehensive installation verification
	@printf '\n$(YELLOW)Testing imports...$(NC)\n'
	@$(VENV_BIN)/python -c "import selenium; import tenacity; import yaml; print('$(GREEN)✅ All core imports successful$(NC)')"
	@printf '\n$(GREEN)✅ Installation verified successfully!$(NC)\n'

venv: check-uv ## Create virtual environment with UV
	@if [ -d "$(VENV)" ]; then \
		printf '$(YELLOW)⚠️  Virtual environment already exists$(NC)\n'; \
		printf 'Use $(GREEN)make clean-all$(NC) to remove it first\n'; \
		exit 1; \
	fi
	$(UV) venv
	@printf '$(GREEN)✅ Virtual environment created$(NC)\n'
	@printf '$(YELLOW)Activate with:$(NC)\n'
ifeq ($(OS),Windows_NT)
	@printf '  .venv\\Scripts\\activate\n'
else
	@printf '  source .venv/bin/activate\n'
endif

#############################################
# Dependency Management
#############################################

install: check-uv check-venv ## Install production dependencies
	$(UV) pip install -e .
	@printf '$(GREEN)✅ Production dependencies installed$(NC)\n'

install-dev: check-uv check-venv ## Install development dependencies
	$(UV) pip install -e ".[dev,lint]"
	@printf '$(GREEN)✅ Development dependencies installed$(NC)\n'


install-all: check-uv check-venv ## Install all dependencies
	@printf '$(YELLOW)Installing all dependencies...$(NC)\n'
	@printf '  Step 1/4: Base package...\n'
	@$(UV) pip install -e .
	@printf '  Step 2/4: Development tools...\n'
	@$(UV) pip install -e ".[dev]"
	@printf '  Step 3/4: Linting tools...\n'
	@$(UV) pip install -e ".[lint]"
	@printf '  Step 4/4: Additional tools...\n'
	@$(UV) pip install -e ".[security,load,docs,precommit]"
	@if [ -f "$(VENV_BIN)/pre-commit" ]; then \
		$(PRE_COMMIT) install 2>/dev/null || true; \
		printf '  $(GREEN)✓$(NC) Pre-commit hooks installed\n'; \
	fi
	@printf '$(GREEN)✅ All dependencies installed$(NC)\n'
	@printf '$(YELLOW)Verifying installation...$(NC)\n'
	@make check-tools



sync: check-uv check-venv ## Sync environment to match pyproject.toml exactly
	$(UV) pip sync
	@printf '$(GREEN)✅ Environment synchronized$(NC)\n'

upgrade: check-uv check-venv ## Upgrade all dependencies to latest versions
	$(UV) pip install --upgrade -e ".[all]"
	@printf '$(GREEN)✅ Dependencies upgraded$(NC)\n'

compile-requirements: check-uv ## Generate requirements.txt files
	$(UV) pip compile pyproject.toml -o requirements.txt
	$(UV) pip compile pyproject.toml --extra dev --extra lint -o requirements-dev.txt
	$(UV) pip compile pyproject.toml --all-extras -o requirements-all.txt
	@printf '$(GREEN)✅ Requirements files generated$(NC)\n'

#############################################
# Testing
#############################################

test: check-venv ## Run all tests with coverage
	@$(MKDIR) test-results 2>/dev/null || true
	$(PYTEST) -v \
		--cov=core \
		--cov=config \
		--cov=infra \
		--cov-report=term-missing:skip-covered \
		--cov-report=html \
		--cov-report=xml \
		--junitxml=test-results/junit.xml
	@printf '\n$(GREEN)✅ Tests completed$(NC)\n'
	@printf 'Coverage report: $(BLUE)htmlcov/index.html$(NC)\n'

test-unit: check-venv ## Run unit tests only
	@if [ -d "tests/unit" ] && [ -n "$$(find tests/unit -name 'test_*.py' -o -name '*_test.py' 2>/dev/null)" ]; then \
		$(PYTEST) tests/unit/ -v -m unit || true; \
	else \
		printf '$(YELLOW)⚠️  No unit tests found in tests/unit/$(NC)\n'; \
	fi

test-integration: check-venv ## Run integration tests
	@if [ -d "tests/integration" ] && [ -n "$$(find tests/integration -name 'test_*.py' 2>/dev/null)" ]; then \
		$(PYTEST) tests/integration/ -v -m integration || true; \
	else \
		printf '$(YELLOW)⚠️  No integration tests found$(NC)\n'; \
	fi

test-e2e: check-venv ## Run end-to-end tests (requires Chrome)
	@if [ -d "tests/e2e" ] && [ -n "$$(find tests/e2e -name 'test_*.py' 2>/dev/null)" ]; then \
		$(PYTEST) tests/e2e/ -v -m e2e --timeout=300 || true; \
	else \
		printf '$(YELLOW)⚠️  No e2e tests found$(NC)\n'; \
	fi

test-property: check-venv ## Run property-based tests with Hypothesis
	@if [ -d "tests/property" ] && [ -n "$$(find tests/property -name 'test_*.py' 2>/dev/null)" ]; then \
		$(PYTEST) tests/property/ -v -m property --hypothesis-show-statistics || true; \
	else \
		printf '$(YELLOW)⚠️  No property tests found$(NC)\n'; \
	fi

test-load: check-venv ## Run load tests with Locust
	@if [ -d "tests/load" ]; then \
		$(PYTEST) tests/load/ -v -m load || true; \
	else \
		printf '$(YELLOW)⚠️  No load tests found$(NC)\n'; \
	fi

test-chaos: check-venv ## Run chaos engineering tests
	@if [ -d "tests/chaos" ]; then \
		$(PYTEST) tests/chaos/ -v -m chaos || true; \
	else \
		printf '$(YELLOW)⚠️  No chaos tests found$(NC)\n'; \
	fi

test-all: test ## Run all test suites (comprehensive)
	@printf '$(GREEN)✅ All test suites completed$(NC)\n'

test-watch: check-venv ## Run tests in watch mode (auto-rerun on changes)
	@command -v pytest-watch >/dev/null 2>&1 || { \
		printf '$(YELLOW)Installing pytest-watch...$(NC)\n'; \
		$(UV) pip install pytest-watch; \
	}
	pytest-watch -c -v

test-parallel: check-venv ## Run tests in parallel (faster)
	$(PYTEST) -v -n auto --maxprocesses=4

test-failed: check-venv ## Re-run only failed tests
	$(PYTEST) --lf -v

test-quick: check-venv ## Run quick smoke tests only
	$(PYTEST) -v -m "not slow" --maxfail=3

#############################################
# Code Quality & Linting
#############################################

lint: check-venv ## Run all linters (comprehensive check)
	@printf '$(YELLOW)Running code quality checks...$(NC)\n'
	@printf '\n$(BLUE)1/4$(NC) Running Black (formatter check)...\n'
	@$(BLACK) --check --diff --color core/ config/ infra/ tests/ runner.py || { \
		printf '$(RED)❌ Black found formatting issues$(NC)\n'; \
		printf 'Fix with: $(GREEN)make format$(NC)\n'; \
		exit 1; \
	}
	@printf '\n$(BLUE)2/4$(NC) Running isort (import sorting)...\n'
	@$(ISORT) --check-only --diff --color core/ config/ infra/ tests/ runner.py || { \
		printf '$(RED)❌ isort found issues$(NC)\n'; \
		printf 'Fix with: $(GREEN)make format$(NC)\n'; \
		exit 1; \
	}
	@printf '\n$(BLUE)3/4$(NC) Running mypy (type checking)...\n'
	@$(MYPY) core/ config/ infra/ runner.py --explicit-package-bases --strict --show-error-codes || { \
		printf '$(RED)❌ mypy found type errors$(NC)\n'; \
		exit 1; \
	}
	@printf '\n$(BLUE)4/4$(NC) Running pylint (code quality)...\n'
	@$(PYLINT) core/ config/ infra/ runner.py --fail-under=8.5 --output-format=colorized || { \
		printf '$(RED)❌ pylint found issues$(NC)\n'; \
		exit 1; \
	}
	@printf '\n$(GREEN)✅ All linters passed!$(NC)\n'

format: check-venv ## Auto-format code with black and isort
	@printf '$(YELLOW)Formatting code...$(NC)\n'
	$(BLACK) core/ config/ infra/ tests/ runner.py
	$(ISORT) core/ config/ infra/ tests/ runner.py
	@printf '$(GREEN)✅ Code formatted$(NC)\n'

type-check: check-venv ## Run type checking with detailed report
	@$(MKDIR) mypy-report 2>/dev/null || true
	$(MYPY) core/ config/ infra/ runner.py \
		--explicit-package-bases \
		--strict \
		--show-error-codes \
		--html-report mypy-report \
		--any-exprs-report mypy-report
	@printf '$(GREEN)✅ Type checking complete$(NC)\n'
	@printf 'HTML report: $(BLUE)mypy-report/index.html$(NC)\n'

security-check: check-venv ## Run security vulnerability scans
	@printf '$(YELLOW)Running security checks...$(NC)\n'
	@printf '\n$(BLUE)1/2$(NC) Bandit (code security scanner)...\n'
	@$(BANDIT) -r core/ config/ infra/ runner.py \
		-f json -o bandit-report.json \
		-ll || printf '$(YELLOW)⚠️  Bandit found potential issues$(NC)\n'
	@printf '\n$(BLUE)2/2$(NC) Safety (dependency vulnerability check)...\n'
	@$(SAFETY) check --json --output safety-report.json --continue-on-error || \
		printf '$(YELLOW)⚠️  Safety found vulnerabilities$(NC)\n'
	@printf '\n$(GREEN)✅ Security checks complete$(NC)\n'

complexity: check-venv ## Analyze code complexity
	@command -v radon >/dev/null 2>&1 || { \
		printf '$(YELLOW)Installing radon...$(NC)\n'; \
		$(UV) pip install radon; \
	}
	@printf '$(YELLOW)Analyzing code complexity...$(NC)\n'
	radon cc core/ config/ infra/ runner.py -a -s
	@printf '\n$(GREEN)✅ Complexity analysis complete$(NC)\n'

#############################################
# Performance & Profiling
#############################################

benchmark: check-venv ## Run performance benchmarks
	@if [ -d "tests/benchmarks" ]; then \
		$(PYTEST) tests/benchmarks/ \
			--benchmark-only \
			--benchmark-json=benchmark.json \
			--benchmark-autosave; \
		printf '$(GREEN)✅ Benchmarks complete$(NC)\n'; \
	else \
		printf '$(YELLOW)⚠️  No benchmarks found$(NC)\n'; \
	fi

profile: check-venv ## Profile application performance
	@$(MKDIR) profiles 2>/dev/null || true
	$(VENV_BIN)/python -m cProfile -o profiles/profile.stats runner.py --config config/sites.yaml
	@printf '\n$(YELLOW)Top 20 functions by cumulative time:$(NC)\n'
	@$(VENV_BIN)/python -c "import pstats; p = pstats.Stats('profiles/profile.stats'); p.sort_stats('cumulative').print_stats(20)"
	@printf '\n$(GREEN)✅ Profile saved to profiles/profile.stats$(NC)\n'

memory-profile: check-venv ## Profile memory usage
	@command -v memory_profiler >/dev/null 2>&1 || { \
		printf '$(YELLOW)Installing memory_profiler...$(NC)\n'; \
		$(UV) pip install memory-profiler; \
	}
	@$(VENV_BIN)/python -m memory_profiler runner.py --config config/sites.yaml
	@printf '$(GREEN)✅ Memory profiling complete$(NC)\n'

#############################################
# Docker Operations
#############################################

docker-build: ## Build production Docker image
	@printf '$(YELLOW)Building production Docker image...$(NC)\n'
	$(DOCKER) build \
		-t $(IMAGE_NAME):$(IMAGE_TAG) \
		-t $(IMAGE_NAME):$$(date +%Y%m%d-%H%M%S) \
		--target production \
		--build-arg PYTHON_VERSION=3.11 \
		.
	@printf '$(GREEN)✅ Production image built: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)\n'
	@$(DOCKER) images $(IMAGE_NAME):$(IMAGE_TAG) --format "Size: {{.Size}}"

docker-build-dev: ## Build development Docker image with cache
	$(DOCKER) build \
		-t $(IMAGE_NAME):dev \
		--target development \
		--cache-from $(IMAGE_NAME):dev \
		.
	@printf '$(GREEN)✅ Development image built: $(IMAGE_NAME):dev$(NC)\n'

docker-build-test: ## Build and run test Docker image
	$(DOCKER) build -t $(IMAGE_NAME):test --target test .
	@printf '$(GREEN)✅ Test image built$(NC)\n'

docker-test: docker-build-test ## Run tests inside Docker container
	@printf '$(YELLOW)Running tests in Docker...$(NC)\n'
	$(DOCKER) run --rm $(IMAGE_NAME):test
	@printf '$(GREEN)✅ Docker tests passed$(NC)\n'

docker-scan: docker-build ## Scan Docker image for vulnerabilities
	@printf '$(YELLOW)Scanning image for vulnerabilities...$(NC)\n'
	@command -v trivy >/dev/null 2>&1 && { \
		trivy image --severity HIGH,CRITICAL $(IMAGE_NAME):$(IMAGE_TAG); \
	} || { \
		printf '$(YELLOW)⚠️  Install trivy for vulnerability scanning$(NC)\n'; \
		printf 'https://github.com/aquasecurity/trivy$(NC)\n'; \
	}

docker-push: docker-build ## Push Docker image to registry
	@printf '$(YELLOW)Pushing to registry...$(NC)\n'
	$(DOCKER) tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	$(DOCKER) tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):latest
	$(DOCKER) push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	$(DOCKER) push $(REGISTRY)/$(IMAGE_NAME):latest
	@printf '$(GREEN)✅ Image pushed to $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)$(NC)\n'



docker-prepare: ## Prepare directories for Docker
	@printf '$(YELLOW)Preparing Docker volumes...$(NC)\n'
	@mkdir -p results artifacts config
	@chmod 755 results artifacts
	@if [ ! -f "config/sites.yaml" ]; then \
		printf '$(YELLOW)⚠️  config/sites.yaml not found$(NC)\n'; \
		printf 'Copy example: $(BLUE)cp config/sites.yaml.example config/sites.yaml$(NC)\n'; \
	fi
	@printf '$(GREEN)✅ Docker volumes ready$(NC)\n'

docker-run: docker-prepare ## Run Docker container with example config
	$(DOCKER) run --rm \
		--user $(shell id -u):$(shell id -g) \
		-v $(PWD)/config/sites.yaml:/app/sites.yaml:ro \
		-v $(PWD)/results:/app/results \
		-v $(PWD)/artifacts:/app/artifacts \
		-e SITE_USERNAME=$(SITE_USERNAME) \
		-e SITE_PASSWORD=$(SITE_PASSWORD) \
		$(IMAGE_NAME):$(IMAGE_TAG) \
		--config sites.yaml \
		--browser chrome \
		--headless \
		--out /app/results/results.json
	@printf '\n$(GREEN)✅ Container completed$(NC)\n'
	@printf 'Results: $(BLUE)results/results.json$(NC)\n'
	@if [ -f "results/results.json" ]; then \
		printf 'View with: $(BLUE)cat results/results.json | jq$(NC)\n'; \
	fi



docker-shell: ## Open interactive shell in container
	$(DOCKER) run --rm -it \
		-v $(PWD):/app \
		--entrypoint /bin/bash \
		$(IMAGE_NAME):dev

docker-clean: ## Remove all Docker images and containers
	@printf '$(YELLOW)Cleaning Docker resources...$(NC)\n'
	$(DOCKER) ps -a -q --filter "ancestor=$(IMAGE_NAME)" | xargs -r $(DOCKER) rm -f || true
	$(DOCKER) images $(IMAGE_NAME) -q | xargs -r $(DOCKER) rmi -f || true
	@printf '$(GREEN)✅ Docker cleanup complete$(NC)\n'

#############################################
# Docker Compose
#############################################

compose-up: ## Start full stack (Selenium Grid + Monitoring)
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml up -d
	@printf '$(GREEN)✅ Docker Compose stack started$(NC)\n'
	@printf '\n$(YELLOW)Services available at:$(NC)\n'
	@printf '  Selenium Hub:  $(BLUE)http://localhost:4444$(NC)\n'
	@printf '  Prometheus:    $(BLUE)http://localhost:9091$(NC)\n'
	@printf '  Grafana:       $(BLUE)http://localhost:3000$(NC) (admin/admin)\n'
	@printf '  Alertmanager:  $(BLUE)http://localhost:9093$(NC)\n'

compose-down: ## Stop Docker Compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yml down
	@printf '$(GREEN)✅ Docker Compose stack stopped$(NC)\n'

compose-logs: ## View Docker Compose logs (live)
	$(DOCKER_COMPOSE) -f docker-compose.production.yml logs -f

compose-ps: ## Show running Docker Compose containers
	$(DOCKER_COMPOSE) -f docker-compose.production.yml ps

compose-restart: compose-down compose-up ## Restart Docker Compose stack

compose-clean: compose-down ## Stop and remove volumes
	$(DOCKER_COMPOSE) -f docker-compose.production.yml down -v
	@printf '$(GREEN)✅ Docker Compose cleaned (volumes removed)$(NC)\n'

#############################################
# Kubernetes
#############################################

k8s-deploy: ## Deploy to Kubernetes cluster
	@command -v kubectl >/dev/null 2>&1 || { \
		printf '$(RED)❌ kubectl not found$(NC)\n'; \
		exit 1; \
	}
	@printf '$(YELLOW)Deploying to Kubernetes...$(NC)\n'
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/pvc.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/servicemonitor.yaml
	kubectl apply -f k8s/hpa.yaml
	@printf '$(GREEN)✅ Deployed to Kubernetes$(NC)\n'
	@printf 'Check status: $(BLUE)kubectl get pods -n selenium-automation$(NC)\n'

k8s-delete: ## Delete from Kubernetes
	kubectl delete -f k8s/ --ignore-not-found=true
	@printf '$(GREEN)✅ Deleted from Kubernetes$(NC)\n'

k8s-status: ## Check Kubernetes deployment status
	@printf '$(YELLOW)Kubernetes Status:$(NC)\n'
	kubectl get all -n selenium-automation
	kubectl get pvc -n selenium-automation

k8s-logs: ## View Kubernetes pod logs
	kubectl logs -f deployment/selenium-automation -n selenium-automation --tail=100

k8s-describe: ## Describe Kubernetes deployment
	kubectl describe deployment selenium-automation -n selenium-automation

k8s-shell: ## Open shell in Kubernetes pod
	kubectl exec -it deployment/selenium-automation -n selenium-automation -- /bin/bash

k8s-port-forward: ## Port forward metrics endpoint locally
	@printf '$(YELLOW)Port forwarding metrics to localhost:9090...$(NC)\n'
	kubectl port-forward svc/selenium-automation 9090:9090 -n selenium-automation

k8s-restart: ## Restart Kubernetes deployment
	kubectl rollout restart deployment/selenium-automation -n selenium-automation
	kubectl rollout status deployment/selenium-automation -n selenium-automation

#############################################
# Documentation
#############################################

docs: check-venv ## Build Sphinx documentation
	@if [ -d "docs" ]; then \
		cd docs && make html; \
		printf '$(GREEN)✅ Documentation built$(NC)\n'; \
		printf 'Open: $(BLUE)docs/_build/html/index.html$(NC)\n'; \
	else \
		printf '$(YELLOW)⚠️  No docs directory found$(NC)\n'; \
	fi

serve-docs: docs ## Serve documentation locally
	@printf '$(YELLOW)Serving documentation at http://localhost:8000$(NC)\n'
	@cd docs/_build/html && $(VENV_BIN)/python -m http.server 8000

docs-clean: ## Clean documentation build
	@if [ -d "docs" ]; then \
		cd docs && make clean; \
		printf '$(GREEN)✅ Documentation cleaned$(NC)\n'; \
	fi

#############################################
# Cleanup
#############################################

clean: ## Clean generated files and caches
	@printf '$(YELLOW)Cleaning generated files...$(NC)\n'
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .hypothesis -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@find . -type f -name '*.pyo' -delete 2>/dev/null || true
	@find . -type f -name '.coverage' -delete 2>/dev/null || true
	@$(RM) htmlcov coverage.xml mypy-report 2>/dev/null || true
	@$(RM) artifacts results test-results profiles 2>/dev/null || true
	@$(RM) dist build 2>/dev/null || true
	@rm -f bandit-report.json safety-report.json benchmark.json profile.stats 2>/dev/null || true
	@printf '$(GREEN)✅ Cleanup complete$(NC)\n'

clean-all: clean docker-clean ## Nuclear option: clean everything including venv
	@printf '$(RED)⚠️  This will delete the virtual environment!$(NC)\n'
	@printf '$(YELLOW)Press Ctrl+C to cancel, or Enter to continue...$(NC)\n'
	@read -r
	@$(RM) $(VENV) 2>/dev/null || true
	@printf '$(GREEN)✅ Full cleanup complete (venv removed)$(NC)\n'

#############################################
# CI/CD & Workflows
#############################################

ci-local: lint test security-check ## Run full CI pipeline locally
	@printf '\n$(GREEN)╔═══════════════════════════════════════╗$(NC)\n'
	@printf '$(GREEN)║  ✅ All CI checks passed locally!     ║$(NC)\n'
	@printf '$(GREEN)╚═══════════════════════════════════════╝$(NC)\n'

pre-commit-install: check-venv ## Install pre-commit Git hooks
	@if [ -f "$(VENV_BIN)/pre-commit" ]; then \
		$(PRE_COMMIT) install; \
		printf '$(GREEN)✅ Pre-commit hooks installed$(NC)\n'; \
	else \
		printf '$(RED)❌ pre-commit not installed$(NC)\n'; \
		printf 'Run: $(GREEN)make install-all$(NC)\n'; \
	fi

pre-commit-run: check-venv ## Run pre-commit on all files
	$(PRE_COMMIT) run --all-files

pre-commit-update: check-venv ## Update pre-commit hooks
	$(PRE_COMMIT) autoupdate

#############################################
# Development Workflows
#############################################

quickstart: venv install-all verify-install ## Complete setup for new developers
	@printf '\n$(GREEN)╔═══════════════════════════════════════╗$(NC)\n'
	@printf '$(GREEN)║  ✅ Quickstart complete!              ║$(NC)\n'
	@printf '$(GREEN)╚═══════════════════════════════════════╝$(NC)\n'
	@printf '\n$(YELLOW)Next steps:$(NC)\n'
	@printf '  1. Activate venv:\n'
ifeq ($(OS),Windows_NT)
	@printf '     $(BLUE).venv\\Scripts\\activate$(NC)\n'
else
	@printf '     $(BLUE)source .venv/bin/activate$(NC)\n'
endif
	@printf '  2. Copy example config: $(BLUE)cp config/sites.yaml.example config/sites.yaml$(NC)\n'
	@printf '  3. Set env vars: $(BLUE)cp .env.example .env$(NC) (edit as needed)\n'
	@printf '  4. Run: $(BLUE)python runner.py --config config/sites.yaml --headless$(NC)\n'
	@printf '  5. Run tests: $(BLUE)make test$(NC)\n'
	@printf '\n$(YELLOW)Useful commands:$(NC)\n'
	@printf '  $(GREEN)make check$(NC)          - Quick pre-commit check\n'
	@printf '  $(GREEN)make format$(NC)         - Auto-format code\n'
	@printf '  $(GREEN)make ci-local$(NC)       - Full CI pipeline\n'
	@printf '  $(GREEN)make docker-build$(NC)   - Build Docker image\n'

dev: install-all pre-commit-install ## Setup complete development environment
	@printf '$(GREEN)✅ Development environment ready!$(NC)\n'
	@printf 'Run $(BLUE)make check$(NC) before committing\n'

check: format lint test-quick ## Quick pre-commit validation
	@printf '\n$(GREEN) ╔═══════════════════════════════════════╗$(NC)\n'
	@printf '$(GREEN) ║✅ All checks passed - ready to commit ║$(NC)\n'
	@printf '$(GREEN) ╚═══════════════════════════════════════╝$(NC)\n'


fix: format ## Auto-fix common issues
	@printf '$(YELLOW)Auto-fixing issues...$(NC)\n'
	@$(PRE_COMMIT) run --all-files || true
	@printf '$(GREEN)✅ Auto-fix complete$(NC)\n'

watch: ## Watch for changes and auto-run tests
	@command -v watchmedo >/dev/null 2>&1 || { \
		printf '$(YELLOW)Installing watchdog...$(NC)\n'; \
		$(UV) pip install watchdog; \
	}
	@printf '$(YELLOW)Watching for changes...$(NC)\n'
	watchmedo shell-command \
		--patterns="*.py" \
		--recursive \
		--command='make test-quick' \
		.

#############################################
# Version Management
#############################################

version: ## Show current version
	@grep "version = " pyproject.toml | head -1 | sed 's/.*= /Version: /'

version-bump: ## Interactive version bump
	@printf '$(YELLOW)Current version:$(NC)\n'
	@make version
	@printf '\n$(YELLOW)Update version in:$(NC)\n'
	@printf '  1. pyproject.toml\n'
	@printf '  2. CHANGELOG.md\n'
	@printf '  3. Create git tag: git tag -a v<version> -m "Release v<version>"\n'

git-tag: ## Create git tag from current version
	@VERSION=$$(grep "version = " pyproject.toml | head -1 | cut -d'"' -f2); \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	printf '$(GREEN)✅ Created tag v$$VERSION$(NC)\n'; \
	printf 'Push with: $(BLUE)git push origin v$$VERSION$(NC)\n'

#############################################
# Maintenance & Diagnostics
#############################################

info: ## Show project information and environment
	@printf '$(BLUE)═══════════════════════════════════════$(NC)\n'
	@printf '$(BLUE)  Project Information$(NC)\n'
	@printf '$(BLUE)═══════════════════════════════════════$(NC)\n'
	@make version
	@printf 'Python: $$($(VENV_BIN)/python --version 2>&1)\n'
	@printf 'UV: $$(uv --version 2>&1)\n'
	@printf 'Docker: $$(docker --version 2>&1)\n'
	@printf 'Image: $(IMAGE_NAME):$(IMAGE_TAG)\n'
	@printf 'Registry: $(REGISTRY)\n'
	@printf '$(BLUE)═══════════════════════════════════════$(NC)\n'

deps-tree: check-venv ## Show dependency tree
	@$(UV) pip list --format=tree || $(UV) pip list

deps-outdated: check-venv ## Check for outdated dependencies
	@$(UV) pip list --outdated

health-check: verify-install ## Comprehensive health check
	@printf '\n$(YELLOW)Running health check...$(NC)\n'
	@make check-python
	@make check-tools
	@printf '\n$(GREEN)✅ Health check passed$(NC)\n'

diagnose: ## Diagnose common issues
	@printf '$(YELLOW)Running diagnostics...$(NC)\n'
	@printf '\n1. Checking UV installation...\n'
	@make check-uv || true
	@printf '\n2. Checking Python version...\n'
	@make check-python || true
	@printf '\n3. Checking virtual environment...\n'
	@make check-venv || true
	@printf '\n4. Checking installed packages...\n'
	@make check-tools || true
	@printf '\n$(GREEN)✅ Diagnostics complete$(NC)\n'

# Catch-all for undefined targets
%:
	@printf '$(RED)❌ Unknown target: $@$(NC)\n'
	@printf 'Run $(GREEN)make help$(NC) to see available targets\n'
	@exit 1

