.PHONY: help install install-dev test test-unit test-integration test-e2e test-all \
        lint format type-check security-check benchmark clean docker-build docker-test \
        docker-push docs serve-docs

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
DOCKER := docker
IMAGE_NAME := selenium-automation
IMAGE_TAG := latest

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt -r requirements-dev.txt
	pre-commit install

test: ## Run all tests with coverage
	$(PYTEST) -v --cov=core --cov=config --cov=infra --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests
	$(PYTEST) tests/integration/ -v

test-e2e: ## Run end-to-end tests
	$(PYTEST) tests/e2e/ -v -m e2e

test-property: ## Run property-based tests
	$(PYTEST) tests/property/ -v -m property

test-load: ## Run load tests
	$(PYTEST) tests/load/ -v -m load

test-chaos: ## Run chaos engineering tests
	$(PYTEST) tests/chaos/ -v -m chaos

test-all: test test-property test-load ## Run all test suites

lint: ## Run all linters
	black --check --diff core/ config/ infra/ tests/ runner.py
	isort --check-only --diff core/ config/ infra/ tests/ runner.py
	pylint core/ config/ infra/ runner.py
	mypy core/ config/ infra/ runner.py --strict

format: ## Format code with black and isort
	black core/ config/ infra/ tests/ runner.py
	isort core/ config/ infra/ tests/ runner.py

type-check: ## Run type checking with mypy
	mypy core/ config/ infra/ runner.py --strict --html-report mypy-report

security-check: ## Run security checks
	bandit -r core/ config/ infra/ runner.py -f json -o bandit-report.json
	safety check --json

benchmark: ## Run performance benchmarks
	$(PYTEST) tests/benchmarks/ --benchmark-only --benchmark-json=benchmark.json

clean: ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf htmlcov/ .coverage coverage.xml mypy-report/
	rm -rf artifacts/ results/ test-results/
	rm -rf dist/ build/ *.egg-info/
	rm -f bandit-report.json safety-report.json benchmark.json

docker-build: ## Build Docker image
	$(DOCKER) build -t $(IMAGE_NAME):$(IMAGE_TAG) --target production .

docker-build-dev: ## Build development Docker image
	$(DOCKER) build -t $(IMAGE_NAME):dev --target development .

docker-test: ## Run tests in Docker
	$(DOCKER) build -t $(IMAGE_NAME):test --target test .

docker-push: ## Push Docker image to registry
	$(DOCKER) tag $(IMAGE_NAME):$(IMAGE_TAG) ghcr.io/yourorg/$(IMAGE_NAME):$(IMAGE_TAG)
	$(DOCKER) push ghcr.io/yourorg/$(IMAGE_NAME):$(IMAGE_TAG)

docker-run: ## Run Docker container with example config
	$(DOCKER) run --rm \
		-v $(PWD)/sites.yaml:/app/sites.yaml:ro \
		-v $(PWD)/artifacts:/app/artifacts \
		$(IMAGE_NAME):$(IMAGE_TAG)

docs: ## Build documentation
	cd docs && make html

serve-docs: docs ## Serve documentation locally
	cd docs/_build/html && $(PYTHON) -m http.server 8000

compose-up: ## Start docker-compose stack
	docker-compose -f docker-compose.production.yml up -d

compose-down: ## Stop docker-compose stack
	docker-compose -f docker-compose.production.yml down

compose-logs: ## View docker-compose logs
	docker-compose -f docker-compose.production.yml logs -f

k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f k8s/

k8s-delete: ## Delete from Kubernetes
	kubectl delete -f k8s/

k8s-logs: ## View Kubernetes logs
	kubectl logs -f deployment/selenium-automation -n selenium-automation

ci-local: lint test security-check ## Run CI checks locally
	@echo "✅ All CI checks passed!"
