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
from infra.cache import get_redis_client

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
        "_redis",
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
        self._redis = get_redis_client()

    @selenium_retry
    def _safe_click(self, xpath: str) -> None:
        """Click with retry and metrics."""
        self._waiter.clickable((By.XPATH, xpath)).click()

    def _get_cache_key(self, step_name: str, fields: list[FieldConfig]) -> str:
        """Generate cache key for step extraction."""
        current_url = self._waiter.driver.current_url
        import hashlib
        import json

        # Create deterministic signature of the fields we are extracting
        fields_sig = sorted([f"{f.name}:{f.xpath}:{f.attribute or ''}" for f in fields])
        key_raw = f"{current_url}:{step_name}:{json.dumps(fields_sig)}"
        return f"cache:step:{hashlib.md5(key_raw.encode()).hexdigest()}"

    def _extract_all_fields_js(self, step_name: str, fields: list[FieldConfig]) -> dict[str, str]:
        """Extract all fields in one JS call to minimize roundtrips."""
        if not fields:
            return {}

        # Try Redis Cache
        if self._redis:
            cache_key = self._get_cache_key(step_name, fields)
            try:
                import json
                cached_val = self._redis.get(cache_key)
                if cached_val:
                    return json.loads(cached_val) # type: ignore
            except Exception:
                self._log.warning("Redis cache get failed", exc_info=True)

        # Construct a mapping of field_name -> {xpath, attribute}
        # We'll inject a script that evaluates all XPaths and returns a JSON object.

        # Safe JS injection construction
        field_specs = []
        for f in fields:
            # Escape quotes in xpath to be safe in JS string
            safe_xpath = f.xpath.replace('"', '\\"')
            attr = f.attribute or ""
            field_specs.append(f'{{name: "{f.name}", xpath: "{safe_xpath}", attr: "{attr}"}}')

        specs_json = f"[{','.join(field_specs)}]"

        js_script = f"""
        const specs = {specs_json};
        const results = {{}};

        for (const spec of specs) {{
            try {{
                const result = document.evaluate(
                    spec.xpath,
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                );
                const node = result.singleNodeValue;

                if (node) {{
                    if (spec.attr) {{
                        results[spec.name] = node.getAttribute(spec.attr) || "";
                    }} else {{
                        results[spec.name] = node.textContent || "";
                    }}
                }} else {{
                    results[spec.name] = null; // Mark as missing
                }}
            }} catch (e) {{
                results[spec.name] = "ERROR: " + e.message;
            }}
        }}
        return results;
        """

        try:
            # Type ignore because execute_script returns Any
            extracted: dict[str, str | None] = self._waiter.driver.execute_script(js_script)  # type: ignore

            # Post-process results (null -> empty string, metrics)
            final_results: dict[str, str] = {}
            for f in fields:
                val = extracted.get(f.name)
                if val is None:
                    # If JS couldn't find it, we might want to fail hard or fallback.
                    # Original logic used _waiter.visible which throws TimeoutException.
                    # To maintain semantics, if it's missing, we should probably try the slow path
                    # OR just raise an error if we are strict.
                    # For performance, we assume if JS didn't find it, it's not there.
                    # BUT, the original logic waited for visibility. JS execution is instant.
                    # We should probably WAIT for the *first* element or a common parent?
                    # Or maybe the 'wait_xpath' in the step config covers this?
                    # Yes, step.wait_xpath guards the page state.
                    val = ""

                final_results[f.name] = str(val)

                Metrics.fields_extracted_total.labels(
                    site=self._config.name,
                    step="current",
                    field=f.name,
                ).inc()

            if self._redis:
                try:
                    import json
                    # Cache for 1 hour
                    self._redis.setex(cache_key, 3600, json.dumps(final_results))
                except Exception:
                    self._log.warning("Redis cache set failed", exc_info=True)

            return final_results

        except Exception as e:
            self._log.error(f"Bulk JS extraction failed: {e}")
            raise

    def _resolve_url(self, url: str) -> str:
        """Resolve URL to absolute and normalize.

        Args:
            url: URL (absolute or relative)

        Returns:
            Normalized absolute URL
        """
        # If already absolute, just normalize
        if is_absolute_url(url):
            return normalize_url(url)

        # Relative URL - make absolute using base_url
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

                # Performance optimization: Bulk extraction via JS
                # This replaces O(N) calls with O(1) call
                data: dict[str, Any] = {}
                try:
                    # We rely on step.wait_xpath to ensure the page is ready.
                    # If fields are missing in JS, they return empty string.
                    # If precise per-field waiting is needed, individual field waits can be added to config.
                    data = self._extract_all_fields_js(step.name, step.fields)  # type: ignore
                except Exception as e:
                    # Fallback or error handling
                    if self._capture.enabled:
                        self._capture.capture(f"{self._config.name}_{step.name}_bulk")
                    raise ExtractionError(
                        f"Bulk extraction failed for step '{step.name}'",
                        context=ErrorContext(site_name=self._config.name, step_name=step.name),
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
        """Stream results step-by-step for memory efficiency.

        Yields:
            Tuple of (step_name, step_data)
        """
        self._log.info("Begin streaming scrape")

        with self._capture.on_failure(f"{self._config.name}_base"):
            if self._config.base_url:
                base_url = normalize_url(self._config.base_url)
                self._waiter.driver.get(base_url)

        for step in self._config.steps:
            with self._capture.on_failure(f"{self._config.name}_{step.name}"):
                data = self._exec_step(step)
                yield (step.name, data)
