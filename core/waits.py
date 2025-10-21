"""Explicit wait primitives with enhanced error context."""

from __future__ import annotations

from typing import TYPE_CHECKING

from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.exceptions import ElementNotFoundError, TimeoutError
from core.metrics import Metrics

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement

__all__ = ["Waiter"]


class Waiter:
    """Encapsulates explicit waits with enhanced error reporting."""

    __slots__ = ("_driver", "_timeout", "_wait_instance")

    def __init__(self, driver: WebDriver, timeout_sec: int = 20) -> None:
        if timeout_sec < 1:
            raise ValueError("timeout_sec must be positive")
        self._driver = driver
        self._timeout = timeout_sec
        self._wait_instance = WebDriverWait(self._driver, self._timeout)

    @property
    def driver(self) -> WebDriver:
        """Access to underlying WebDriver."""
        return self._driver

    @property
    def timeout(self) -> int:
        """Configured timeout in seconds."""
        return self._timeout

    def presence(self, locator: tuple[str, str]) -> WebElement:
        """Wait for element presence in DOM with metrics."""
        import time

        start = time.monotonic()

        try:
            element = self._wait_instance.until(EC.presence_of_element_located(locator))
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="presence").observe(duration)
            return element
        except SeleniumTimeoutException as e:
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="presence").observe(duration)
            url = self._driver.current_url
            raise ElementNotFoundError(f"Element not present: {locator[1]} (URL: {url})") from e

    def visible(self, locator: tuple[str, str]) -> WebElement:
        """Wait for element visibility with metrics."""
        import time

        start = time.monotonic()

        try:
            element = self._wait_instance.until(EC.visibility_of_element_located(locator))
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="visibility").observe(duration)
            return element
        except SeleniumTimeoutException as e:
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="visibility").observe(duration)
            url = self._driver.current_url
            raise ElementNotFoundError(f"Element not visible: {locator[1]} (URL: {url})") from e

    def clickable(self, locator: tuple[str, str]) -> WebElement:
        """Wait for element to be clickable with metrics."""
        import time

        start = time.monotonic()

        try:
            element = self._wait_instance.until(EC.element_to_be_clickable(locator))
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="clickable").observe(duration)
            return element
        except SeleniumTimeoutException as e:
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="clickable").observe(duration)
            url = self._driver.current_url
            raise ElementNotFoundError(f"Element not clickable: {locator[1]} (URL: {url})") from e

    def url_contains(self, substring: str) -> bool:
        """Wait for URL to contain substring with metrics."""

        import time

        start = time.monotonic()

        try:
            result: bool = self._wait_instance.until(EC.url_contains(substring))
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="url_contains").observe(duration)
            return result
        except SeleniumTimeoutException as e:
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="url_contains").observe(duration)
            url = self._driver.current_url
            raise TimeoutError(
                f"URL does not contain '{substring}' (current: {url})",
                timeout_sec=self._timeout,
            ) from e
