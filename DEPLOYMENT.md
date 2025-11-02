# Helm + Argo CD deployment for ScrapeMe

This implementation replaces raw manifests/Kustomize with Helm charts, managed by Argo CD (GitOps).

## Overview
- charts/scrapeme: umbrella chart (depends on subcharts)
- charts/scrapeme-app: main application (Deployment, Service, HPA, PDB, RBAC, NP, ConfigMap)
- charts/selenium-grid: hub + chrome nodes with HPA and /dev/shm tuning
- charts/observability: basic Prometheus/Grafana/Alertmanager (swap to kube-prometheus-stack in enterprises)
- deploy/environments: values per environment (dev/staging/prod)
- deploy/argo: Argo CD Applications that install the umbrella chart with env values

## Quick start

### Dev (cluster with Argo CD installed)
```bash
# Apply dev Application (assumes Argo CD in argocd ns)
kubectl apply -f deploy/argo/application-dev.yaml
# Watch sync in Argo UI or via CLI
```

### Helm locally (without Argo)
```bash
helm upgrade --install scrapeme charts/scrapeme -n scrapeme-dev \
  --create-namespace -f deploy/environments/dev.yaml
```

## Best practices included
- Non-root pods, seccomp RuntimeDefault, no privilege escalation, drop ALL caps
- NetworkPolicies least-privilege
- HPA with sensible behavior; PDB for availability
- Topology spreading and anti-affinity (configurable)
- Immutable image tags in staging/prod values
- Separate artifacts/results PVCs (RWX) with configurable storageClassName
- Optional ServiceMonitor integration

## Production notes
- Prefer kube-prometheus-stack for enterprise monitoring; wire ServiceMonitor via values
- Consider Argo Rollouts for canary/blue/green rollouts
- External Secrets Operator or SealedSecrets for secret material
- Image signing and admission policies (Kyverno/OPA Gatekeeper)

## Maintenance
- Bump subchart versions in charts/scrapeme/Chart.yaml
- Tag app images (avoid latest) and update deploy/environments/*.yaml
- Use Argo CD automated sync for dev/staging; require manual for prod
