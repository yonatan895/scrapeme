"""Circuit breaker pattern for failing sites."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto
from threading import Lock
from typing import TYPE_CHECKING

from core.metrics import Metrics

if TYPE_CHECKING:
    from core.type_aliases import SiteName

__all__ = ["CircuitBreaker", "CircuitState"]


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = auto()  # Normal operation
    OPEN = auto()  # Failing, reject requests
    HALF_OPEN = auto()  # Testing recovery


@dataclass(slots=True)
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2


class CircuitBreaker:
    """Circuit breaker for site scraping."""

    __slots__ = (
        "_site",
        "_config",
        "_state",
        "_failures",
        "_successes",
        "_last_failure_time",
        "_lock",
    )

    def __init__(self, site: SiteName, config: CircuitBreakerConfig | None = None) -> None:
        self._site = site
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._successes = 0
        self._last_failure_time: float | None = None
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        with self._lock:
            self._maybe_attempt_reset()
            return self._state

    def _maybe_attempt_reset(self) -> None:
        """Attempt to reset circuit if recovery timeout elapsed."""
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            if time.time() - self._last_failure_time >= self._config.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                self._successes = 0

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state with metrics."""
        old_state = self._state
        self._state = new_state
        Metrics.circuit_breaker_state_changes.labels(
            site=self._site,
            from_state=old_state.name,
            to_state=new_state.name,
        ).inc()

    def record_success(self) -> None:
        """Record successful operation."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._successes += 1
                if self._successes >= self._config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    self._failures = 0
            elif self._state == CircuitState.CLOSED:
                self._failures = 0

    def record_failure(self) -> None:
        """Record failed operation."""
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failures >= self._config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

            failure_rate = self._failures / max(self._failures + self._successes, 1)
            Metrics.circuit_breaker_failure_rate.labels(site=self._site).set(failure_rate)

    def is_call_permitted(self) -> bool:
        """Check if call is permitted."""
        with self._lock:
            self._maybe_attempt_reset()
            return self._state != CircuitState.OPEN


class CircuitBreakerRegistry:
    """Global registry of circuit breakers."""

    _breakers: dict[SiteName, CircuitBreaker] = {}
    _lock = Lock()

    @classmethod
    def get(cls, site: SiteName) -> CircuitBreaker:
        """Get or create circuit breaker for site."""
        with cls._lock:
            if site not in cls._breakers:
                cls._breakers[site] = CircuitBreaker(site)
            return cls._breakers[site]
