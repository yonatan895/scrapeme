"""Retry utilities for Selenium operations."""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from tenacity import retry, stop_after_attempt, wait_fixed

F = TypeVar("F", bound=Callable[..., object])


def selenium_retry(func: F) -> F:
    """Retry decorator for flaky Selenium interactions.

    Retries a few times with short delays to overcome transient flakiness.
    """

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.3))
    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[misc]
        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
