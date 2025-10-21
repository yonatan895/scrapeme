# tests/unit/test_url.py
"""Unit tests for URL utilities."""
import pytest
from core.url import normalize_url, is_absolute_url, make_absolute_url


class TestIsAbsoluteUrl:
    """Test is_absolute_url function."""
    
    def test_http_url(self):
        assert is_absolute_url("http://example.com") is True
    
    def test_https_url(self):
        assert is_absolute_url("https://example.com") is True
    
    def test_relative_url(self):
        assert is_absolute_url("/path/to/page") is False
    
    def test_empty_url(self):
        assert is_absolute_url("") is False


class TestMakeAbsoluteUrl:
    """Test make_absolute_url function."""
    
    def test_already_absolute(self):
        result = make_absolute_url("https://example.com/page", "https://base.com")
        assert result == "https://example.com/page"
    
    def test_relative_with_slash(self):
        result = make_absolute_url("/api/data", "https://example.com")
        assert result == "https://example.com/api/data"
    
    def test_relative_without_slash(self):
        result = make_absolute_url("api/data", "https://example.com")
        assert result == "https://example.com/api/data"
    
    def test_base_url_with_trailing_slash(self):
        result = make_absolute_url("/api", "https://example.com/")
        assert result == "https://example.com/api"
    
    def test_empty_url_raises(self):
        with pytest.raises(ValueError, match="URL cannot be empty"):
            make_absolute_url("", "https://example.com")
    
    def test_invalid_base_url_raises(self):
        with pytest.raises(ValueError, match="invalid base_url"):
            make_absolute_url("/api", "/relative/path")


class TestNormalizeUrl:
    """Test normalize_url function."""
    
    def test_valid_url(self):
        result = normalize_url("https://example.com/path")
        assert result == "https://example.com/path"
    
    def test_no_scheme_raises(self):
        with pytest.raises(ValueError, match="must have scheme"):
            normalize_url("/just/a/path")
    
    def test_empty_url_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_url("")

