"""High-performance artifact capture with async I/O."""
from __future__ import annotations

import concurrent.futures
import contextlib
import functools
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, ParamSpec, TypeVar

if TYPE_CHECKING:
    from logging import Logger
    from selenium.webdriver.remote.webdriver import WebDriver

__all__ = ["ArtifactCapture", "CapturedArtifact"]

P = ParamSpec("P")
R = TypeVar("R")

# Global thread pool for async artifact writing
_CAPTURE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="artifact_writer",
)


@dataclass(slots=True, frozen=True, kw_only=True)
class CapturedArtifact:
    """Immutable metadata for captured artifacts."""
    context: str
    timestamp: str
    screenshot: Path | None
    html: Path | None
    url: str | None


class ArtifactCapture:
    """High-performance artifact capture with async writes."""
    
    __slots__ = ("_driver", "_output_dir", "_logger", "_enabled")
    
    def __init__(
        self,
        driver: WebDriver,
        output_dir: Path,
        logger: Logger,
        *,
        enabled: bool = True,
    ) -> None:
        self._driver = driver
        self._output_dir = output_dir
        self._logger = logger
        self._enabled = enabled
        
        if self._enabled:
            self._output_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def enabled(self) -> bool:
        """Check if capture is enabled."""
        return self._enabled
    
    def _async_write_screenshot(self, path: Path, png_data: bytes) -> None:
        """Write screenshot asynchronously."""
        try:
            path.write_bytes(png_data)
            self._logger.debug(f"Screenshot written: {path.name}")
        except Exception as e:
            self._logger.warning(f"Async screenshot write failed: {e}")
    
    def _async_write_html(self, path: Path, html: str) -> None:
        """Write HTML asynchronously."""
        try:
            path.write_text(html, encoding="utf-8", errors="replace")
            self._logger.debug(f"HTML written: {path.name}")
        except Exception as e:
            self._logger.warning(f"Async HTML write failed: {e}")
    
    def capture(self, context: str) -> CapturedArtifact:
        """Capture artifacts with async I/O.
        
        Screenshot and HTML are captured synchronously but written async.
        """
        if not self._enabled:
            return CapturedArtifact(
                context=context,
                timestamp="",
                screenshot=None,
                html=None,
                url=None,
            )
        
        # Generate safe filename components
        timestamp = time.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        safe_context = "".join(
            c if c.isalnum() or c in ("_", "-") else "_" for c in context
        )
        
        # Capture URL
        current_url = None
        try:
            current_url = self._driver.current_url
        except Exception as e:
            self._logger.debug(f"Failed to retrieve current URL: {e}")
        
        # Capture screenshot (in-memory)
        screenshot_path = None
        png_data = None
        try:
            png_data = self._driver.get_screenshot_as_png()
            screenshot_path = self._output_dir / f"{safe_context}_{timestamp}.png"
            self._logger.info(f"Screenshot captured: {screenshot_path.name}")
        except Exception as e:
            self._logger.warning(f"Screenshot capture failed for '{context}': {e}")
        
        # Capture HTML (in-memory)
        html_path = None
        html_source = None
        try:
            html_source = self._driver.page_source
            html_path = self._output_dir / f"{safe_context}_{timestamp}.html"
            self._logger.info(f"HTML captured: {html_path.name}")
        except Exception as e:
            self._logger.warning(f"HTML capture failed for '{context}': {e}")
        
        # Submit async writes
        if png_data and screenshot_path:
            _CAPTURE_EXECUTOR.submit(self._async_write_screenshot, screenshot_path, png_data)
        
        if html_source and html_path:
            _CAPTURE_EXECUTOR.submit(self._async_write_html, html_path, html_source)
        
        return CapturedArtifact(
            context=context,
            timestamp=timestamp,
            screenshot=screenshot_path,
            html=html_path,
            url=current_url,
        )
    
    @contextlib.contextmanager
    def on_failure(self, context: str):
        """Context manager capturing artifacts only on exception."""
        try:
            yield
        except Exception as e:
            if self._enabled:
                artifact = self.capture(context)
                if not hasattr(e, "_capture_artifact"):
                    e._capture_artifact = artifact  # type: ignore[attr-defined]
            raise
    
    def decorator(
        self,
        context: str | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Create decorator for automatic failure capture."""
        def decorator_impl(func: Callable[P, R]) -> Callable[P, R]:
            ctx = context or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                with self.on_failure(ctx):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator_impl


def shutdown_capture_executor() -> None:
    """Shutdown capture executor gracefully."""
    _CAPTURE_EXECUTOR.shutdown(wait=True, cancel_futures=False)
