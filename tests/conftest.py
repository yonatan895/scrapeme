"""Shared test fixtures and configuration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config.models import FieldConfig, LoginConfig, SiteConfig, StepBlock
from core.secrets import EnvSecrets
from core.waits import Waiter


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "property: Property-based tests")
    config.addinivalue_line("markers", "load: Load tests")
    config.addinivalue_line("markers", "chaos: Chaos engineering tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_driver():
    """Mock WebDriver for unit tests."""
    driver = MagicMock(spec=webdriver.Chrome)
    driver.current_url = "https://test.example.com"
    driver.page_source = "<html><body><h1>Test Page</h1></body></html>"
    driver.get_screenshot_as_png.return_value = b"fake_png_data"
    return driver


@pytest.fixture
def mock_waiter(mock_driver):
    """Mock Waiter with mock driver."""
    mock_waiter_instance = MagicMock(spec=Waiter)
    type(mock_waiter_instance).driver = PropertyMock(return_value=mock_driver)  # Mock the property
    mock_waiter_instance.timeout = 10  # Set a default integer value for timeout
    mock_waiter_instance.visible.return_value = MagicMock()  # Default return value
    mock_waiter_instance.presence.return_value = MagicMock()  # Default return value
    mock_waiter_instance.clickable.return_value = MagicMock()  # Default return value
    mock_waiter_instance.url_contains.return_value = True  # Default return value
    return mock_waiter_instance


@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.exception = Mock()
    return logger


@pytest.fixture
def temp_artifact_dir(tmp_path):
    """Temporary directory for artifacts."""
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    return artifact_dir


@pytest.fixture
def sample_login_config():
    """Sample login configuration."""
    return LoginConfig(
        url="https://test.example.com/login",
        username_xpath="//input[@id='username']",
        password_xpath="//input[@id='password']",
        submit_xpath="//button[@type='submit']",
        username_env="TEST_USER",
        password_env="TEST_PASS",
        post_login_wait_xpath="//div[@id='dashboard']",
        post_login_url_contains="/dashboard",
    )


@pytest.fixture
def sample_field_config():
    """Sample field configuration."""
    return FieldConfig(
        name="test_field",
        xpath="//span[@id='test']",
        attribute=None,
    )


@pytest.fixture
def sample_step_block(sample_field_config):
    """Sample step block."""
    return StepBlock(
        name="test_step",
        goto_url="https://test.example.com/page",
        wait_xpath="//h1[@id='title']",
        fields=(sample_field_config,),
    )


@pytest.fixture
def sample_site_config(sample_login_config, sample_step_block):
    """Sample site configuration."""
    return SiteConfig(
        name="test_site",
        base_url="https://test.example.com",
        login=sample_login_config,
        steps=(sample_step_block,),
        wait_timeout_sec=10,
        page_load_timeout_sec=20,
    )


@pytest.fixture(scope="session")
def test_server_port():
    """Test server port."""
    return 5555


@pytest.fixture
def env_secrets(monkeypatch):
    """EnvSecrets with test credentials."""
    monkeypatch.setenv("TEST_USER", "testuser")
    monkeypatch.setenv("TEST_PASS", "testpass123")
    return EnvSecrets()


@pytest.fixture(scope="session")
def chrome_options():
    """Chrome options for integration tests."""
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    return options


@pytest.fixture
def mock_metrics():
    """Mock Prometheus metrics."""
    with patch("core.metrics.Metrics") as mock:
        yield mock


@pytest.fixture
def ensure_capture_executor_shutdown(tmp_path):
    """Ensures the capture executor is shut down after tests using tmp_path."""
    yield
    from core.capture import shutdown_capture_executor

    shutdown_capture_executor()
