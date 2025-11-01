# Architecture Overview

## High level
- runner.py orchestrates scraping across sites with a thread pool.
- Browsers are managed by core/browser.BrowserManager with optional pooling.
- Each site is represented by config.models.SiteConfig loaded via config.loader.
- Scraping logic lives in core/scraper.SiteScraper, using core/waits and Selenium.
- Errors are structured (core/exceptions) and can attach artifacts (core/capture).
- Observability via core/metrics + infra/server for health endpoints.

## Error handling & resilience
- Circuit breakers per-site (core/circuit_breaker) to back off failing targets.
- Structured error payloads with contextual fields and optional artifacts.

## Logging
- infra/logging_config sets JSON or human-readable logs.
- Signals and graceful shutdown via infra/signals.
