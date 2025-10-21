"""Token bucket rate limiter."""

from __future__ import annotations

import time
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.type_aliases import SiteName

__all__ = ["RateLimiter"]


class TokenBucket:
    """Token bucket for rate limiting."""

    __slots__ = ("_capacity", "_tokens", "_fill_rate", "_last_update", "_lock")

    def __init__(self, capacity: int, fill_rate: float) -> None:
        """Initialize token bucket.

        Args:
            capacity: Maximum tokens in bucket
            fill_rate: Tokens per second refill rate
        """
        self._capacity = capacity
        self._tokens = float(capacity)
        self._fill_rate = fill_rate
        self._last_update = time.monotonic()
        self._lock = Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self._capacity, self._tokens + elapsed * self._fill_rate)
        self._last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens.

        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait_for_tokens(self, tokens: int = 1, timeout: float | None = None) -> bool:
        """Wait for tokens to become available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum wait time in seconds

        Returns:
            True if tokens acquired, False if timeout
        """
        start = time.monotonic()
        while True:
            if self.consume(tokens):
                return True

            if timeout is not None and (time.monotonic() - start) >= timeout:
                return False

            # Wait for next refill
            time.sleep(0.1)


class RateLimiter:
    """Per-site rate limiter registry."""

    _limiters: dict[SiteName, TokenBucket] = {}
    _lock = Lock()

    @classmethod
    def get(cls, site: SiteName, requests_per_second: float = 2.0) -> TokenBucket:
        """Get or create rate limiter for site."""
        with cls._lock:
            if site not in cls._limiters:
                capacity = max(1, int(requests_per_second * 10))
                cls._limiters[site] = TokenBucket(capacity, requests_per_second)
            return cls._limiters[site]
