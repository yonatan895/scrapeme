"""Integration test for actual scraping functionality."""

from __future__ import annotations

import os
from unittest.mock import Mock

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config.models import FieldConfig, SiteConfig, StepBlock
from core.processor import SiteProcessor
from core.secrets import EnvSecrets


@pytest.fixture
def integration_chrome_driver():
    """Chrome WebDriver for integration tests."""
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
            options=options
        )
    except Exception:
        driver = webdriver.Chrome(options=options)
    
    yield driver
    driver.quit()


@pytest.mark.integration
def test_site_processor_integration(integration_chrome_driver):
    """Test SiteProcessor with a real site (httpbin.org)."""
    # Create a simple config to test against httpbin.org
    field_config = FieldConfig(
        name="page_title",
        xpath="//title",
        attribute=None
    )
    
    step_config = StepBlock(
        name="get_title",
        goto_url="https://httpbin.org/html",
        wait_xpath="//title",
        fields=(field_config,)
    )
    
    site_config = SiteConfig(
        name="httpbin_test",
        base_url="https://httpbin.org",
        login=None,
        steps=(step_config,),
        wait_timeout_sec=10,
        page_load_timeout_sec=20
    )
    
    # Mock artifacts directory and secrets
    mock_artifacts_dir = Mock()
    mock_artifacts_dir.exists.return_value = True
    mock_secrets = Mock(spec=EnvSecrets)
    
    # Create processor and run
    processor = SiteProcessor(
        site_config=site_config,
        driver=integration_chrome_driver,
        artifacts_dir=mock_artifacts_dir,
        secrets=mock_secrets
    )
    
    result = processor.process_site()
    
    # Verify results
    assert result is not None
    assert result["site"] == "httpbin_test"
    assert "steps" in result
    assert len(result["steps"]) > 0
    
    # Check that the step ran
    step_result = result["steps"][0]
    assert step_result["name"] == "get_title"
    assert "fields" in step_result
