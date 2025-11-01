"""Integration test for actual scraping functionality using SiteScraper."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from unittest.mock import Mock

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

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

    try:
        driver = webdriver.Remote(
            command_executor=selenium_remote_url,
            options=options,
        )
    except Exception:
        driver = webdriver.Chrome(options=options)

    yield driver
    driver.quit()


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
        wait_timeout_sec=10,
        page_load_timeout_sec=20,
    )

    waiter = Waiter(integration_chrome_driver, timeout_sec=10)
    logger = logging.getLogger("integration-test")

    scraper = SiteScraper(
        config=site_config,
        waiter=waiter,
        logger=logger,
        artifact_dir=tmp_path,
    )

    results = scraper.run()

    # Assertions
    assert "get_title" in results
    step_data = results["get_title"]
    assert "page_title" in step_data
    assert isinstance(step_data["page_title"], str)
