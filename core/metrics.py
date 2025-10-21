"""Prometheus metrics for observability."""
from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.types import SiteName, StepName

__all__ = ["Metrics"]


class Metrics:
    """Centralized metrics collection."""
    
    __slots__ = ()
    
    # Counters
    scrapes_total = Counter(
        "selenium_scrapes_total",
        "Total number of scrape attempts",
        ["site", "status"],
    )
    
    login_attempts_total = Counter(
        "selenium_login_attempts_total",
        "Total login attempts",
        ["site", "status"],
    )
    
    steps_executed_total = Counter(
        "selenium_steps_executed_total",
        "Total steps executed",
        ["site", "step", "status"],
    )
    
    fields_extracted_total = Counter(
        "selenium_fields_extracted_total",
        "Total fields extracted",
        ["site", "step", "field"],
    )
    
    retries_total = Counter(
        "selenium_retries_total",
        "Total retry attempts",
        ["site", "exception_type"],
    )
    
    circuit_breaker_state_changes = Counter(
        "selenium_circuit_breaker_state_changes_total",
        "Circuit breaker state transitions",
        ["site", "from_state", "to_state"],
    )
    
    # Histograms
    scrape_duration_seconds = Histogram(
        "selenium_scrape_duration_seconds",
        "Time spent scraping site",
        ["site"],
        buckets=(1, 5, 10, 30, 60, 120, 300),
    )
    
    step_duration_seconds = Histogram(
        "selenium_step_duration_seconds",
        "Time spent on step",
        ["site", "step"],
        buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
    )
    
    wait_duration_seconds = Histogram(
        "selenium_wait_duration_seconds",
        "Explicit wait durations",
        ["wait_type"],
        buckets=(0.1, 0.5, 1, 2, 5, 10, 20),
    )
    
    page_load_duration_seconds = Histogram(
        "selenium_page_load_duration_seconds",
        "Page load times",
        ["site"],
        buckets=(0.5, 1, 2, 5, 10, 30),
    )
    
    # Gauges
    active_sessions = Gauge(
        "selenium_active_sessions",
        "Current active WebDriver sessions",
    )
    
    circuit_breaker_failure_rate = Gauge(
        "selenium_circuit_breaker_failure_rate",
        "Current failure rate for circuit breaker",
        ["site"],
    )
    
    memory_usage_bytes = Gauge(
        "selenium_memory_usage_bytes",
        "Current memory usage",
    )
    
    # Info
    build_info = Info(
        "selenium_automation_build",
        "Build information",
    )
    
    @classmethod
    def record_scrape_success(cls, site: SiteName, duration: float) -> None:
        """Record successful scrape."""
        cls.scrapes_total.labels(site=site, status="success").inc()
        cls.scrape_duration_seconds.labels(site=site).observe(duration)
    
    @classmethod
    def record_scrape_failure(cls, site: SiteName, duration: float, error_type: str) -> None:
        """Record failed scrape."""
        cls.scrapes_total.labels(site=site, status="failure").inc()
        cls.scrape_duration_seconds.labels(site=site).observe(duration)
    
    @classmethod
    def record_step_execution(
        cls,
        site: SiteName,
        step: StepName,
        duration: float,
        success: bool,
    ) -> None:
        """Record step execution."""
        status = "success" if success else "failure"
        cls.steps_executed_total.labels(site=site, step=step, status=status).inc()
        cls.step_duration_seconds.labels(site=site, step=step).observe(duration)
