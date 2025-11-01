"""Integration test for actual scraping functionality using SiteScraper."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from unittest.mock import Mock

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException, TimeoutException

from config.models import FieldConfig, SiteConfig, StepBlock
from core.scraper import SiteScraper
from core.waits import Waiter


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
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--window-size=1280,720")
    
    # Docker-specific optimizations
    if os.getenv("DOCKER_ENV") or os.path.exists("/.dockerenv"):
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-ipc-flooding-protection")

    driver = None
    try:
        # Try remote first (for CI/Docker environments)
        driver = webdriver.Remote(
            command_executor=selenium_remote_url,
            options=options,
        )
    except (WebDriverException, ConnectionError) as e:
        # Fall back to local Chrome
        try:
            driver = webdriver.Chrome(options=options)
        except WebDriverException:
            pytest.skip(f"No WebDriver available: {e}")

    if driver:
        yield driver
        driver.quit()
    else:
        pytest.skip("Could not initialize WebDriver")


@pytest.mark.integration
def test_site_scraper_integration(integration_chrome_driver, tmp_path: Path):
    """Test SiteScraper with a real site (httpbin.org)."""
    # Minimal config to test against httpbin.org
    field_config = FieldConfig(
        name="page_title",
        xpath="//h1",
        attribute=None,
    )

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
        wait_timeout_sec=30,  # Increased timeout for Docker
        page_load_timeout_sec=60,  # Increased timeout for Docker
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

        # Assertions
        assert "get_title" in results
        step_data = results["get_title"]
        assert "page_title" in step_data
        assert isinstance(step_data["page_title"], str)
        assert len(step_data["page_title"]) > 0  # Should have some content
        
    except (TimeoutException, WebDriverException) as e:
        # In Docker environments, network issues might cause timeouts
        if os.getenv("DOCKER_ENV") or os.path.exists("/.dockerenv"):
            pytest.skip(f"Network timeout in Docker environment: {e}")
        else:
            raise
