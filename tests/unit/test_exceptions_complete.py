"""Unit tests for core.exceptions to achieve complete coverage."""

import pytest

from core.exceptions import (
    ConfigurationError,
    ElementNotFoundError,
    ScrapingError,
    TimeoutError,
)


@pytest.mark.unit
class TestExceptions:
    def test_element_not_found_error_construction(self):
        """Test ElementNotFoundError with various arguments."""
        # Basic message
        err1 = ElementNotFoundError("Element not found")
        assert str(err1) == "Element not found"

        # With locator info
        err2 = ElementNotFoundError("Element not found: //div[@id='test']")
        assert "//div[@id='test']" in str(err2)

        # With chained exception (must raise to chain)
        try:
            cause = Exception("Original cause")
            raise ElementNotFoundError("Element not found") from cause
        except ElementNotFoundError as err3:
            assert err3.__cause__ is not None
            assert str(err3.__cause__) == "Original cause"

    def test_timeout_error_construction(self):
        """Test TimeoutError with timeout information."""
        # With timeout seconds
        err1 = TimeoutError("Operation timed out", timeout_sec=30)
        assert "Operation timed out" in str(err1)

        # Without timeout seconds
        err2 = TimeoutError("Operation timed out")
        assert "Operation timed out" in str(err2)

        # With chained exception (must raise to chain)
        try:
            cause = Exception("Selenium timeout")
            raise TimeoutError("Wait failed", timeout_sec=10) from cause
        except TimeoutError as err3:
            assert err3.__cause__ is not None
            assert str(err3.__cause__) == "Selenium timeout"

    def test_scraping_error_construction(self):
        """Test ScrapingError construction."""
        err1 = ScrapingError("Failed to scrape data")
        assert str(err1) == "Failed to scrape data"

        # With site context
        err2 = ScrapingError("Failed to scrape from example.com")
        assert "example.com" in str(err2)

        # Optional chaining example
        try:
            cause = ValueError("Bad data")
            raise ScrapingError("Failed to scrape") from cause
        except ScrapingError as err:
            assert err.__cause__ is not None
            assert isinstance(err.__cause__, ValueError)

    def test_configuration_error_construction(self):
        """Test ConfigurationError construction."""
        err1 = ConfigurationError("Invalid config")
        assert str(err1) == "Invalid config"

        # With field context
        err2 = ConfigurationError("Missing required field: base_url")
        assert "base_url" in str(err2)

    def test_all_exceptions_inherit_properly(self):
        """Test inheritance hierarchy."""
        assert issubclass(ElementNotFoundError, ScrapingError)
        assert issubclass(TimeoutError, ScrapingError)
        assert issubclass(ConfigurationError, Exception)
        assert issubclass(ScrapingError, Exception)
