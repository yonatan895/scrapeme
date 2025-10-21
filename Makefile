.PHONY: help venv install install-dev install-all sync compile-requirements \
        test test-unit test-integration test-e2e test-property test-load test-chaos test-all \
        lint format type-check security-check benchmark clean \
        docker-build docker-build-dev docker-test docker-push docker-run \
        docs serve-docs compose-up compose-down compose-logs \
        k8s-deploy k8s-delete k8s-logs ci-local

# Variables
PYTHON := python
UV := uv
PYTEST := pytest
DOCKER := docker
DOCKER_COMPOSE := docker-compose
IMAGE_NAME := scrapeme
IMAGE_TAG := latest
REGISTRY := ghcr.io/yonatan895

# Color output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# === Environment Setup ===

check-uv: ## Check if UV is installed
	@command -v $(UV) >/dev/null 2>&1 || {  \
		echo "$(RED)❌ UV is not installed!$(NC)"; \
		echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "Or on Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""; \
		exit 1; \
	}
	@echo "$(GREEN)✅ UV is installed$(NC)"

venv: check-uv ## Create virtual environment with UV
	$(UV) venv
	@echo "$(GREEN)✅ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with:$(NC)"
	@echo "  Windows: .venv\\Scripts\\activate"
	@echo "  Linux/Mac: source .venv/bin/activate"

install: check-uv ## Install production dependencies only
	$(UV) pip install -e .
	@echo "$(GREEN)✅ Production dependencies installed$(NC)"

install-dev: check-uv ## Install with development dependencies
	$(UV) pip install -e ".[dev,lint]"
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

install-all: check-uv ## Install all optional dependencies
	$(UV) pip install -e ".[all]"
	pre-commit install || true
	@echo "$(GREEN)✅ All dependencies installed$(NC)"

sync: check-uv ## Sync environment to match pyproject.toml exactly
	$(UV) pip sync
	@echo "$(GREEN)✅ Environment synchronized$(NC)"

compile-requirements: check-uv ## Generate requirements.txt from pyproject.toml
	$(UV) pip compile pyproject.toml -o requirements.txt
	$(UV) pip compile pyproject.toml --extra dev --extra lint -o requirements-dev.txt
	$(UV) pip compile pyproject.toml --all-extras -o requirements-all.txt
	@echo "$(GREEN)✅ Requirements files generated$(NC)"

# === Testing ===

test: ## Run all tests with coverage
	$(PYTEST) -v \
		--cov=core \
		--cov=config \
		--cov=infra

test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/ -v -m unit

test-integration: ## Run integration tests
	$(PYTEST) tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests (requires Chrome)
	$(PYTEST) tests/e2e/ -v -m e2e --timeout=300

test-property: ## Run property-based tests
	$(PYTEST) tests/property/ -v -m property

test-load: ## Run load tests
	$(PYTEST) tests/load/ -v -m load

test-chaos: ## Run chaos engineering tests
	$(PYTEST) tests/chaos/ -v -m chaos

test-all: test test-unit test-integration test-e2e test-property test-load test-chaos ## Run all test suites
	@echo "$(GREEN)✅ All test suites passed$(NC)"

test-watch: ## Run tests in watch mode (auto-rerun on changes)
	pytest-watch -c -v

test-parallel: ## Run tests in parallel
	$(PYTEST) -v -n auto

# === Code Quality ===

lint: ## Run all linters
	@echo "$(YELLOW)Running Black...$(NC)"
	black --check --diff core/ config/ infra/ tests/ runner.py
	@echo "$(YELLOW)Running isort...$(NC)"
	isort --check-only --diff core/ config/ infra/ tests/ runner.py
	@echo "$(YELLOW)Running pylint...$(NC)"
	pylint core/ config/ infra/ runner.py
	@echo "$(YELLOW)Running mypy...$(NC)"
	mypy core/ config/ infra/ runner.py --strict
	@echo "$(GREEN)✅ All linters passed$(NC)"

format: ## Format code with black and isort
	black core/ config/ infra/ tests/ runner.py
	isort core/ config/ infra/ tests/ runner.py
	@echo "$(GREEN)✅ Code formatted$(NC)"

type-check: ## Run type checking with mypy
	mypy core/ config/ infra/ runner.py --strict --html-report mypy-report
	@echo "$(GREEN)✅ Type checking complete$(NC)"
	@echo "HTML report: mypy-report/index.html"

security-check: ## Run security checks
	@echo "$(YELLOW)Running Bandit...$(NC)"
	bandit -r core/ config/ infra/ runner.py -f json -o bandit-report.json
	@echo "$(YELLOW)Running Safety...$(NC)"
	safety check --json || true
	@echo "$(GREEN)✅ Security checks complete$(NC)"

# === Performance ===

benchmark: ## Run performance benchmarks
	$(PYTEST) tests/benchmarks/ --benchmark-only --benchmark-json=benchmark.json
	@echo "$(GREEN)✅ Benchmarks complete$(NC)"

profile: ## Profile application performance
	$(PYTHON) -m cProfile -o profile.stats runner.py --config sites.yaml
	@echo "Analyze with: python -c \"import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)\""

# === Docker ===

docker-build: ## Build production Docker image
	$(DOCKER) build -t $(IMAGE_NAME):$(IMAGE_TAG) --target production --no-cache .
	@echo "$(GREEN)✅ Production image built: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"

docker-build-dev: ## Build development Docker image
	$(DOCKER) build -t $(IMAGE_NAME):dev --target development .
	@echo "$(GREEN)✅ Development image built: $(IMAGE_NAME):dev$(NC)"

docker-build-test: ## Build test Docker image
	$(DOCKER) build -t $(IMAGE_NAME):test --target test .
	@echo "$(GREEN)✅ Test image built: $(IMAGE_NAME):test$(NC)"

docker-test: docker-build-test ## Run tests in Docker
	$(DOCKER) run --rm $(IMAGE_NAME):test pytest -v \
		--cov=core \
		--cov=config \
		--cov=infra \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml
	@echo "$(GREEN)✅ Tests passed in Docker$(NC)"

docker-scan: docker-build ## Scan Docker image for vulnerabilities
	docker scan $(IMAGE_NAME):$(IMAGE_TAG) || true
	@echo "$(YELLOW)Consider using: trivy image $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"

docker-push: docker-build ## Push Docker image to registry
	$(DOCKER) tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	$(DOCKER) push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)✅ Image pushed to $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)$(NC)"

docker-run: ## Run Docker container with example config
	$(DOCKER) run --rm \
		-v $(PWD)/config/sites.yaml:/app/sites.yaml:ro \
		-e SITE_USERNAME=${SITE_USERNAME} \
		-e SITE_PASSWORD=${SITE_PASSWORD} \
		$(IMAGE_NAME):$(IMAGE_TAG)

docker-shell: ## Open shell in Docker container
	$(DOCKER) run --rm -it \
		-v $(PWD):/app \
		$(IMAGE_NAME):dev \
		/bin/bash

# === Docker Compose ===

compose-up: ## Start docker-compose stack (includes Selenium Grid + Monitoring)
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml up -d
	@echo "$(GREEN)✅ Docker Compose stack started$(NC)"
	@echo "Services available at:"
	@echo "  - Selenium Hub: http://localhost:4444"
	@echo "  - Prometheus: http://localhost:9091"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Alertmanager: http://localhost:9093"

compose-down: ## Stop docker-compose stack
	$(DOCKER_COMPOSE) -f docker-compose.production.yml down
	@echo "$(GREEN)✅ Docker Compose stack stopped$(NC)"

compose-logs: ## View docker-compose logs
	$(DOCKER_COMPOSE) -f docker-compose.production.yaml logs -f

compose-restart: compose-down compose-up ## Restart docker-compose stack

compose-ps: ## Show running containers
	$(DOCKER_COMPOSE) -f docker-compose.production.yml ps

# === Kubernetes ===

k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/pvc.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/servicemonitor.yaml
	kubectl apply -f k8s/hpa.yaml
	@echo "$(GREEN)✅ Deployed to Kubernetes$(NC)"
	@echo "Check status: kubectl get pods -n selenium-automation"

k8s-delete: ## Delete from Kubernetes
	kubectl delete -f k8s/
	@echo "$(GREEN)✅ Deleted from Kubernetes$(NC)"

k8s-logs: ## View Kubernetes logs
	kubectl logs -f deployment/selenium-automation -n selenium-automation

k8s-status: ## Check Kubernetes deployment status
	kubectl get all -n selenium-automation
	kubectl get pvc -n selenium-automation

k8s-describe: ## Describe Kubernetes deployment
	kubectl describe deployment selenium-automation -n selenium-automation

k8s-shell: ## Open shell in Kubernetes pod
	kubectl exec -it deployment/selenium-automation -n selenium-automation -- /bin/bash

k8s-port-forward: ## Port forward metrics endpoint
	kubectl port-forward svc/selenium-automation 9090:9090 -n selenium-automation

# === Documentation ===

docs: ## Build documentation
	cd docs && make html
	@echo "$(GREEN)✅ Documentation built$(NC)"
	@echo "Open: docs/_build/html/index.html"

serve-docs: docs ## Serve documentation locally
	@echo "$(YELLOW)Serving documentation at http://localhost:8000$(NC)"
	cd docs/_build/html && $(PYTHON) -m http.server 8000

# === Cleanup ===

clean: ## Clean generated files
	@echo "$(YELLOW)Cleaning generated files...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf htmlcov/ .coverage coverage.xml mypy-report/
	rm -rf artifacts/ results/ test-results/
	rm -rf dist/ build/ *.egg-info/
	rm -f bandit-report.json safety-report.json benchmark.json
	rm -f profile.stats
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including venv
	rm -rf .venv
	@echo "$(GREEN)✅ Full cleanup complete$(NC)"

# === CI/CD ===

ci-local: lint test security-check ## Run CI checks locally
	@echo "$(GREEN)✅ All CI checks passed!$(NC)"

pre-commit-install: ## Install pre-commit hooks
	pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed$(NC)"

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

# === Quick Start ===

quickstart: venv install-all ## Complete setup for new developers
	@echo "$(GREEN)✅ Quickstart complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Activate venv:"
	@echo "     Windows: .venv\\Scripts\\activate"
	@echo "     Linux/Mac: source .venv/bin/activate"
	@echo "  2. Create sites.yaml configuration"
	@echo "  3. Set environment variables (copy .env.example to .env)"
	@echo "  4. Run: python runner.py --config sites.yaml --headless"
	@echo "  5. Run tests: make test"

# === Development Workflow ===

dev: install-all pre-commit-install ## Setup complete development environment
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

check: lint test ## Quick check before commit
	@echo "$(GREEN)✅ All checks passed - ready to commit!$(NC)"

# === Version Management ===

version: ## Show current version
	@grep "version = " pyproject.toml | head -1

bump-patch: ## Bump patch version (0.0.X)
	@echo "Bump patch version manually in pyproject.toml"

bump-minor: ## Bump minor version (0.X.0)
	@echo "Bump minor version manually in pyproject.toml"

bump-major: ## Bump major version (X.0.0)
	@echo "Bump major version manually in pyproject.toml"
