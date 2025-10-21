"""Production-grade orchestration with observability and fault tolerance."""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from prometheus_client import start_http_server

from core.browser import BrowserManager
from core.waits import Waiter
from core.auth import AuthFlow
from core.scraper import SiteScraper
from core.exceptions import AutomationError
from core.serialization import to_jsonable
from core.secrets import EnvSecrets
from core.metrics import Metrics
from core.circuit_breaker import CircuitBreakerRegistry, CircuitState
from config.loader import load_sites
from infra.logging_config import configure_logging
from infra.signals import setup_signal_handlers, register_shutdown_handler, shutdown_event
from infra.health import HealthRegistry, HealthStatus


def format_error_result(site_name: str, error: Exception) -> dict[str, Any]:
    """Format error with context for JSON output."""
    result: dict[str, Any] = {
        "site": site_name,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
    }
    
    # Add ErrorContext if available
    if isinstance(error, AutomationError) and error.context:
        ctx = error.context
        context_data = {
            k: v
            for k, v in {
                "step": ctx.step_name,
                "field": ctx.field_name,
                "frame": ctx.frame_spec,
                "xpath": ctx.xpath,
                "url": ctx.url,
            }.items()
            if v is not None
        }
        if ctx.extra:
            context_data["extra"] = ctx.extra
        if context_data:
            result["error"]["context"] = context_data
    
    # Add captured artifacts
    if hasattr(error, "_capture_artifact"):
        artifact = error._capture_artifact
        result["error"]["artifacts"] = {
            "context": artifact.context,
            "timestamp": artifact.timestamp,
            "screenshot": str(artifact.screenshot) if artifact.screenshot else None,
            "html": str(artifact.html) if artifact.html else None,
            "url": artifact.url,
        }
    
    # Add timeout info
    if hasattr(error, "timeout_sec") and error.timeout_sec:
        result["error"]["timeout_sec"] = error.timeout_sec
    
    return result


def process_site(
    site,
    *,
    browser: str,
    headless: bool,
    incognito: bool,
    download_dir: Path | None,
    remote_url: str | None,
    chromedriver_path: Path | None,
    artifact_dir: Path | None,
    enable_pooling: bool,
) -> dict:
    """Process single site with circuit breaker and metrics."""
    # Check circuit breaker
    circuit_breaker = CircuitBreakerRegistry.get(site.name)
    if not circuit_breaker.is_call_permitted():
        return {
            "site": site.name,
            "error": {
                "type": "CircuitBreakerOpen",
                "message": f"Circuit breaker is {circuit_breaker.state.name}",
            },
        }
    
    start_time = time.monotonic()
    
    try:
        manager = BrowserManager(
            browser=browser,
            headless=headless,
            incognito=incognito,
            page_load_timeout_sec=site.page_load_timeout_sec,
            download_dir=download_dir,
            remote_url=remote_url,
            chromedriver_path=chromedriver_path,
            enable_pooling=enable_pooling,
        )
        
        with manager.session() as driver:
            logger = configure_logging().bind(site=site.name)
            waiter = Waiter(driver, timeout_sec=site.wait_timeout_sec)
            secrets = EnvSecrets()
            
            # Optional login
            if site.login:
                AuthFlow(waiter, logger, secrets, artifact_dir=artifact_dir).login(
                    site.login, site_name=site.name
                )
            
            # Execute and extract
            scraper = SiteScraper(site, waiter, logger, artifact_dir=artifact_dir)
            data = scraper.run()
            
            # Record success
            duration = time.monotonic() - start_time
            Metrics.record_scrape_success(site.name, duration)
            circuit_breaker.record_success()
            
            return {"site": site.name, "data": data}
    
    except Exception as e:
        duration = time.monotonic() - start_time
        Metrics.record_scrape_failure(site.name, duration, type(e).__name__)
        circuit_breaker.record_failure()
        raise


def main() -> int:
    """CLI entry point with full observability."""
    parser = argparse.ArgumentParser(
        description="Production Selenium automation with observability"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--browser", choices=["chrome", "firefox"], default="chrome")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--incognito", action="store_true")
    parser.add_argument("--download-dir", type=Path)
    parser.add_argument("--remote-url")
    parser.add_argument("--chromedriver-path", type=Path)
    parser.add_argument("--artifact-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--out", type=Path, default=Path("results.json"))
    parser.add_argument("--log-file", type=Path)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--json-logs", action="store_true")
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--no-artifacts", action="store_true")
    parser.add_argument("--enable-pooling", action="store_true")
    parser.add_argument("--metrics-port", type=int, default=9090)
    
    args = parser.parse_args()
    
    # Setup infrastructure
    setup_signal_handlers()
    logger = configure_logging(args.log_level, args.log_file, args.json_logs)
    
    # Start metrics server
    start_http_server(args.metrics_port)
    logger.info("metrics_server_started", port=args.metrics_port)
    
    # Register health checks
    HealthRegistry.register(
        "database",
        lambda: (HealthStatus.HEALTHY, "OK"),
    )
    
    # Artifact directory
    artifact_dir = None if args.no_artifacts else args.artifact_dir
    if artifact_dir:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        logger.info("artifacts_enabled", path=str(artifact_dir))
    
    # Load configuration
    try:
        sites = load_sites(args.config)
        logger.info("config_loaded", site_count=len(sites))
    except Exception as e:
        logger.exception("config_load_failed", error=str(e))
        return 1
    
    # Set build info
    Metrics.build_info.info({
        "version": "2.0.0",
        "python_version": sys.version.split()[0],
    })
    
    # Process sites with graceful shutdown support
    results = []
    max_workers = min(args.max_workers, max(1, len(sites)))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        futures = {
            executor.submit(
                process_site,
                site,
                browser=args.browser,
                headless=args.headless,
                incognito=args.incognito,
                download_dir=args.download_dir,
                remote_url=args.remote_url,
                chromedriver_path=args.chromedriver_path,
                artifact_dir=artifact_dir,
                enable_pooling=args.enable_pooling,
            ): site.name
            for site in sites
        }
        
        # Process completions with shutdown check
        for future in as_completed(futures):
            if shutdown_event.is_set():
                logger.warning("shutdown_requested", pending=len(futures))
                executor.shutdown(wait=False, cancel_futures=True)
                break
            
            site_name = futures[future]
            try:
                result = future.result()
                results.append(result)
                logger.info("site_completed", site=site_name)
            except AutomationError as e:
                logger.error("site_failed", site=site_name, error=str(e))
                results.append(format_error_result(site_name, e))
            except Exception as e:
                logger.exception("site_error", site=site_name)
                results.append(format_error_result(site_name, e))
    
    # Write results
    try:
        output = json.dumps(to_jsonable(results), indent=2, ensure_ascii=False)
        args.out.write_text(output, encoding="utf-8")
        logger.info("results_written", path=str(args.out))
    except Exception as e:
        logger.exception("results_write_failed", error=str(e))
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
