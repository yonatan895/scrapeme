"""Unit tests for core.exceptions to achieve complete coverage of existing API only."""

import pytest

# Import only the exceptions that actually exist in core.exceptions
from core.exceptions import (
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

        # With locator info (string content check only)
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
        """Test TimeoutError with timeout information and chaining."""
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

    def test_scraping_error_construction_and_chaining(self):
        """Test ScrapingError construction and optional chaining."""
        err1 = ScrapingError("Failed to scrape data")
        assert str(err1) == "Failed to scrape data"

        # Optional chaining example
        try:
            cause = ValueError("Bad data")
            raise ScrapingError("Failed to scrape") from cause
        except ScrapingError as err:
            assert err.__cause__ is not None
            assert isinstance(err.__cause__, ValueError)

    def test_inheritance(self):
        """Test inheritance hierarchy among existing exception classes."""
        assert issubclass(ElementNotFoundError, ScrapingError)
        assert issubclass(TimeoutError, ScrapingError)
        assert issubclass(ScrapingError, Exception)
