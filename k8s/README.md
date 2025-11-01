# Kubernetes Deployment for ScrapeMe

This directory contains Kubernetes manifests for deploying the ScrapeMe Selenium automation framework.

## Architecture Overview

The Kubernetes deployment consists of:

- **Application Layer**: Main ScrapeMe application with auto-scaling
- **Browser Infrastructure**: Selenium Grid Hub + Chrome nodes
- **Observability Stack**: Prometheus, Grafana, AlertManager
- **Storage**: Persistent volumes for artifacts, results, and monitoring data
- **Configuration**: ConfigMaps and Secrets for application settings

## Quick Start

```bash
# Deploy everything
make k8s-deploy

# Check status
make k8s-status

# View logs
make k8s-logs

# Access services
make k8s-port-forward
```

## Manual Deployment

```bash
# 1. Create namespace and RBAC
kubectl apply -f k8s/namespace.yaml

# 2. Deploy storage
kubectl apply -f k8s/storage.yaml

# 3. Deploy configuration
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml

# 4. Deploy Selenium Grid
kubectl apply -f k8s/selenium-hub.yaml
kubectl apply -f k8s/selenium-chrome.yaml

# 5. Deploy main application
kubectl apply -f k8s/scrapeme-deployment.yaml
kubectl apply -f k8s/scrapeme-service.yaml

# 6. Deploy monitoring stack
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f k8s/grafana.yaml
kubectl apply -f k8s/alertmanager.yaml

# 7. Enable auto-scaling
kubectl apply -f k8s/hpa.yaml

# 8. Apply network policies (optional)
kubectl apply -f k8s/network-policies.yaml
```

## Directory Structure

```
k8s/
├── README.md                   # This file
├── namespace.yaml              # Namespace, ServiceAccount, RBAC
├── storage.yaml                # PersistentVolumeClaims
├── configmaps.yaml            # Application configuration
├── secrets.yaml               # Sensitive data (template)
├── scrapeme-deployment.yaml   # Main application deployment
├── scrapeme-service.yaml      # Application service
├── selenium-hub.yaml          # Selenium Grid Hub
├── selenium-chrome.yaml       # Chrome node workers
├── prometheus.yaml            # Prometheus server
├── grafana.yaml              # Grafana dashboard server
├── alertmanager.yaml         # AlertManager
├── hpa.yaml                  # Horizontal Pod Autoscaler
├── network-policies.yaml     # Network security policies
└── monitoring/
    ├── servicemonitor.yaml   # Prometheus ServiceMonitor
    └── grafana-dashboards/   # Dashboard ConfigMaps
```

## Configuration

### Secrets

Copy `secrets.yaml` and update with base64-encoded values:

```bash
echo -n "your-username" | base64
echo -n "your-password" | base64
```

### Storage Classes

Update `storage.yaml` with appropriate `storageClassName` for your cluster:

- **Local clusters**: `standard` or `hostpath`
- **Cloud providers**: `gp2` (AWS), `standard` (GCP), `managed-premium` (Azure)
- **NFS**: `nfs-client`

### Resource Requirements

Adjust resource requests/limits in deployment files based on your cluster capacity:

- **Small cluster**: Reduce CPU/memory requests by 50%
- **Large cluster**: Increase limits for better performance
- **Production**: Set guaranteed QoS with equal requests/limits

## Monitoring

### Endpoints

- **Application metrics**: `http://scrapeme-app:9090/metrics`
- **Health checks**: `http://scrapeme-app:9090/healthz`
- **Readiness**: `http://scrapeme-app:9090/ready`
- **Prometheus UI**: Port-forward 9090
- **Grafana UI**: Port-forward 3000

### Port Forwarding

```bash
# Application metrics
kubectl port-forward svc/scrapeme-app 9090:9090 -n scrapeme

# Prometheus
kubectl port-forward svc/prometheus 9091:9090 -n scrapeme

# Grafana
kubectl port-forward svc/grafana 3000:3000 -n scrapeme

# Selenium Grid
kubectl port-forward svc/selenium-hub 4444:4444 -n scrapeme
```

## Troubleshooting

### Common Issues

1. **ImagePullBackOff**: Ensure Docker image is pushed to accessible registry
2. **Pending Pods**: Check node resources and storage class availability
3. **CrashLoopBackOff**: Review logs with `kubectl logs`
4. **Network Issues**: Verify DNS resolution and service discovery

### Debug Commands

```bash
# Pod status
kubectl get pods -n scrapeme -o wide

# Detailed pod info
kubectl describe pod -l app=scrapeme -n scrapeme

# Application logs
kubectl logs -f deployment/scrapeme-app -n scrapeme

# Events
kubectl get events -n scrapeme --sort-by='.firstTimestamp'

# Resource usage
kubectl top pods -n scrapeme
```

### Health Checks

```bash
# Test application health
kubectl exec -it deployment/scrapeme-app -n scrapeme -- curl localhost:9090/healthz

# Check Selenium Grid
kubectl exec -it deployment/selenium-hub -n scrapeme -- curl localhost:4444/status

# Verify configuration
kubectl get configmap scrapeme-config -n scrapeme -o yaml
```

## Security

- All pods run as non-root user (10001)
- Network policies restrict inter-pod communication
- Secrets are base64-encoded (consider external secret management)
- ServiceAccount has minimal required permissions
- Security contexts enforce filesystem group ownership

## Scaling

- **Application**: HPA scales based on CPU/memory usage (2-10 replicas)
- **Selenium Chrome**: Manual scaling based on browser session demand
- **Storage**: Persistent volumes auto-expand if supported by storage class

## Production Considerations

- [ ] Configure external secret management (Vault, AWS Secrets Manager)
- [ ] Set up ingress with TLS termination
- [ ] Implement backup strategy for persistent volumes
- [ ] Configure log aggregation (ELK, Loki)
- [ ] Set up external monitoring (DataDog, New Relic)
- [ ] Implement disaster recovery procedures
- [ ] Configure resource quotas and limits
- [ ] Set up pod security policies/standards
