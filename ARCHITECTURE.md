# Architecture

This document provides a high-level overview of the `scrapeme` application's architecture.

## Core Components

The application is built around a few core components that work together to provide a robust and observable scraping solution.

### 1. Configuration

The application's behavior is driven by a central YAML configuration file, `config/sites.yaml`. This file defines the sites to be scraped, the steps to be executed for each site, and the data to be extracted.

The configuration is loaded and validated at startup by the `config.loader` module. The configuration models are defined in `config.models`, providing type safety and immutability.

### 2. Browser Management

The `core.browser` module is responsible for managing WebDriver instances. It supports both Chrome and Firefox and can be configured to run in headless mode.

For improved performance and resource utilization, the `BrowserManager` can use a `WebDriverPool` to reuse WebDriver sessions across multiple scraping tasks.

### 3. Authentication

The `core.auth` module provides a generic `AuthFlow` class for handling form-based authentication. It uses the credentials defined in the site configuration and retrieves the actual secrets from a `SecretProvider`.

The authentication process is resilient, with built-in retries for transient failures. On failure, it captures artifacts (screenshots and HTML) for easier debugging.

### 4. Scraping

The main scraping logic is encapsulated in the `core.scraper.SiteScraper` class. This class iterates through the steps defined in the site configuration and executes them in order.

The `SiteScraper` is designed for both batch and streaming use cases. The `run()` method executes all steps and returns the results as a dictionary, while the `stream()` method yields the results for each step as they are completed, allowing for memory-efficient processing of large amounts of data.

### 5. Observability

The application is designed with observability in mind, providing detailed metrics and structured logs.

#### Metrics

The `core.metrics` module defines a set of Prometheus metrics that provide insights into the application's performance and behavior. These metrics include:

*   Scrape duration
*   Step duration
*   Page load times
*   Number of retries
*   Circuit breaker state changes
*   Active WebDriver sessions

The metrics are exposed via a Prometheus endpoint, which can be scraped by a Prometheus server.

#### Logging

The application uses `structlog` for structured logging. The `infra.logging_config` module configures the logger to output JSON-formatted logs, which can be easily ingested and analyzed by a log management system.

### 6. Resilience

The application is designed to be resilient to failures. It uses several patterns to handle transient and permanent errors.

#### Retries

The `core.retry` module provides a declarative retry mechanism with exponential backoff and jitter. This is used throughout the application to handle transient failures, such as network errors or temporary unavailability of elements on the page.

#### Circuit Breaker

The `core.circuit_breaker` module implements a circuit breaker pattern to prevent the application from repeatedly trying to scrape a site that is down or returning errors. When the circuit is open, the application will not attempt to scrape the site for a configurable amount of time.

#### Rate Limiting

The `core.rate_limiter` module provides a token bucket rate limiter to avoid overwhelming the target sites with too many requests.

### 7. Secret Management

The `core.secrets` module provides an abstraction for secret management. It supports multiple backends, including environment variables, files, and HashiCorp Vault. This allows for secure storage and retrieval of sensitive information, such as login credentials.

## Deployment

The application is designed to be deployed in a containerized environment using Docker and Kubernetes. The repository includes a `Dockerfile` for building the application image, a `docker-compose.production.yaml` file for running the application in a production-like environment, and a `k8s` directory with Kubernetes manifests for deploying the application to a Kubernetes cluster.

## Monitoring

The `monitoring` directory contains configurations for Prometheus and Grafana. The Prometheus configuration scrapes the application's metrics endpoint, and the Grafana dashboard provides a visual representation of the metrics.
