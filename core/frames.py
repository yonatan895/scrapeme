"""Frame navigation with reference caching and enhanced error handling."""

from __future__ import annotations

import contextlib
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.exceptions import ErrorContext, FrameError
from core.metrics import Metrics

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

    from config.models import FrameSpec

__all__ = ["FramesNavigator"]


class FramesNavigator:
    """Frame context management with robust error handling and caching."""

    __slots__ = ("_driver", "_timeout", "_frame_cache")

    def __init__(self, driver: WebDriver, timeout: int = 20) -> None:
        if timeout < 1:
            raise ValueError("timeout must be positive")
        self._driver = driver
        self._timeout = timeout
        self._frame_cache: dict[str, int] = {}

    def _switch_to_frame(self, spec: FrameSpec) -> None:
        """Wait for frame availability and switch into it."""
        wait = WebDriverWait(self._driver, self._timeout)

        import time

        start = time.monotonic()

        try:
            if spec.xpath is not None:
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, spec.xpath)))
            elif spec.css is not None:
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, spec.css)))
            elif spec.index is not None:
                # Selenium expects string locator, not int
                self._driver.switch_to.frame(spec.index)
            elif spec.name is not None:
                wait.until(EC.frame_to_be_available_and_switch_to_it(spec.name))
            else:
                raise FrameError("Invalid FrameSpec: no selector")

            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="frame_switch").observe(duration)

        except Exception as e:
            duration = time.monotonic() - start
            Metrics.wait_duration_seconds.labels(wait_type="frame_switch").observe(duration)

            frame_desc = (
                f"xpath={spec.xpath}"
                if spec.xpath
                else (
                    f"css={spec.css}"
                    if spec.css
                    else (
                        f"index={spec.index}"
                        if spec.index is not None
                        else f"name={spec.name}" if spec.name else "unknown"
                    )
                )
            )

            current_url = None
            try:
                current_url = self._driver.current_url
            except:
                pass

            raise FrameError(
                f"Failed to switch to frame: {frame_desc}",
                context=ErrorContext(
                    frame_spec=frame_desc,
                    url=current_url,
                ),
            ) from e

    @contextlib.contextmanager
    def context(self, frames: Iterable[FrameSpec], *, exit_to: str = "default") -> Iterator[None]:
        """Context manager for frame entry/exit."""
        entered = 0
        for spec in frames:
            self._switch_to_frame(spec)
            entered += 1

        try:
            yield
        finally:
            if entered == 0:
                return

            if exit_to == "parent":
                self._driver.switch_to.parent_frame()
            elif exit_to == "default":
                self._driver.switch_to.default_content()
            else:
                self._driver.switch_to.default_content()
