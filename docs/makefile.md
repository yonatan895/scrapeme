# Makefile Commands

This project uses a `Makefile` to automate common tasks. This document provides an overview of the available commands.

## General Commands

*   `make help`: Displays a list of all available commands and their descriptions.

## Environment Setup

*   `make check-uv`: Checks if `uv` is installed.
*   `make venv`: Creates a virtual environment using `uv`.
*   `make install`: Installs only the production dependencies.
*   `make install-dev`: Installs the development dependencies.
*   `make install-all`: Installs all optional dependencies.
*   `make sync`: Synchronizes the environment to match the `pyproject.toml` file exactly.
*   `make compile-requirements`: Generates `requirements.txt`, `requirements-dev.txt`, and `requirements-all.txt` from `pyproject.toml`.

## Testing

*   `make test`: Runs all tests with coverage.
*   `make test-unit`: Runs only the unit tests.
*   `make test-integration`: Runs the integration tests.
*   `make test-e2e`: Runs the end-to-end tests.
*   `make test-property`: Runs the property-based tests.
*   `make test-load`: Runs the load tests.
*   `make test-chaos`: Runs the chaos engineering tests.
*   `make test-all`: Runs all test suites.
*   `make test-watch`: Runs tests in watch mode, which automatically re-runs tests on file changes.
*   `make test-parallel`: Runs tests in parallel.

## Code Quality

*   `make lint`: Runs all linters (Black, isort, pylint, mypy).
*   `make format`: Formats the code using Black and isort.
*   `make type-check`: Runs type checking with mypy and generates an HTML report.
*   `make security-check`: Runs security checks using Bandit and Safety.

## Performance

*   `make benchmark`: Runs performance benchmarks.
*   `make profile`: Profiles the application's performance using cProfile.

## Docker

*   `make docker-build`: Builds the production Docker image.
*   `make docker-build-dev`: Builds the development Docker image.
*   `make docker-build-test`: Builds the test Docker image.
*   `make docker-test`: Runs tests in a Docker container.
*   `make docker-scan`: Scans the Docker image for vulnerabilities.
*   `make docker-push`: Pushes the Docker image to the container registry.
*   `make docker-run`: Runs the Docker container with an example configuration.
*   `make docker-shell`: Opens a shell in the Docker container.

## Docker Compose

*   `make compose-up`: Starts the Docker Compose stack, which includes the Selenium Grid and monitoring services.
*   `make compose-down`: Stops the Docker Compose stack.
*   `make compose-logs`: Views the logs of the Docker Compose stack.
*   `make compose-restart`: Restarts the Docker Compose stack.
*   `make compose-ps`: Shows the running containers in the Docker Compose stack.

## Kubernetes

*   `make k8s-deploy`: Deploys the application to Kubernetes.
*   `make k8s-delete`: Deletes the application from Kubernetes.
*   `make k8s-logs`: Views the logs of the Kubernetes deployment.
*   `make k8s-status`: Checks the status of the Kubernetes deployment.
*   `make k8s-describe`: Describes the Kubernetes deployment.
*   `make k8s-shell`: Opens a shell in a Kubernetes pod.
*   `make k8s-port-forward`: Port-forwards the metrics endpoint.

## Documentation

*   `make docs`: Builds the documentation.
*   `make serve-docs`: Serves the documentation locally.

## Cleanup

*   `make clean`: Cleans up generated files.
*   `make clean-all`: Cleans up everything, including the virtual environment.

## CI/CD

*   `make ci-local`: Runs the CI checks locally.
*   `make pre-commit-install`: Installs the pre-commit hooks.
*   `make pre-commit-run`: Runs the pre-commit hooks on all files.

## Quick Start

*   `make quickstart`: Sets up the complete environment for new developers.

## Development Workflow

*   `make dev`: Sets up the complete development environment.
*   `make check`: Runs a quick check before committing.

## Version Management

*   `make version`: Shows the current version of the project.
*   `make bump-patch`: Bumps the patch version (e.g., 0.0.X).
*   `make bump-minor`: Bumps the minor version (e.g., 0.X.0).
*   `make bump-major`: Bumps the major version (e.g., X.0.0).
