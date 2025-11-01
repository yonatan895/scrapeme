"""Real application load testing for ScrapeMe.

This file provides load testing scenarios that test the actual ScrapeMe application
under realistic conditions, including:
- Full browser automation workflows
- Selenium WebDriver stress testing
- Real scraping scenario validation
- Resource utilization monitoring
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

# Configuration for real application testing
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
METRICS_URL = os.getenv("METRICS_URL", "http://localhost:9090")
SCRAPING_CONFIG = os.getenv("SCRAPING_CONFIG", "config/test_sites.yaml")
TEST_MODE = os.getenv("REAL_LOAD_TEST_MODE", "scraping")  # scraping, monitoring, mixed


class RealScrapingTaskSet(TaskSet):
    """Load testing actual scraping workflows."""

    def on_start(self) -> None:
        """Initialize scraping test session."""
        self.session_data = {"start_time": time.time(), "scrapes_completed": 0, "errors": 0}

    @task(5)
    def trigger_scraping_job(self) -> None:
        """Trigger a real scraping job via API or runner."""
        with self.client.post(
            "/api/scrape",
            json={"config": "test_site_minimal.yaml", "headless": True, "timeout": 30},
            name="POST /api/scrape",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.session_data["scrapes_completed"] += 1
                response.success()
            elif response.status_code == 202:
                # Accepted - job queued
                response.success()
            else:
                self.session_data["errors"] += 1
                response.failure(f"Scraping job failed: {response.status_code}")

    @task(3)
    def check_job_status(self) -> None:
        """Check status of running scraping jobs."""
        with self.client.get(
            "/api/jobs/status", name="GET /api/jobs/status", catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    active_jobs = data.get("active_jobs", 0)
                    if active_jobs > 100:  # Too many concurrent jobs
                        response.failure(f"Too many active jobs: {active_jobs}")
                    else:
                        response.success()
                except (json.JSONDecodeError, KeyError):
                    response.failure("Invalid job status response")
            else:
                response.failure(f"Job status check failed: {response.status_code}")

    @task(2)
    def retrieve_results(self) -> None:
        """Retrieve scraping results."""
        with self.client.get(
            "/api/results/latest", name="GET /api/results", catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    results_count = len(data.get("results", []))
                    if results_count > 0:
                        response.success()
                    else:
                        response.failure("No results available")
                except (json.JSONDecodeError, KeyError):
                    response.failure("Invalid results response")
            else:
                response.failure(f"Results retrieval failed: {response.status_code}")

    @task(1)
    def validate_data_quality(self) -> None:
        """Validate quality of scraped data."""
        with self.client.get(
            "/api/results/validate", name="GET /api/validate", catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    quality_score = data.get("quality_score", 0)
                    if quality_score < 0.8:  # Quality threshold
                        response.failure(f"Data quality too low: {quality_score}")
                    else:
                        response.success()
                except (json.JSONDecodeError, KeyError):
                    response.failure("Invalid validation response")
            else:
                response.failure(f"Data validation failed: {response.status_code}")


class RealMonitoringTaskSet(TaskSet):
    """Load testing monitoring and health endpoints of running application."""

    @task(10)
    def health_check_real_app(self) -> None:
        """Test health endpoint of running application."""
        # Use different base URL for metrics
        metrics_client = self.client
        metrics_client.base_url = METRICS_URL

        with metrics_client.get("/healthz", name="REAL /healthz", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure(f"Unhealthy status: {data}")
                except (json.JSONDecodeError, KeyError):
                    response.failure("Invalid health response format")
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def readiness_check_real_app(self) -> None:
        """Test readiness of running application."""
        metrics_client = self.client
        metrics_client.base_url = METRICS_URL

        with metrics_client.get("/ready", name="REAL /ready", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") in ["ready", "healthy"]:
                        response.success()
                    else:
                        response.failure(f"Not ready: {data}")
                except (json.JSONDecodeError, KeyError):
                    response.failure("Invalid readiness response format")
            else:
                response.failure(f"Readiness check failed: {response.status_code}")

    @task(3)
    def metrics_collection_real_app(self) -> None:
        """Test metrics endpoint with real application data."""
        metrics_client = self.client
        metrics_client.base_url = METRICS_URL

        with metrics_client.get("/metrics", name="REAL /metrics", catch_response=True) as response:
            if response.status_code == 200:
                content = response.text
                # Validate real metrics are present
                required_metrics = [
                    "scrapeme_scrapes_total",
                    "scrapeme_request_duration_seconds",
                    "scrapeme_browser_sessions_active",
                    "scrapeme_errors_total",
                ]

                missing_metrics = [m for m in required_metrics if m not in content]
                if missing_metrics:
                    response.failure(f"Missing metrics: {missing_metrics}")
                else:
                    response.success()
            else:
                response.failure(f"Metrics endpoint failed: {response.status_code}")

    @task(1)
    def resource_usage_check(self) -> None:
        """Check resource usage of running application."""
        with self.client.get(
            "/api/system/resources", name="GET /api/resources", catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    cpu_usage = data.get("cpu_percent", 0)
                    memory_usage = data.get("memory_percent", 0)

                    if cpu_usage > 90:
                        response.failure(f"High CPU usage: {cpu_usage}%")
                    elif memory_usage > 85:
                        response.failure(f"High memory usage: {memory_usage}%")
                    else:
                        response.success()
                except (json.JSONDecodeError, KeyError):
                    response.failure("Invalid resource usage response")
            else:
                response.failure(f"Resource check failed: {response.status_code}")


class BrowserStressTaskSet(TaskSet):
    """Stress testing browser automation specifically."""

    def on_start(self) -> None:
        """Initialize browser stress testing."""
        self.browser_sessions = 0
        self.max_sessions = 10  # Limit concurrent browser sessions

    @task(3)
    def start_browser_session(self) -> None:
        """Start a new browser automation session."""
        if self.browser_sessions >= self.max_sessions:
            return  # Skip if too many sessions

        with self.client.post(
            "/api/browser/start",
            json={"headless": True, "timeout": 60, "max_pages": 5},
            name="POST /api/browser/start",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                self.browser_sessions += 1
                response.success()
            else:
                response.failure(f"Browser session start failed: {response.status_code}")

    @task(5)
    def execute_browser_action(self) -> None:
        """Execute browser actions (clicks, form fills, navigation)."""
        actions = [
            {"action": "navigate", "url": "https://httpbin.org/html"},
            {"action": "click", "xpath": "//h1"},
            {"action": "wait", "seconds": 2},
            {"action": "screenshot", "filename": "test.png"},
        ]

        with self.client.post(
            "/api/browser/execute",
            json={"actions": actions},
            name="POST /api/browser/execute",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited - too many browser actions")
            else:
                response.failure(f"Browser action failed: {response.status_code}")

    @task(1)
    def cleanup_browser_session(self) -> None:
        """Clean up browser sessions."""
        if self.browser_sessions > 0:
            with self.client.delete(
                "/api/browser/cleanup", name="DELETE /api/browser/cleanup", catch_response=True
            ) as response:
                if response.status_code in [200, 204]:
                    self.browser_sessions = max(0, self.browser_sessions - 1)
                    response.success()
                else:
                    response.failure(f"Browser cleanup failed: {response.status_code}")


# User classes for real application testing
class RealScrapingUser(HttpUser):
    """User that performs actual scraping operations."""

    wait_time = between(2.0, 5.0)  # Realistic timing
    tasks = [RealScrapingTaskSet]
    weight = 3

    def on_start(self) -> None:
        self.client.base_url = APP_BASE_URL


class RealMonitoringUser(HttpUser):
    """User that monitors real application health."""

    wait_time = between(1.0, 3.0)
    tasks = [RealMonitoringTaskSet]
    weight = 2

    def on_start(self) -> None:
        self.client.base_url = APP_BASE_URL


class BrowserStressUser(HttpUser):
    """User that stress tests browser automation."""

    wait_time = between(5.0, 10.0)  # Slower due to browser overhead
    tasks = [BrowserStressTaskSet]
    weight = 1

    def on_start(self) -> None:
        self.client.base_url = APP_BASE_URL


class RealMixedUser(HttpUser):
    """User combining real scraping and monitoring."""

    wait_time = between(1.0, 4.0)
    tasks = {RealScrapingTaskSet: 60, RealMonitoringTaskSet: 30, BrowserStressTaskSet: 10}
    weight = 4

    def on_start(self) -> None:
        self.client.base_url = APP_BASE_URL


# Event handlers for real application insights
@events.request.add_listener
def on_real_request(
    request_type: str, name: str, response_time: float, response_length: int, **kwargs: Any
) -> None:
    """Log performance issues in real application."""
    if "REAL" in name and response_time > 10000:  # 10 second threshold for real app
        print(f"SLOW REAL APP REQUEST: {request_type} {name} took {response_time:.2f}ms")


@events.test_start.add_listener
def on_real_test_start(environment: Any, **kwargs: Any) -> None:
    """Initialize real application load test."""
    print(f"Real application load test starting")
    print(f"App URL: {APP_BASE_URL}")
    print(f"Metrics URL: {METRICS_URL}")
    print(f"Test Mode: {TEST_MODE}")
    print("WARNING: This will test your actual running application!")


@events.test_stop.add_listener
def on_real_test_stop(environment: Any, **kwargs: Any) -> None:
    """Cleanup after real application testing."""
    print("Real application load test completed")

    # Enhanced results for real application testing
    if hasattr(environment, "stats") and environment.stats.entries:
        results = {
            "timestamp": time.time(),
            "test_mode": f"REAL_APP_{TEST_MODE}",
            "app_url": APP_BASE_URL,
            "metrics_url": METRICS_URL,
            "total_requests": sum(stat.num_requests for stat in environment.stats.entries.values()),
            "total_failures": sum(stat.num_failures for stat in environment.stats.entries.values()),
            "failure_rate": environment.stats.total.fail_ratio,
            "avg_response_time": environment.stats.total.avg_response_time,
            "max_response_time": environment.stats.total.max_response_time,
            "requests_per_second": environment.stats.total.current_rps,
            "real_app_metrics": {
                "scraping_requests": sum(
                    1 for name in environment.stats.entries.keys() if "scrape" in name.lower()
                ),
                "monitoring_requests": sum(
                    1
                    for name in environment.stats.entries.keys()
                    if any(x in name.lower() for x in ["health", "ready", "metrics"])
                ),
                "browser_requests": sum(
                    1 for name in environment.stats.entries.keys() if "browser" in name.lower()
                ),
            },
        }

        results_file = Path("real_app_load_test_results.json")
        with results_file.open("w") as f:
            json.dump(results, f, indent=2)
        print(f"Real application results saved to {results_file}")
