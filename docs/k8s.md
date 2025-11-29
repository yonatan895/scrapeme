# Kubernetes Deployment

This project includes a comprehensive Helm chart for deploying the application on Kubernetes, compatible with ArgoCD.

## Prerequisites

- Kubernetes 1.23+
- Helm 3.0+
- (Optional) ArgoCD
- (Optional) Prometheus Operator (for ServiceMonitor)

## Helm Chart

The chart is located in `charts/scrapeme`.

### Installation

```bash
# Install dependencies (Selenium Grid)
helm dependency update charts/scrapeme

# Install chart
helm install scrapeme charts/scrapeme \
  --namespace scrapeme \
  --create-namespace \
  --values charts/scrapeme/values.yaml
```

### Configuration

Key configuration options in `values.yaml`:

| Key | Description | Default |
|-----|-------------|---------|
| `mode` | Execution mode: `deployment` (loop) or `cronjob` (schedule) | `deployment` |
| `deployment.loopInterval` | Interval in seconds for the loop mode | `300` |
| `cronjob.schedule` | Cron schedule for the cronjob mode | `*/10 * * * *` |
| `config.sites` | YAML content for `sites.yaml` | (Example provided) |
| `selenium-grid.enabled` | Deploy a dedicated Selenium Grid | `true` |
| `selenium.hubUrl` | External Selenium Hub URL (if grid disabled) | `""` |
| `monitoring.serviceMonitor.enabled` | Create ServiceMonitor for Prometheus | `false` |

## ArgoCD

To deploy using ArgoCD, apply the manifest in `argocd/application.yaml`.

```bash
kubectl apply -f argocd/application.yaml
```

Make sure to customize `argocd/values-production.yaml` and commit it to your repository (or use an external values file).

## Architecture

The deployment consists of:

1.  **ScrapeMe Pods**:
    -   Run as a `Deployment` (long-running with loop) or `CronJob`.
    -   Mount configuration from `ConfigMap`.
    -   Expose metrics on port 9090.
2.  **Selenium Grid** (Optional):
    -   Deployed as a subchart or external service.
    -   Hub and Chrome/Firefox nodes.
3.  **Observability**:
    -   Prometheus ServiceMonitor scrapes `/metrics`.
    -   Liveness/Readiness probes ensure availability.

## Scaling

-   **Vertical Scaling**: Adjust `resources.requests` and `resources.limits`.
-   **Horizontal Scaling**:
    -   Increase `deployment.replicaCount`.
    -   **Note**: Each replica processes the *entire* `sites.yaml` configuration. To shard the workload, you must split the configuration into multiple releases or implement a work-queue architecture (future feature).
