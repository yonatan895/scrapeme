"""Site scraping with streaming results and enhanced metrics."""

from __future__ import annotations

import time
from logging import Logger
from pathlib import Path
from typing import Any, Iterator

from selenium.webdriver.common.by import By

from config.models import FieldConfig, SiteConfig, StepBlock
from core.capture import ArtifactCapture
from core.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
from core.exceptions import ErrorContext, ExtractionError
from core.frames import FramesNavigator
from core.metrics import Metrics
from core.rate_limiter import RateLimiter, TokenBucket
from core.retry import selenium_retry
from core.url import is_absolute_url, make_absolute_url, normalize_url
from core.waits import Waiter

__all__ = ["SiteScraper"]


class SiteScraper:
    """Site scraper with streaming results and rate limiting."""

    __slots__ = (
        "_config",
        "_waiter",
        "_log",
        "_frames",
        "_capture",
        "_rate_limiter",
        "_circuit_breaker",
    )

    def __init__(
        self,
        config: SiteConfig,
        waiter: Waiter,
        logger: Logger,
        *,
        artifact_dir: Path | None = None,
    ) -> None:
        self._config = config
        self._waiter = waiter
        self._log = logger
        self._frames = FramesNavigator(waiter.driver, timeout=waiter.timeout)

        if artifact_dir:
            capture_dir = artifact_dir / "scrape"
            self._capture = ArtifactCapture(waiter.driver, capture_dir, logger, enabled=True)
        else:
            self._capture = ArtifactCapture(waiter.driver, Path(), logger, enabled=False)

        self._circuit_breaker: CircuitBreaker = CircuitBreakerRegistry.get(self._config.name)
        self._rate_limiter: TokenBucket = RateLimiter.get(
            self._config.name, requests_per_second=2.0
        )

    @selenium_retry
    def _safe_click(self, xpath: str) -> None:
        """Click with retry and metrics."""
        self._waiter.clickable((By.XPATH, xpath)).click()

    @selenium_retry
    def _extract_field(self, field: FieldConfig) -> str:
        """Extract field with retry and metrics."""
        element = self._waiter.visible((By.XPATH, field.xpath))

        if field.attribute:
            value = element.get_attribute(field.attribute)
        else:
            value = element.text

        Metrics.fields_extracted_total.labels(
            site=self._config.name,
            step="current",
            field=field.name,
        ).inc()

        return "" if value is None else str(value)

    def _resolve_url(self, url: str) -> str:
        """Resolve URL to absolute and normalize."""
        if is_absolute_url(url):
            return normalize_url(url)

        absolute_url = make_absolute_url(url, self._config.base_url)
        return normalize_url(absolute_url)

    def _exec_step(self, step: StepBlock) -> dict[str, Any]:
        """Execute single step with metrics."""
        start_time = time.monotonic()
        success = False

        try:
            if not self._rate_limiter.wait_for_tokens(tokens=1, timeout=30.0):
                raise ExtractionError(
                    f"Rate limit timeout for step '{step.name}'",
                    context=ErrorContext(site_name=self._config.name, step_name=step.name),
                )

            if step.goto_url:
                url = self._resolve_url(step.goto_url)
                self._log.info(f"GOTO {url!r}")

                nav_start = time.monotonic()
                self._waiter.driver.get(url)
                nav_duration = time.monotonic() - nav_start

                Metrics.page_load_duration_seconds.labels(site=self._config.name).observe(
                    nav_duration
                )

            with self._frames.context(step.frames, exit_to=step.frame_exit):
                if step.execute_js:
                    self._log.info("Executing JS")
                    self._waiter.driver.execute_script(step.execute_js)

                if step.click_xpath:
                    self._log.info("Clicking element")
                    self._safe_click(step.click_xpath)

                if step.wait_xpath:
                    self._log.info("Waiting for element")
                    self._waiter.visible((By.XPATH, step.wait_xpath))

                if step.wait_url_contains:
                    self._log.info("Waiting for URL")
                    self._waiter.url_contains(step.wait_url_contains)

                data: dict[str, Any] = {}
                for field in step.fields:
                    try:
                        data[field.name] = self._extract_field(field)
                    except Exception as e:
                        if self._capture.enabled:
                            self._capture.capture(f"{self._config.name}_{step.name}_{field.name}")

                        raise ExtractionError(
                            f"Field '{field.name}' extraction failed",
                            context=ErrorContext(
                                site_name=self._config.name,
                                step_name=step.name,
                                field_name=field.name,
                                xpath=field.xpath,
                            ),
                        ) from e

                success = True
                return data

        finally:
            duration = time.monotonic() - start_time
            Metrics.record_step_execution(
                self._config.name,
                step.name,
                duration,
                success,
            )

    def run(self) -> dict[str, dict[str, Any]]:
        """Execute all steps and return results."""
        self._log.info("Begin site scrape")

        with self._capture.on_failure(f"{self._config.name}_base"):
            if self._config.base_url:
                base_url = normalize_url(self._config.base_url)
                self._waiter.driver.get(base_url)

        results: dict[str, dict[str, Any]] = {}
        for step in self._config.steps:
            with self._capture.on_failure(f"{self._config.name}_{step.name}"):
                results[step.name] = self._exec_step(step)

        return results

    def stream(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Stream results step-by-step for memory efficiency."""
        self._log.info("Begin streaming scrape")

        with self._capture.on_failure(f"{self._config.name}_base"):
            if self._config.base_url:
                base_url = normalize_url(self._config.base_url)
                self._waiter.driver.get(base_url)

        for step in self._config.steps:
            with self._capture.on_failure(f"{self._config.name}_{step.name}"):
                data = self._exec_step(step)
                yield (step.name, data)
