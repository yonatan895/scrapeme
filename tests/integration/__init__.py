"""Integration tests that use Selenium WebDriver with real browsers."""

from __future__ import annotations

import os

import pytest
from selenium import webdriver
from urllib.parse import urlparse
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.waits import Waiter


@pytest.fixture
def chrome_remote_driver():
    """Chrome WebDriver connected to Selenium Grid (if available) or local."""
    selenium_remote_url = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")

    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")

    try:
        # Try Selenium Grid first
        driver = webdriver.Remote(
            command_executor=selenium_remote_url,
            options=options,
        )
    except Exception:
        # Fallback to local Chrome
        driver = webdriver.Chrome(options=options)

    yield driver
    driver.quit()


@pytest.mark.integration
def test_waiter_integration(chrome_remote_driver):
    """Test Waiter class with real WebDriver against a simple page."""
    driver = chrome_remote_driver
    waiter = Waiter(driver, timeout_sec=10)

    driver.get("https://httpbin.org/html")

    assert waiter.url_contains("httpbin.org")

    # Wait for an element
    h1_element = waiter.presence((By.TAG_NAME, "h1"))
    assert h1_element is not None

    # Visible wait
    h1_visible = waiter.visible((By.TAG_NAME, "h1"))
    assert h1_visible is not None


@pytest.mark.integration
def test_basic_selenium_grid_connectivity(chrome_remote_driver):
    """Test basic connectivity to Selenium Grid or local Chrome."""
    driver = chrome_remote_driver

    driver.get("https://httpbin.org/status/200")
    parsed = urlparse(driver.current_url)
    # Check if the hostname is httpbin.org (no substring check)
    assert parsed.hostname == "httpbin.org"

    # Page source accessible
    page_source = driver.page_source
    assert len(page_source) > 0


@pytest.mark.integration
def test_selenium_grid_capabilities(chrome_remote_driver):
    """Test executing basic Selenium commands."""
    driver = chrome_remote_driver

    driver.get("https://httpbin.org/forms/post")

    # Find form element
    wait = WebDriverWait(driver, 10)
    form = wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
    assert form is not None

    # Screenshot capability
    screenshot = driver.get_screenshot_as_png()
    assert isinstance(screenshot, bytes)
    assert len(screenshot) > 0
