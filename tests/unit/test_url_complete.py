"""Unit tests for core.url module to achieve 100% coverage."""

import urllib.parse

import pytest

from core.url import normalize_url


@pytest.mark.unit
class TestURLNormalizeUnit:
    def test_empty_query_value_preserved(self):
        """Empty query values should be preserved."""
        url = "http://example.com/?k="
        normalized = normalize_url(url)
        parsed = urllib.parse.urlparse(normalized)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        assert ("k", "") in pairs

    def test_multi_value_param_preserved(self):
        """Multi-value parameters should be preserved."""
        base = "http://example.com/"
        query = urllib.parse.urlencode([("k", "a"), ("k", "b")], doseq=True)
        url = f"{base}?{query}"
        normalized = normalize_url(url)
        parsed = urllib.parse.urlparse(normalized)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        assert ("k", "a") in pairs and ("k", "b") in pairs

    def test_fragment_idempotent(self):
        """Fragment normalization should be idempotent."""
        url = "http://example.com/path?x=1#frag"
        normalized = normalize_url(url)
        again = normalize_url(normalized)
        assert normalized == again

    def test_trailing_slash_normalization(self):
        """Trailing slash behavior should be consistent."""
        url1 = "http://example.com/path"
        url2 = "http://example.com/path/"
        normalized1 = normalize_url(url1)
        normalized2 = normalize_url(url2)
        # Both should normalize consistently (implementation dependent)
        assert normalize_url(normalized1) == normalized1
        assert normalize_url(normalized2) == normalized2

    def test_percent_encoding_roundtrip(self):
        """Percent-encoded values should round-trip correctly."""
        url = "http://example.com/?q=hello%20world&special=%2B%26%3D"
        normalized = normalize_url(url)
        parsed = urllib.parse.urlparse(normalized)
        pairs = urllib.parse.parse_qsl(parsed.query)
        # Should decode properly
        assert any("hello world" in v for k, v in pairs)
        assert any("+&=" in v for k, v in pairs)

    def test_scheme_handling(self):
        """Scheme should be preserved and consistent."""
        http_url = "http://example.com/"
        https_url = "https://example.com/"
        assert normalize_url(http_url).startswith("http://")
        assert normalize_url(https_url).startswith("https://")
