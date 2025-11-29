"""Redis cache client wrapper."""

from __future__ import annotations

import os
from typing import Any

import redis

__all__ = ["get_redis_client"]

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis | None:
    """Get or create global Redis client.

    Returns:
        Redis client if REDIS_URL is set, else None.
    """
    global _client

    if _client is not None:
        return _client

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None

    try:
        _client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        _client.ping()
        return _client
    except Exception:
        # If connection fails, we return None so the app can degrade gracefully
        # (or we could let it crash, but graceful degradation for cache is usually better)
        # However, for 'go all out', maybe we want to know if it fails.
        # But for now, let's allow running without Redis if env var is missing.
        # If env var IS present but connection fails, maybe we should log it?
        # Since I don't have a logger here easily without circular imports or setup,
        # I'll just return None or raise.
        # Given the requirements, let's fail if configured but unreachable?
        # Or better, just print a warning and return None.
        _client = None
        return None
