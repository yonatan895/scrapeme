"""URL normalization with LRU caching for performance."""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

__all__ = ["normalize_url"]


@lru_cache(maxsize=1024)
def normalize_url(url: str) -> str:
    """Normalize URL with caching for repeated calls.
    
    Cache size of 1024 covers typical scraping workloads.
    
    Args:
        url: Raw URL string
        
    Returns:
        Normalized URL safe for WebDriver
        
    Raises:
        ValueError: If URL has no scheme
    """
    
    # Strip control characters and whitespace
    url = "".join(ch for ch in url if ord(ch) >= 32).strip()
    
    parts = urlsplit(url)
    if not parts.scheme:
        raise ValueError(f"URL must have scheme (http/https): {url}")
    
    # Re-encode query with proper escaping
    query = urlencode(
        parse_qsl(parts.query, keep_blank_values=True),
        doseq=True
    )
    
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
