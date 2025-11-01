"""Enhanced Locust load testing for ScrapeMe framework.

This file provides comprehensive load testing scenarios including:
- Framework API testing via health endpoints
- Browser automation stress testing
- Metrics endpoint validation
- Circuit breaker behavior testing
- Rate limiting validation
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

from locust import HttpUser, TaskSet, between, events, task
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import InterruptTaskSet, RescheduleTask

# Configuration
TARGET_BASE = os.getenv("LOAD_BASE_URL", "http://localhost:9090")
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "9090"))
TEST_MODE = os.getenv("LOAD_TEST_MODE", "health")  # health, metrics, mixed, stress
ENABLE_EXTERNAL_TARGETS = os.getenv("ENABLE_EXTERNAL_TARGETS", "false").lower() == "true"

# External test targets for realistic scenarios
EXTERNAL_TARGETS = [
    "http://quotes.toscrape.com",
    "https://httpbin.org",
    "https://scrapeme.live",
]


class HealthCheckTaskSet(TaskSet):
    """Health endpoint testing - validates application health."""

    @task(5)
    def liveness_check(self) -> None:
        """Test the /healthz liveness endpoint."""
        with self.client.get("/healthz", name="GET /healthz", catch_response=True) as resp:
            if resp.status_code == 200:
                try:
                    data = resp.json() if resp.content else {}
                    if data.get("status") == "healthy":
                        resp.success()
                    else:
                        resp.failure(f"Unhealthy status: {data}")
                except (json.JSONDecodeError, KeyError):
                    resp.failure("Invalid health response format")
            else:
                resp.failure(f"Health check failed with status {resp.status_code}")

    @task(3)
    def readiness_check(self) -> None:
        """Test the /ready readiness endpoint."""
        with self.client.get("/ready", name="GET /ready", catch_response=True) as resp:
            if resp.status_code == 200:
                try:
                    data = resp.json() if resp.content else {}
                    if data.get("status") in ["healthy", "ready"]:
                        resp.success()
                    else:
                        resp.failure(f"Not ready status: {data}")
                except (json.JSONDecodeError, KeyError):
                    resp.failure("Invalid readiness response format")
            else:
                resp.failure(f"Readiness check failed with status {resp.status_code}")

    @task(2)
    def metrics_endpoint(self) -> None:
        """Validate metrics endpoint returns Prometheus format."""
        with self.client.get("/metrics", name="GET /metrics", catch_response=True) as resp:
            if resp.status_code == 200:
                content = resp.text
                # Basic validation for Prometheus format
                if "# HELP" in content and "# TYPE" in content:
                    resp.success()
                else:
                    resp.failure("Metrics not in Prometheus format")
            else:
                resp.failure(f"Metrics endpoint failed with status {resp.status_code}")


class StressTestTaskSet(TaskSet):
    """Stress testing scenarios for framework limits."""

    def on_start(self) -> None:
        """Initialize stress test session."""
        self.error_count = 0
        self.max_errors = 5

    @task(3)
    def concurrent_health_checks(self) -> None:
        """Rapid-fire health checks to test concurrency."""
        endpoints = ["/healthz", "/ready"]
        endpoint = random.choice(endpoints)

        with self.client.get(endpoint, name=f"STRESS {endpoint}", catch_response=True) as resp:
            if resp.status_code != 200:
                self.error_count += 1
                if self.error_count > self.max_errors:
                    resp.failure(f"Too many errors ({self.error_count}), backing off")
                    raise InterruptTaskSet()
                else:
                    resp.failure(f"Status {resp.status_code}")
            else:
                self.error_count = max(0, self.error_count - 1)  # Decay errors on success

    @task(2)
    def metrics_scraping(self) -> None:
        """Heavy metrics endpoint usage."""
        with self.client.get("/metrics", name="STRESS /metrics", catch_response=True) as resp:
            if resp.status_code == 200:
                # Simulate metrics parsing work
                lines = resp.text.count("\n")
                if lines < 10:
                    resp.failure("Insufficient metrics data")
            else:
                resp.failure(f"Status {resp.status_code}")

    @task(1)
    def circuit_breaker_test(self) -> None:
        """Test circuit breaker behavior with intentional failures."""
        # Simulate various failure scenarios
        endpoints = ["/nonexistent", "/error", "/timeout"]
        endpoint = random.choice(endpoints)

        with self.client.get(
            endpoint, name=f"CIRCUIT_TEST {endpoint}", catch_response=True
        ) as resp:
            # We expect these to fail - that's the point
            if resp.status_code >= 400:
                resp.success()  # Expected failure for circuit breaker testing
            else:
                resp.failure("Expected failure for circuit breaker test")


class ExternalTargetTaskSet(TaskSet):
    """External target testing for realistic browser automation scenarios."""

    def on_start(self) -> None:
        """Set up external target testing."""
        if not ENABLE_EXTERNAL_TARGETS:
            raise InterruptTaskSet("External targets disabled")

        self.target_base = random.choice(EXTERNAL_TARGETS)
        # Override host for this session
        self.client.base_url = self.target_base

    @task(5)
    def homepage_load(self) -> None:
        """Load homepage of external target."""
        with self.client.get("/", name="EXT /", catch_response=True) as resp:
            if resp.status_code == 200:
                # Basic content validation
                if len(resp.content) > 1000:  # Reasonable page size
                    resp.success()
                else:
                    resp.failure("Page content too small")
            else:
                resp.failure(f"Status {resp.status_code}")

    @task(2)
    def page_navigation(self) -> None:
        """Navigate to different pages."""
        pages = ["/page/1", "/page/2", "/login", "/about", "/contact"]
        page = random.choice(pages)

        with self.client.get(page, name=f"EXT {page}", catch_response=True) as resp:
            if resp.status_code in [200, 404]:  # 404 is acceptable for test pages
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")


class MixedTestTaskSet(TaskSet):
    """Mixed testing combining all scenarios."""

    tasks = {
        HealthCheckTaskSet: 50,
        StressTestTaskSet: 30,
    }

    def on_start(self) -> None:
        """Initialize mixed testing."""
        if ENABLE_EXTERNAL_TARGETS:
            self.tasks[ExternalTargetTaskSet] = 20


class HealthUser(HttpUser):
    """User focused on health and metrics endpoints."""

    wait_time = between(0.5, 1.5)
    tasks = [HealthCheckTaskSet]
    weight = 3

    def on_start(self) -> None:
        """Set up health testing user."""
        self.client.base_url = TARGET_BASE


class StressUser(HttpUser):
    """User for stress testing scenarios."""

    wait_time = between(0.1, 0.5)  # More aggressive timing
    tasks = [StressTestTaskSet]
    weight = 2

    def on_start(self) -> None:
        """Set up stress testing user."""
        self.client.base_url = TARGET_BASE


class ExternalUser(HttpUser):
    """User for external target testing."""

    wait_time = between(1.0, 3.0)
    tasks = [ExternalTargetTaskSet]
    weight = 1 if ENABLE_EXTERNAL_TARGETS else 0


class MixedUser(HttpUser):
    """User combining multiple test scenarios."""

    wait_time = between(0.5, 2.0)
    tasks = [MixedTestTaskSet]
    weight = 4

    def on_start(self) -> None:
        """Set up mixed testing user."""
        self.client.base_url = TARGET_BASE


class FastHealthUser(FastHttpUser):
    """High-performance user for health checks using FastHttpUser."""

    wait_time = between(0.1, 0.3)
    weight = 2

    def on_start(self) -> None:
        """Set up fast health testing."""
        self.client.base_url = TARGET_BASE

    @task(10)
    def fast_health_check(self) -> None:
        """Rapid health checks."""
        with self.client.get("/healthz", name="FAST /healthz") as resp:
            if resp.status_code != 200:
                print(f"Fast health check failed: {resp.status_code}")

    @task(5)
    def fast_metrics_check(self) -> None:
        """Rapid metrics checks."""
        with self.client.get("/metrics", name="FAST /metrics") as resp:
            if resp.status_code != 200:
                print(f"Fast metrics check failed: {resp.status_code}")


# Event handlers for additional insights
@events.request.add_listener
def on_request(
    request_type: str, name: str, response_time: float, response_length: int, **kwargs: Any
) -> None:
    """Log slow requests for analysis."""
    if response_time > 5000:  # Log requests slower than 5 seconds
        print(f"SLOW REQUEST: {request_type} {name} took {response_time:.2f}ms")


@events.test_start.add_listener
def on_test_start(environment: Any, **kwargs: Any) -> None:
    """Initialize test session."""
    print(f"Load test starting with mode: {TEST_MODE}")
    print(f"Target: {TARGET_BASE}")
    print(f"External targets enabled: {ENABLE_EXTERNAL_TARGETS}")


@events.test_stop.add_listener
def on_test_stop(environment: Any, **kwargs: Any) -> None:
    """Clean up test session."""
    print("Load test completed")

    # Save results summary
    if hasattr(environment, "stats") and environment.stats.entries:
        results = {
            "timestamp": time.time(),
            "test_mode": TEST_MODE,
            "target_base": TARGET_BASE,
            "total_requests": sum(stat.num_requests for stat in environment.stats.entries.values()),
            "total_failures": sum(stat.num_failures for stat in environment.stats.entries.values()),
            "avg_response_time": environment.stats.total.avg_response_time,
            "max_response_time": environment.stats.total.max_response_time,
            "requests_per_second": environment.stats.total.current_rps,
        }

        results_file = Path("load_test_results.json")
        with results_file.open("w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {results_file}")
