"""Integration test for actual scraping functionality using SiteScraper."""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Optional

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config.models import FieldConfig, SiteConfig, StepBlock
from core.scraper import SiteScraper
from core.waits import Waiter


def _is_docker() -> bool:
    return bool(os.getenv("DOCKER_ENV")) or os.path.exists("/.dockerenv")


def _probe_selenium(remote_url: str, timeout_sec: float = 1.5) -> bool:
    try:
        status_url = remote_url.rstrip("/")
        if status_url.endswith("/session"):
            status_url = status_url[: -len("/session")] + "/status"
        elif not status_url.endswith("/status"):
            status_url = status_url + "/status"
        req = urllib.request.Request(status_url)
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:  # nosec B310
            data = resp.read()
            payload = json.loads(data.decode("utf-8"))
            return bool(payload)
    except Exception:
        return False


@pytest.fixture
def integration_chrome_driver():
    """Chrome WebDriver for integration tests (Grid or local)."""
    selenium_remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")

    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1280,720")

    if _is_docker():
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-ipc-flooding-protection")

    driver: Optional[webdriver.Chrome] = None

    if _probe_selenium(selenium_remote_url):
        try:
            driver = webdriver.Remote(command_executor=selenium_remote_url, options=options)
        except WebDriverException:
            driver = None

    if driver is None:
        try:
            driver = webdriver.Chrome(options=options)
        except WebDriverException:
            pytest.skip(
                "No Selenium Grid reachable and local Chrome/Chromedriver not available. "
                "Set SELENIUM_REMOTE_URL to a reachable Grid or install Chrome + Chromedriver."
            )

    yield driver
    driver.quit()


@pytest.mark.integration
def test_site_scraper_integration(integration_chrome_driver, tmp_path: Path):
    """Test SiteScraper with a real site (httpbin.org)."""
    field_config = FieldConfig(name="page_title", xpath="//h1", attribute=None)

    step_config = StepBlock(
        name="get_title",
        goto_url="https://httpbin.org/html",
        wait_xpath="//h1",
        fields=(field_config,),
    )

    site_config = SiteConfig(
        name="httpbin_test",
        base_url="https://httpbin.org",
        login=None,
        steps=(step_config,),
        wait_timeout_sec=30,
        page_load_timeout_sec=60,
    )

    waiter = Waiter(integration_chrome_driver, timeout_sec=30)
    logger = logging.getLogger("integration-test")

    scraper = SiteScraper(
        config=site_config,
        waiter=waiter,
        logger=logger,
        artifact_dir=tmp_path,
    )

    try:
        results = scraper.run()
        assert "get_title" in results
        step_data = results["get_title"]
        assert "page_title" in step_data
        assert isinstance(step_data["page_title"], str)
        assert len(step_data["page_title"]) > 0
    except (TimeoutException, WebDriverException) as e:
        if _is_docker():
            pytest.skip(f"Network/infra issue in Docker environment: {e}")
        raise
