from __future__ import annotations

import json
import os
from pathlib import Path

from locust import HttpUser, between, events, task

# This Locust test drives the runner via HTTP by invoking a lightweight Flask wrapper is not present.
# Instead, we will simulate load by calling a tiny endpoint if user exposes one, else we perform headless GETs
# against the example target (quotes.toscrape.com) to exercise network and parsing paths.
# For full-system load, prefer `make compose-up` and hit the /metrics endpoint concurrently.

TARGET_BASE = os.getenv("LOAD_BASE_URL", "http://quotes.toscrape.com")


class QuotesUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def homepage(self):
        with self.client.get("/", name="GET /", catch_response=True) as resp:
            if resp.status_code != 200 or b"quote" not in resp.content:
                resp.failure(f"unexpected status/content: {resp.status_code}")

    @task(1)
    def page2(self):
        with self.client.get("/page/2/", name="GET /page/2", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"status {resp.status_code}")

    def on_start(self):
        # Override host at runtime to allow pointing to arbitrary targets
        self.host = TARGET_BASE
