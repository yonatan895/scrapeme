"""Property-based tests for URL normalization using Hypothesis."""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from core.url import normalize_url


# Custom strategy for valid URLs
@st.composite
def valid_urls(draw):
    """Generate valid HTTP/HTTPS URLs."""
    scheme = draw(st.sampled_from(["http", "https"]))
    domain = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
            min_size=3,
            max_size=20,
        )
    )
    tld = draw(st.sampled_from(["com", "org", "net", "edu"]))
    path = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="/-_"),
            max_size=50,
        )
    )
    return f"{scheme}://{domain}.{tld}/{path}"


# URL-safe character strategy for query parameters
@st.composite
def url_safe_params(draw):
    """Generate URL-safe query parameters."""
    # RFC 3986 unreserved: A-Z a-z 0-9 - . _ ~
    safe_chars = st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="-._~"
    )
    return draw(
        st.dictionaries(
            st.text(alphabet=safe_chars, min_size=1, max_size=10),
            st.text(alphabet=safe_chars, max_size=20),
            min_size=1,
            max_size=5,
        )
    )


@pytest.mark.property
class TestURLNormalizationProperties:
    """Property-based tests for URL normalization."""

    @given(valid_urls())
    def test_normalization_is_idempotent(self, url: str):
        """Normalizing twice should give same result."""
        normalized_once = normalize_url(url)
        normalized_twice = normalize_url(normalized_once)
        assert normalized_once == normalized_twice

    @given(valid_urls())
    def test_normalized_url_has_scheme(self, url: str):
        """Normalized URL must have scheme."""
        normalized = normalize_url(url)
        assert normalized.startswith("http://") or normalized.startswith("https://")

    @given(valid_urls(), st.text(max_size=10))
    @settings(suppress_health_check=[HealthCheck.nested_given])
    def test_control_characters_removed(self, url: str, noise: str):
        """Control characters should be stripped."""
        dirty_url = url + "\r\n\t" + noise + "\x00\x01"
        normalized = normalize_url(dirty_url)
        for char in normalized:
            assert ord(char) >= 32

    @given(valid_urls(), url_safe_params())
    def test_query_params_preserved(self, base_url: str, params: dict):
        """Query parameters should be preserved after normalization."""
        from urllib.parse import parse_qs, urlencode, urlparse

        # Remove existing query to avoid collisions
        if "?" in base_url:
            base_url = base_url.split("?")[0]

        url_with_params = f"{base_url}?{urlencode(params)}"
        normalized = normalize_url(url_with_params)

        parsed_url = urlparse(normalized)
        query_params = parse_qs(parsed_url.query)

        for key in params:
            assert key in query_params, f"Key '{key}' missing from query params {query_params}"
