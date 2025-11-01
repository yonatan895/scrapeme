#!/usr/bin/env python3
"""Standalone test server for load testing.

This script provides a lightweight HTTP server that mimics the health endpoints
of the main ScrapeMe application, allowing load tests to run without requiring
the full application stack.
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

# Simple metrics simulation
METRICS_DATA = """# HELP scrapeme_build_info Build information
# TYPE scrapeme_build_info gauge
scrapeme_build_info{version="2.0.0",python_version="3.11.0"} 1
# HELP scrapeme_requests_total Total number of requests
# TYPE scrapeme_requests_total counter
scrapeme_requests_total{endpoint="/healthz"} 42
scrapeme_requests_total{endpoint="/ready"} 38
scrapeme_requests_total{endpoint="/metrics"} 15
# HELP scrapeme_request_duration_seconds Request duration in seconds
# TYPE scrapeme_request_duration_seconds histogram
scrapeme_request_duration_seconds_bucket{le="0.1"} 85
scrapeme_request_duration_seconds_bucket{le="0.5"} 92
scrapeme_request_duration_seconds_bucket{le="1.0"} 95
scrapeme_request_duration_seconds_bucket{le="+Inf"} 95
scrapeme_request_duration_seconds_sum 12.3
scrapeme_request_duration_seconds_count 95
# HELP scrapeme_health_check_duration_seconds Health check duration
# TYPE scrapeme_health_check_duration_seconds gauge
scrapeme_health_check_duration_seconds{check="config"} 0.001
scrapeme_health_check_duration_seconds{check="ready"} 0.002
"""


class LoadTestHandler(BaseHTTPRequestHandler):
    """HTTP handler for load testing endpoints."""
    
    def log_message(self, format: str, *args: Any) -> None:
        """Override to use Python logging instead of stderr."""
        logging.debug(format % args)

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/healthz":
            self._handle_healthz()
        elif self.path == "/ready":
            self._handle_ready()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/":
            self._handle_root()
        else:
            self._send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def _handle_healthz(self) -> None:
        """Handle liveness probe."""
        response = {
            "status": "healthy",
            "timestamp": self._get_timestamp(),
        }
        self._send_json_response(HTTPStatus.OK, response)

    def _handle_ready(self) -> None:
        """Handle readiness probe."""
        response = {
            "status": "ready",
            "timestamp": self._get_timestamp(),
            "checks": {
                "config": {
                    "status": "healthy",
                    "message": "Configuration loaded successfully",
                    "duration_ms": 1.2
                },
                "ready": {
                    "status": "healthy", 
                    "message": "Application ready",
                    "duration_ms": 0.8
                }
            }
        }
        self._send_json_response(HTTPStatus.OK, response)

    def _handle_metrics(self) -> None:
        """Handle Prometheus metrics endpoint."""
        try:
            metrics_data = METRICS_DATA.encode('utf-8')
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(metrics_data)))
            self.end_headers()
            self.wfile.write(metrics_data)
        except Exception as e:
            logging.exception("Failed to generate metrics")
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Metrics error: {e}")

    def _handle_root(self) -> None:
        """Handle root endpoint."""
        response = {
            "service": "ScrapeMe Load Test Server",
            "version": "2.0.0",
            "timestamp": self._get_timestamp(),
            "endpoints": [
                "/healthz - Liveness probe",
                "/ready - Readiness probe", 
                "/metrics - Prometheus metrics"
            ]
        }
        self._send_json_response(HTTPStatus.OK, response)

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
        error_response = {
            "error": message,
            "code": status_code.value,
            "timestamp": self._get_timestamp(),
        }
        self._send_json_response(status_code, error_response)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


class LoadTestServer:
    """Standalone server for load testing."""
    
    def __init__(self, port: int = 9090, host: str = "localhost") -> None:
        self.port = port
        self.host = host
        self.server: HTTPServer | None = None
        self.should_stop = False
        
    def start(self) -> None:
        """Start the server."""
        self.server = HTTPServer((self.host, self.port), LoadTestHandler)
        
        print(f"Load test server starting on {self.host}:{self.port}")
        print(f"  - Liveness:  http://{self.host}:{self.port}/healthz")
        print(f"  - Readiness: http://{self.host}:{self.port}/ready")
        print(f"  - Metrics:   http://{self.host}:{self.port}/metrics")
        print(f"  - Root:      http://{self.host}:{self.port}/")
        print("Press Ctrl+C to stop")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutdown requested...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the server."""
        if self.server:
            print("Stopping load test server")
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            print("Server stopped")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ScrapeMe Load Test Server")
    parser.add_argument("--port", type=int, default=9090, help="Port to listen on")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = LoadTestServer(port=args.port, host=args.host)
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum: int, frame: Any) -> None:
        print("\nReceived interrupt signal")
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        server.start()
        return 0
    except Exception as e:
        print(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
