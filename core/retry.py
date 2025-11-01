"""Retry utilities for Selenium operations."""

from __future__ import annotations

from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from tenacity import retry, stop_after_attempt, wait_fixed

P = ParamSpec("P")
R = TypeVar("R")


def selenium_retry(func: Callable[P, R]) -> Callable[P, R]:
    """Retry decorator for flaky Selenium interactions.

    Retries a few times with short delays to overcome transient flakiness.
    """

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.3))
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return wrapper
