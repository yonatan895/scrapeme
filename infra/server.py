"""HTTP server for health checks and metrics."""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from infra.health import HealthRegistry, HealthStatus

logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks and metrics."""

    def log_message(self, format: str, *args: Any) -> None:
        """Override to use Python logging instead of stderr."""
        logger.debug(format % args)

    def do_GET(self) -> None:
        """Handle GET requests for health checks and metrics."""
        if self.path == "/healthz":
            self._handle_healthz()
        elif self.path == "/ready":
            self._handle_ready()
        elif self.path == "/metrics":
            self._handle_metrics()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def _handle_healthz(self) -> None:
        """Handle liveness probe - always healthy if server is responding."""
        response = {"status": "healthy", "timestamp": self._get_timestamp()}
        self._send_json_response(HTTPStatus.OK, response)

    def _handle_ready(self) -> None:
        """Handle readiness probe - check all registered health checks."""
        results = HealthRegistry.check_all()
        
        if not results:
            # No health checks registered - consider ready
            response = {"status": "ready", "timestamp": self._get_timestamp()}
            self._send_json_response(HTTPStatus.OK, response)
            return

        # Check if all health checks pass
        all_healthy = all(r.status == HealthStatus.HEALTHY for r in results.values())
        status_code = HTTPStatus.OK if all_healthy else HTTPStatus.SERVICE_UNAVAILABLE
        
        response = {
            "status": "ready" if all_healthy else "not_ready",
            "timestamp": self._get_timestamp(),
            "checks": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "duration_ms": result.duration_ms,
                }
                for name, result in results.items()
            },
        }
        
        self._send_json_response(status_code, response)

    def _handle_metrics(self) -> None:
        """Handle Prometheus metrics endpoint."""
        try:
            metrics_data = generate_latest()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.send_header("Content-Length", str(len(metrics_data)))
            self.end_headers()
            self.wfile.write(metrics_data)
        except Exception as e:
            logger.exception("Failed to generate metrics")
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Metrics error: {e}")

    def _send_json_response(self, status_code: HTTPStatus, data: dict[str, Any]) -> None:
        """Send JSON response with proper headers."""
        response_body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(response_body)

    def _send_error(self, status_code: HTTPStatus, message: str) -> None:
        """Send error response."""
        response = {
            "error": message,
            "code": status_code.value,
            "timestamp": self._get_timestamp(),
        }
        self._send_json_response(status_code, response)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


class HealthServer:
    """HTTP server for health checks and metrics."""

    def __init__(self, port: int = 9090, host: str = "0.0.0.0") -> None:
        self.port = port
        self.host = host
        self.server: HTTPServer | None = None
        self.thread: Thread | None = None

    def start(self) -> None:
        """Start the health server in a background thread."""
        if self.server is not None:
            logger.warning("Health server already started")
            return

        self.server = HTTPServer((self.host, self.port), HealthHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        logger.info(f"Health server started on {self.host}:{self.port}")
        logger.info(f"  - Liveness:  http://{self.host}:{self.port}/healthz")
        logger.info(f"  - Readiness: http://{self.host}:{self.port}/ready")
        logger.info(f"  - Metrics:   http://{self.host}:{self.port}/metrics")

    def stop(self) -> None:
        """Stop the health server."""
        if self.server is None:
            return

        logger.info("Stopping health server")
        self.server.shutdown()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        self.server = None
        self.thread = None
        logger.info("Health server stopped")