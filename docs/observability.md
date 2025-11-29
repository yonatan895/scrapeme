# Observability & Health

The application provides comprehensive observability through Prometheus metrics, health endpoints, and structured logging.

## Metrics

Prometheus metrics are exposed on the port specified by `--metrics-port` (default: 9090) at the `/metrics` endpoint.

### Counters

| Metric Name | Labels | Description |
|-------------|--------|-------------|
| `selenium_scrapes_total` | `site`, `status` | Total number of scrape attempts (status: "success", "failure"). |
| `selenium_login_attempts_total` | `site`, `status` | Total login attempts. |
| `selenium_steps_executed_total` | `site`, `step`, `status` | Total steps executed within a site flow. |
| `selenium_fields_extracted_total` | `site`, `step`, `field` | Total data fields successfully extracted. |
| `selenium_retries_total` | `site`, `exception_type` | Total retry attempts triggered by failures. |
| `selenium_circuit_breaker_state_changes_total` | `site`, `from_state`, `to_state` | Number of circuit breaker state transitions. |

### Histograms

| Metric Name | Labels | Buckets (sec) | Description |
|-------------|--------|---------------|-------------|
| `selenium_scrape_duration_seconds` | `site` | 1, 5, 10, 30, 60, 120, 300 | Total time spent scraping a site. |
| `selenium_step_duration_seconds` | `site`, `step` | 0.1, 0.5, 1, 2, 5, 10, 30 | Time spent executing a single step. |
| `selenium_wait_duration_seconds` | `wait_type` | 0.1, 0.5, 1, 2, 5, 10, 20 | Duration of explicit waits. |
| `selenium_page_load_duration_seconds` | `site` | 0.5, 1, 2, 5, 10, 30 | Time taken for page loads. |

### Gauges

| Metric Name | Labels | Description |
|-------------|--------|-------------|
| `selenium_active_sessions` | None | Current number of active WebDriver sessions. |
| `selenium_circuit_breaker_failure_rate` | `site` | Current calculated failure rate (0.0 - 1.0) for the circuit breaker. |
| `selenium_memory_usage_bytes` | None | Current memory usage of the application. |

### Info

| Metric Name | Description |
|-------------|-------------|
| `selenium_automation_build` | Build information (version, python_version). |

## Health Endpoints

Provided by `infra/server.py` for liveness and readiness probes.

- **`/healthz` (Liveness)**: Returns `200 OK` if the metrics server is running. Used to restart the pod if the process hangs.
- **`/ready` (Readiness)**: Returns `200 OK` if the application is ready to accept work. Checks:
    - **`config`**: Validates that `sites.yaml` was successfully loaded.
    - **`ready`**: Basic application readiness.

## Logging

Logging is configured via `infra/logging_config`.

- **Structured JSON**: Enable with `--json-logs` for machine-parsable logs (ideal for ELK/Splunk).
- **Human-readable**: Default format for local development.
- **Log Levels**: Control verbosity with `--log-level` (default: INFO).

Logs include correlation IDs and context (site name, step name) where applicable to trace execution flow.
