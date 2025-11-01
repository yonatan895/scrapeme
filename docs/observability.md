# Observability & Health

## Metrics
- Prometheus metrics on --metrics-port (default 9090)
- See core/metrics for counters/histograms, build_info labels in runner

References:
- Prometheus overview: https://prometheus.io/docs/introduction/overview/
- Prometheus exposition formats: https://prometheus.io/docs/instrumenting/exposition_formats/

## Health endpoints
Provided by infra/server.py:
- /healthz — liveness (200 OK if server is up)
- /ready   — readiness with detailed checks

Checks registered via infra/health.HealthRegistry, e.g.:
- config load check in runner (validates sites.yaml)
