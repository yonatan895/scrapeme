"""Property-based tests for URL normalization using Hypothesis."""

from __future__ import annotations

import pytest
from hypothesis import given, settings, HealthCheck
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
        # Inject control characters
        dirty_url = url + "\r\n\t" + noise + "\x00\x01"
        normalized = normalize_url(dirty_url)

        # Should not contain control chars
        for char in normalized:
            assert ord(char) >= 32

            @given(
                valid_urls(),
                st.dictionaries(
                    st.text(min_size=1, max_size=10),
                    st.text(max_size=20),
                    min_size=1,
                    max_size=5,
                ),
            )
            def test_query_params_preserved(self, base_url: str, params: dict):
                """Query parameters should be preserved after normalization."""
                from urllib.parse import urlencode, urlparse, parse_qs
        
                url_with_params = f"{base_url}?{urlencode(params)}"
                normalized = normalize_url(url_with_params)
        
                # All param keys should be in normalized URL's query string
                parsed_url = urlparse(normalized)
                query_params = parse_qs(parsed_url.query)
        
                for key in params:
                    assert key in query_params
