"""URL normalization with LRU caching for performance."""

from __future__ import annotations

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

__all__ = ["normalize_url", "is_absolute_url", "make_absolute_url"]


def is_absolute_url(url: str) -> bool:
    """Check if URL is absolute (has scheme).

    Args:
        url: URL to check

    Returns:
        True if URL has http/https scheme
    """
    if not url:
        return False
    url = url.strip()
    return url.startswith(("http://", "https://"))


def make_absolute_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute using base URL.

    Args:
        url: URL (absolute or relative)
        base_url: Base URL for relative paths

    Returns:
        Absolute URL

    Raises:
        ValueError: If result is not a valid absolute URL
    """
    if not url or url.isspace():
        raise ValueError("URL cannot be empty")

    url = url.strip()

    # Already absolute
    if is_absolute_url(url):
        return url

    # Relative URL - need base
    if not base_url or not is_absolute_url(base_url):
        raise ValueError(
            f"Cannot make absolute URL: relative URL '{url}' but invalid base_url '{base_url}'"
        )

    # Ensure base_url doesn't end with / if url starts with /
    base_url = base_url.rstrip("/")

    # Add leading / if missing
    if not url.startswith("/"):
        url = "/" + url

    return base_url + url


@lru_cache(maxsize=1024)
def normalize_url(url: str) -> str:
    """Normalize URL with caching for repeated calls.

    Cache size of 1024 covers typical scraping workloads.

    Args:
        url: Raw URL string (must be absolute with scheme)

    Returns:
        Normalized URL safe for WebDriver

    Raises:
        ValueError: If URL has no scheme or is invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Convert to string if not already
    if not isinstance(url, str):
        url = str(url)

    # Strip control characters and whitespace
    url = "".join(ch for ch in url if ord(ch) >= 32).strip()

    if not url:
        raise ValueError("URL is empty after stripping whitespace")

    parts = urlsplit(url)
    if not parts.scheme:
        raise ValueError(f"URL must have scheme (http/https): {url}")

    if parts.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme must be http or https, got: {parts.scheme}")

    # Re-encode query with proper escaping
    query = urlencode(parse_qsl(parts.query, keep_blank_values=True), doseq=True)

    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
