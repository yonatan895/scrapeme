"""Declarative retry policies with exponential backoff and jitter."""

from __future__ import annotations

import logging
import random
from typing import Any

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from tenacity import (
    RetryCallState,
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.metrics import Metrics

__all__ = ["RETRYABLE_EXCEPTIONS", "selenium_retry"]

logger = logging.getLogger(__name__)

# Tuple for retry_if_exception_type
RETRYABLE_EXCEPTIONS = (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    WebDriverException,
)


def _record_retry_metric(retry_state: RetryCallState) -> None:
    """Record retry attempt in metrics."""
    if retry_state.outcome and retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        if exception:
            Metrics.retries_total.labels(
                site="unknown",
                exception_type=type(exception).__name__,
            ).inc()


def _add_jitter(wait_time: float) -> float:
    """Add jitter to wait time."""
    jitter = wait_time * 0.25 * (random.random() * 2 - 1)
    return max(0.1, wait_time + jitter)


class JitteredExponentialWait:
    """Exponential backoff with jitter."""

    def __init__(self, multiplier: float = 0.5, min_wait: float = 0.5, max_wait: float = 4.0):
        self.multiplier = multiplier
        self.min_wait = min_wait
        self.max_wait = max_wait

    def __call__(self, retry_state: RetryCallState) -> float:
        """Calculate wait time with jitter."""
        attempt = retry_state.attempt_number
        wait = min(self.max_wait, self.multiplier * (2**attempt))
        wait = max(self.min_wait, wait)
        return _add_jitter(wait)


selenium_retry = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=JitteredExponentialWait(multiplier=0.5, min_wait=0.5, max_wait=4.0),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    after=after_log(logger, logging.DEBUG),
)


selenium_retry_aggressive = retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=JitteredExponentialWait(multiplier=0.3, min_wait=0.3, max_wait=8.0),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
