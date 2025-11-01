"""WebDriver session lifecycle management."""

from __future__ import annotations

import atexit
import contextlib
import queue
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from config.models import Browser
from core.metrics import Metrics

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

__all__ = ["BrowserManager", "WebDriverPool"]


class WebDriverPool:
    """Thread-safe WebDriver connection pool for reuse."""

    __slots__ = ("_factory", "_pool", "_max_size", "_created", "_lock", "_closed")

    def __init__(self, factory: Callable[[], WebDriver], max_size: int = 10) -> None:
        """Initialize connection pool.

        Args:
            factory: Function that creates WebDriver instances
            max_size: Maximum pool size
        """
        self._factory = factory
        self._pool: queue.Queue[WebDriver] = queue.Queue(maxsize=max_size)
        self._max_size = max_size
        self._created = 0
        self._lock = threading.Lock()
        self._closed = False

        atexit.register(self.close_all)

    def acquire(self, timeout: float = 30.0) -> WebDriver:
        """Acquire a WebDriver from pool."""
        if self._closed:
            raise RuntimeError("Pool is closed")

        try:
            driver = self._pool.get(timeout=timeout)

            try:
                _ = driver.current_url
                Metrics.active_sessions.inc()
                return driver
            except Exception:
                driver.quit()
                self._created -= 1
        except queue.Empty:
            pass

        with self._lock:
            if self._created < self._max_size:
                driver = self._factory()
                self._created += 1
                Metrics.active_sessions.inc()
                return driver

        driver = self._pool.get(timeout=timeout)
        Metrics.active_sessions.inc()
        return driver

    def release(self, driver: WebDriver) -> None:
        """Release WebDriver back to pool."""
        if self._closed:
            driver.quit()
            return

        try:
            _ = driver.current_url
            self._pool.put_nowait(driver)
        except (queue.Full, Exception):
            driver.quit()
            with self._lock:
                self._created -= 1
        finally:
            Metrics.active_sessions.dec()

    def close_all(self) -> None:
        """Close all pooled connections."""
        self._closed = True
        while True:
            try:
                driver = self._pool.get_nowait()
                driver.quit()
            except queue.Empty:
                break
        self._created = 0
        Metrics.active_sessions.set(0)

    @contextlib.contextmanager
    def connection(self, timeout: float = 30.0) -> Iterator[WebDriver]:
        """Context manager for pool connection."""
        driver = self.acquire(timeout)
        try:
            yield driver
        finally:
            self.release(driver)


class BrowserManager:
    """Enhanced WebDriver factory with pooling support."""

    __slots__ = (
        "_browser",
        "_headless",
        "_incognito",
        "_page_load_timeout",
        "_download_dir",
        "_proxy",
        "_chromedriver_path",
        "_geckodriver_path",
        "_remote_url",
        "_chrome_binary",
        "_pool",
    )

    def __init__(
        self,
        *,
        browser: str = "chrome",
        headless: bool = True,
        incognito: bool = False,
        page_load_timeout_sec: int = 30,
        download_dir: Path | None = None,
        proxy: str | None = None,
        chromedriver_path: Path | None = None,
        geckodriver_path: Path | None = None,
        remote_url: str | None = None,
        chrome_binary: Path | None = None,
        enable_pooling: bool = False,
        pool_size: int = 5,
    ) -> None:
        self._browser = Browser(browser)
        self._headless = headless
        self._incognito = incognito
        self._page_load_timeout = page_load_timeout_sec
        self._download_dir = download_dir
        self._proxy = proxy
        self._chromedriver_path = chromedriver_path
        self._geckodriver_path = geckodriver_path
        self._remote_url = remote_url
        self._chrome_binary = chrome_binary

        if enable_pooling:
            self._pool: WebDriverPool | None = WebDriverPool(
                self._create_driver, max_size=pool_size
            )
        else:
            self._pool = None

    @contextlib.contextmanager
    def session(self) -> Iterator[WebDriver]:
        """Context manager for WebDriver lifecycle."""
        if self._pool:
            with self._pool.connection() as driver:
                yield driver
        else:
            driver = self._create_driver()
            try:
                Metrics.active_sessions.inc()
                yield driver
            finally:
                driver.quit()
                Metrics.active_sessions.dec()

    def _create_driver(self) -> WebDriver:
        """Factory for WebDriver instances."""
        driver = (
            self._create_chrome() if self._browser == Browser.CHROME else self._create_firefox()
        )
        driver.set_page_load_timeout(self._page_load_timeout)
        driver.implicitly_wait(0)
        return driver

    def _create_chrome(self) -> WebDriver:
        """Chrome WebDriver with comprehensive options."""
        opts = ChromeOptions()

        if self._headless:
            opts.add_argument("--headless=new")

        if self._incognito:
            opts.add_argument("--incognito")

        if self._proxy:
            opts.add_argument(f"--proxy-server={self._proxy}")

        if self._chrome_binary:
            opts.binary_location = str(self._chrome_binary)

        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-features=VizDisplayCompositor")

        opts.set_capability("acceptInsecureCerts", True)
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument("--allow-insecure-localhost")
        opts.add_argument("--log-level=3")

        if self._download_dir:
            opts.add_experimental_option(
                "prefs",
                {
                    "download.default_directory": str(self._download_dir),
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True,
                },
            )

        if self._remote_url:
            return webdriver.Remote(command_executor=self._remote_url, options=opts)

        service = ChromeService(
            executable_path=str(self._chromedriver_path) if self._chromedriver_path else None
        )
        return webdriver.Chrome(service=service, options=opts)

    def _create_firefox(self) -> WebDriver:
        """Firefox WebDriver with basic options."""
        opts = FirefoxOptions()

        if self._headless:
            opts.add_argument("-headless")

        opts.set_capability("acceptInsecureCerts", True)

        if self._remote_url:
            return webdriver.Remote(command_executor=self._remote_url, options=opts)

        service = FirefoxService(
            executable_path=str(self._geckodriver_path) if self._geckodriver_path else None
        )
        return webdriver.Firefox(service=service, options=opts)
