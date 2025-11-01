from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any

from prometheus_client import start_http_server

from config.loader import load_sites
from config.models import SiteConfig
from core.auth import AuthFlow
from core.browser import BrowserManager
from core.circuit_breaker import CircuitBreakerRegistry, CircuitState
from core.exceptions import AutomationError
from core.metrics import Metrics
from core.scraper import SiteScraper
from core.secrets import EnvSecrets
from core.serialization import dumps_bytes, dumps_str, pretty_dumps
from core.waits import Waiter
from infra.health import HealthRegistry, HealthStatus
from infra.logging_config import configure_logging
from infra.signals import register_shutdown_handler, setup_signal_handlers, shutdown_event

if TYPE_CHECKING:
    from core.capture import CapturedArtifact


def format_error_result(site_name: str, error: Exception) -> dict[str, Any]:
    """Format error with rich context for JSON output."""
    result: dict[str, Any] = {
        "site": site_name,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
    }

    if isinstance(error, AutomationError) and getattr(error, "context", None):
        ctx = error.context  # type: ignore[assignment]
        context_data: dict[str, Any] = {
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
        # Support optional extra mapping if present
        extra = getattr(ctx, "extra", None)
        if extra:
            context_data["extra"] = dict(extra)
        if context_data:
            result["error"]["context"] = context_data

    # Check for dynamically attached artifact using hasattr
    if hasattr(error, "_capture_artifact"):
        from core.capture import CapturedArtifact

        artifact = getattr(error, "_capture_artifact", None)
        if artifact is not None and isinstance(artifact, CapturedArtifact):
            result["error"]["artifacts"] = {
                "context": artifact.context,
                "timestamp": artifact.timestamp,
                "screenshot": str(artifact.screenshot) if artifact.screenshot else None,
                "html": str(artifact.html) if artifact.html else None,
                "url": artifact.url,
            }

    if hasattr(error, "timeout_sec"):
        timeout = getattr(error, "timeout_sec", None)
        if timeout is not None:
            result["error"]["timeout_sec"] = timeout

    return result


def process_site(
    site: SiteConfig,
    *,
    browser: str,
    headless: bool,
    incognito: bool,
    download_dir: Path | None,
    remote_url: str | None,
    chromedriver_path: Path | None,
    artifact_dir: Path | None,
    enable_pooling: bool,
) -> dict[str, Any]:
    """Process single site: login and scrape."""
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
            logger = logging.getLogger(f"site.{site.name}")
            waiter = Waiter(driver, timeout_sec=site.wait_timeout_sec)
            secrets = EnvSecrets()

            if site.login:
                AuthFlow(waiter, logger, secrets, artifact_dir=artifact_dir).login(
                    site.login, site_name=site.name
                )

            scraper = SiteScraper(site, waiter, logger, artifact_dir=artifact_dir)
            data = scraper.run()

            duration = time.monotonic() - start_time
            Metrics.record_scrape_success(site.name, duration)
            circuit_breaker.record_success()

            return {"site": site.name, "data": data}

    except Exception:
        duration = time.monotonic() - start_time
        Metrics.record_scrape_failure(site.name, duration, "UnhandledException")
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
    parser.add_argument(
        "--jsonl", action="store_true", help="Write JSONL output (one line per site)"
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output (slower)")

    args = parser.parse_args()

    setup_signal_handlers()
    logger = configure_logging(args.log_level, args.log_file, args.json_logs)

    start_http_server(args.metrics_port)
    logger.info(f"Metrics server started on port {args.metrics_port}")

    HealthRegistry.register(
        "ready",
        lambda: (HealthStatus.HEALTHY, "OK"),
    )

    artifact_dir = None if args.no_artifacts else args.artifact_dir
    if artifact_dir:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Artifacts enabled: {artifact_dir}")

    try:
        sites = load_sites(args.config)
        logger.info(f"Loaded {len(sites)} sites")
    except Exception:
        logger.exception("Failed to load configuration")
        return 1

    Metrics.build_info.info(
        {
            "version": "2.0.0",
            "python_version": sys.version.split()[0],
        }
    )

    results: list[dict[str, Any]] = []
    max_workers = min(args.max_workers, max(1, len(sites)))

    if args.jsonl:
        try:
            with args.out.open("wb") as fp:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
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

                    for future in as_completed(futures):
                        if shutdown_event.is_set():
                            logger.warning("Shutdown requested")
                            executor.shutdown(wait=False, cancel_futures=True)
                            break

                        site_name = futures[future]
                        try:
                            result = future.result()
                            logger.info(f"✓ Completed: {site_name}")
                        except AutomationError as e:
                            logger.error(f"✗ Automation error on {site_name}: {e}")
                            result = format_error_result(site_name, e)
                        except Exception as e:
                            logger.exception(f"✗ Unhandled error on {site_name}")
                            result = format_error_result(site_name, e)

                        fp.write(dumps_bytes(result))
                        fp.write(b"\n")
        except Exception:
            logger.exception("Failed to write results")
            return 1
        return 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
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

        for future in as_completed(futures):
            if shutdown_event.is_set():
                logger.warning("Shutdown requested")
                executor.shutdown(wait=False, cancel_futures=True)
                break

            site_name = futures[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"✓ Completed: {site_name}")
            except AutomationError as e:
                logger.error(f"✗ Automation error on {site_name}: {e}")
                results.append(format_error_result(site_name, e))
            except Exception as e:
                logger.exception(f"✗ Unhandled error on {site_name}")
                results.append(format_error_result(site_name, e))

    try:
        output_text = pretty_dumps(results) if args.pretty else dumps_str(results)
        args.out.write_text(output_text)
        logger.info(f"Results written to {args.out}")
    except Exception:
        logger.exception("Failed to write results")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
