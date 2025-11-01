import urllib.parse

import pytest

from core.url import normalize_url


@pytest.mark.unit
class TestURLNormalizeUnit:
    def test_empty_query_value_preserved(self):
        url = "http://example.com/?k="
        normalized = normalize_url(url)
        parsed = urllib.parse.urlparse(normalized)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        assert ("k", "") in pairs

    def test_multi_value_param_preserved(self):
        base = "http://example.com/"
        query = urllib.parse.urlencode([("k", "a"), ("k", "b")], doseq=True)
        url = f"{base}?{query}"
        normalized = normalize_url(url)
        parsed = urllib.parse.urlparse(normalized)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        assert ("k", "a") in pairs and ("k", "b") in pairs

    def test_fragment_idempotent(self):
        url = "http://example.com/path?x=1#frag"
        normalized = normalize_url(url)
        again = normalize_url(normalized)
        assert normalized == again
