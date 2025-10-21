"""Health check endpoints for container orchestration."""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

__all__ = ["HealthStatus", "HealthCheck", "HealthRegistry"]


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(slots=True, frozen=True)
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float


class HealthCheck:
    """Base health check."""
    
    def __init__(self, name: str, check_fn: Callable[[], tuple[HealthStatus, str]]) -> None:
        self.name = name
        self._check_fn = check_fn
    
    def execute(self) -> HealthCheckResult:
        """Execute health check with timing."""
        start = time.monotonic()
        try:
            status, message = self._check_fn()
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            message = f"Check failed: {e}"
        
        duration_ms = (time.monotonic() - start) * 1000
        return HealthCheckResult(self.name, status, message, duration_ms)


class HealthRegistry:
    """Registry of health checks."""
    
    _checks: list[HealthCheck] = []
    
    @classmethod
    def register(cls, name: str, check_fn: Callable[[], tuple[HealthStatus, str]]) -> None:
        """Register a health check."""
        cls._checks.append(HealthCheck(name, check_fn))
    
    @classmethod
    def check_all(cls) -> dict[str, HealthCheckResult]:
        """Execute all health checks."""
        return {check.name: check.execute() for check in cls._checks}
    
    @classmethod
    def is_healthy(cls) -> bool:
        """Check if all health checks pass."""
        results = cls.check_all()
        return all(r.status == HealthStatus.HEALTHY for r in results.values())
