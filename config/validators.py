"""Input validation utilities."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from lxml import etree

__all__ = ["validate_xpath", "validate_url", "sanitize_context_name"]


def validate_xpath(xpath: str) -> bool:
    """Validate XPath syntax."""
    try:
        etree.XPath(xpath)
        return True
    except etree.XPathSyntaxError:
        return False


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def sanitize_context_name(context: str, max_length: int = 100) -> str:
    """Sanitize context name for safe filesystem use."""
    safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", context)
    if len(safe) > max_length:
        safe = safe[:max_length]
    return safe
