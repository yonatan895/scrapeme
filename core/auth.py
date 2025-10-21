"""Form-based authentication with retries and artifact capture."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By

from core.exceptions import ErrorContext, LoginError
from core.metrics import Metrics
from core.retry import selenium_retry

if TYPE_CHECKING:
    from logging import Logger

    from config.models import LoginConfig
    from core.capture import ArtifactCapture
    from core.secrets import SecretProvider
    from core.waits import Waiter

__all__ = ["AuthFlow"]


class AuthFlow:
    """Handles form-based login with explicit waits and artifact capture."""

    __slots__ = ("_waiter", "_log", "_secrets", "_capture")

    def __init__(
        self,
        waiter: Waiter,
        logger: Logger,
        secrets: SecretProvider,
        *,
        artifact_dir: Path | None = None,
    ) -> None:
        self._waiter = waiter
        self._log = logger
        self._secrets = secrets

        if artifact_dir is not None:
            from core.capture import ArtifactCapture

            capture_dir = artifact_dir / "login"
            self._capture = ArtifactCapture(
                waiter.driver,
                capture_dir,
                logger,
                enabled=True,
            )
        else:
            from core.capture import ArtifactCapture

            self._capture = ArtifactCapture(
                waiter.driver,
                Path(),
                logger,
                enabled=False,
            )

    @selenium_retry
    def _fill_field(self, xpath: str, value: str) -> None:
        """Fill form field with retry on transient failures."""
        element = self._waiter.visible((By.XPATH, xpath))
        element.clear()
        element.send_keys(value)

    @selenium_retry
    def _click_element(self, xpath: str) -> None:
        """Click element with retry on transient failures."""
        element = self._waiter.clickable((By.XPATH, xpath))
        element.click()

    def login(self, config: LoginConfig, *, site_name: str = "unknown") -> None:
        """Execute login flow with post-login verification.

        Args:
            config: Login configuration
            site_name: Site name for error context and metrics

        Raises:
            LoginError: If credentials missing or login fails
        """
        username = self._secrets.get(config.username_env)
        password = self._secrets.get(config.password_env)

        if not username or not password:
            Metrics.login_attempts_total.labels(site=site_name, status="failed").inc()
            raise LoginError(
                f"Missing credentials: {config.username_env}, {config.password_env}",
                context=ErrorContext(site_name=site_name),
            )

        start_time = time.monotonic()

        with self._capture.on_failure(f"login_{site_name}"):
            try:
                self._log.info("Navigating to login URL")
                self._waiter.driver.get(config.url)

                self._log.info("Submitting credentials")
                self._fill_field(config.username_xpath, username)
                self._fill_field(config.password_xpath, password)
                self._click_element(config.submit_xpath)

                # Post-login verification
                if config.post_login_wait_xpath is not None:
                    self._log.info("Waiting for post-login element")
                    self._waiter.visible((By.XPATH, config.post_login_wait_xpath))

                if config.post_login_url_contains is not None:
                    self._log.info("Waiting for post-login URL")
                    self._waiter.url_contains(config.post_login_url_contains)

                duration = time.monotonic() - start_time
                Metrics.login_attempts_total.labels(site=site_name, status="success").inc()
                self._log.info("Login successful", extra={"duration_sec": duration})

            except Exception as e:
                duration = time.monotonic() - start_time
                Metrics.login_attempts_total.labels(site=site_name, status="failed").inc()

                current_url = None
                try:
                    current_url = self._waiter.driver.current_url
                except:
                    pass

                raise LoginError(
                    f"Login failed: {e}",
                    context=ErrorContext(
                        site_name=site_name,
                        url=current_url,
                    ),
                ) from e
