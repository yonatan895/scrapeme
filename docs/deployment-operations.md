# Deployment Operations Guide

Complete guide for managing ScrapeMe deployments with Kubernetes, Helm, and ArgoCD.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Deploying](#deploying)
- [Updating](#updating)
- [Scaling](#scaling)
- [Restarting](#restarting)
- [Stopping](#stopping)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)

---

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| kubectl | 1.23+ | `curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"` |
| Helm | 3.0+ | `curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \| bash` |
| kind | 0.20+ | `curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.25.0/kind-linux-amd64` |
| ArgoCD CLI | 2.0+ | `curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64` |

### Verify Installation

```bash
kubectl version --client
helm version
kind version
argocd version --client
```

---

## Initial Setup

### 1. Create Local Cluster (Development)

```bash
# Create cluster with kind
kind create cluster --name scrapeme

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### 2. Install ArgoCD (Optional)

```bash
# Create namespace and install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port-forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Access at: https://localhost:8080 (user: admin)
```

### 3. Update Helm Dependencies

```bash
cd charts/scrapeme
helm dependency update
```

---

## Deploying

### Option A: Deploy with Helm (Direct)

```bash
# Default deployment
helm install scrapeme charts/scrapeme \
  --namespace scrapeme \
  --create-namespace

# Production deployment with custom values
helm install scrapeme charts/scrapeme \
  --namespace scrapeme \
  --create-namespace \
  -f argocd/values-production.yaml

# Dry-run (preview without applying)
helm install scrapeme charts/scrapeme \
  --namespace scrapeme \
  --dry-run --debug
```

### Option B: Deploy with ArgoCD (GitOps)

```bash
# Apply ArgoCD Application
kubectl apply -f argocd/application.yaml

# Check sync status
argocd app get scrapeme-prod

# Force sync if needed
argocd app sync scrapeme-prod

# Watch sync progress
argocd app get scrapeme-prod --refresh
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n scrapeme -w

# Check all resources
kubectl get all -n scrapeme

# Check logs
kubectl logs -n scrapeme -l app.kubernetes.io/name=scrapeme -f
```

---

## Updating

### Update with Helm

```bash
# Update values and upgrade
helm upgrade scrapeme charts/scrapeme \
  --namespace scrapeme \
  -f argocd/values-production.yaml

# Upgrade with specific image tag
helm upgrade scrapeme charts/scrapeme \
  --namespace scrapeme \
  --set image.tag=2.1.0

# Rollback to previous release
helm rollback scrapeme -n scrapeme

# Rollback to specific revision
helm history scrapeme -n scrapeme
helm rollback scrapeme 2 -n scrapeme
```

### Update with ArgoCD

```bash
# Sync to latest (pulls from Git)
argocd app sync scrapeme-prod

# Hard refresh (re-fetch manifests)
argocd app get scrapeme-prod --hard-refresh

# Sync with prune (remove orphaned resources)
argocd app sync scrapeme-prod --prune
```

### Update Configuration Only

```bash
# Update sites.yaml content
kubectl create configmap scrapeme-config \
  --from-file=sites.yaml=config/sites.yaml \
  -n scrapeme \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up config
kubectl rollout restart deployment/scrapeme -n scrapeme
```

### Update Secrets

```bash
# Update credentials
kubectl create secret generic scrapeme-secrets \
  --from-literal=SITE_USERNAME=newuser \
  --from-literal=SITE_PASSWORD=newpass \
  -n scrapeme \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart to apply
kubectl rollout restart deployment/scrapeme -n scrapeme
```

---

## Scaling

### Manual Scaling

```bash
# Scale replicas
kubectl scale deployment scrapeme -n scrapeme --replicas=3

# With Helm
helm upgrade scrapeme charts/scrapeme \
  --namespace scrapeme \
  --set deployment.replicaCount=3
```

### Enable Autoscaling

```bash
# Enable HPA via Helm
helm upgrade scrapeme charts/scrapeme \
  --namespace scrapeme \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=10

# Check HPA status
kubectl get hpa -n scrapeme
kubectl describe hpa scrapeme -n scrapeme
```

### Scale Selenium Grid

```bash
# Scale Chrome nodes
kubectl scale deployment scrapeme-selenium-grid-chrome -n scrapeme --replicas=5
```

---

## Restarting

### Rolling Restart (Zero Downtime)

```bash
# Restart deployment
kubectl rollout restart deployment/scrapeme -n scrapeme

# Watch progress
kubectl rollout status deployment/scrapeme -n scrapeme
```

### Force Restart (All Pods)

```bash
# Delete all pods (will be recreated)
kubectl delete pods -n scrapeme -l app.kubernetes.io/name=scrapeme
```

### Restart Specific Pod

```bash
# Get pod name
kubectl get pods -n scrapeme

# Delete specific pod
kubectl delete pod scrapeme-xxxx-yyyy -n scrapeme
```

### Restart Dependencies

```bash
# Restart Selenium Grid
kubectl rollout restart deployment -n scrapeme -l app.kubernetes.io/name=selenium-grid

# Restart Redis
kubectl rollout restart statefulset/scrapeme-redis-master -n scrapeme

# Restart all
kubectl rollout restart deployment,statefulset -n scrapeme
```

---

## Stopping

### Pause Deployment (Scale to Zero)

```bash
# Scale to zero (keeps resources)
kubectl scale deployment scrapeme -n scrapeme --replicas=0

# Resume
kubectl scale deployment scrapeme -n scrapeme --replicas=2
```

### Uninstall with Helm

```bash
# Uninstall (keeps namespace and PVCs)
helm uninstall scrapeme -n scrapeme

# Full cleanup including PVCs
helm uninstall scrapeme -n scrapeme
kubectl delete pvc -n scrapeme --all
kubectl delete namespace scrapeme
```

### Disable in ArgoCD

```bash
# Delete ArgoCD application (keeps resources)
kubectl delete application scrapeme-prod -n argocd

# Delete with cascade (removes all resources)
argocd app delete scrapeme-prod --cascade
```

### Stop Local Cluster

```bash
# Delete kind cluster
kind delete cluster --name scrapeme
```

---

## Troubleshooting

### Check Pod Status

```bash
# List pods with status
kubectl get pods -n scrapeme -o wide

# Describe failing pod
kubectl describe pod scrapeme-xxxx-yyyy -n scrapeme

# Check events
kubectl get events -n scrapeme --sort-by='.lastTimestamp'
```

### View Logs

```bash
# Current logs
kubectl logs -n scrapeme -l app.kubernetes.io/name=scrapeme

# Follow logs
kubectl logs -n scrapeme -l app.kubernetes.io/name=scrapeme -f

# Previous container logs (after crash)
kubectl logs -n scrapeme <pod-name> --previous

# All containers in pod
kubectl logs -n scrapeme <pod-name> --all-containers
```

### Debug Pod

```bash
# Shell into running pod
kubectl exec -it -n scrapeme <pod-name> -- /bin/bash

# Run debug container
kubectl debug -n scrapeme <pod-name> -it --image=busybox

# Port-forward for local testing
kubectl port-forward -n scrapeme svc/scrapeme 9090:9090
```

### Common Issues

#### Pod CrashLoopBackOff

```bash
# Check logs
kubectl logs -n scrapeme <pod-name> --previous

# Common causes:
# - Missing secrets: kubectl get secrets -n scrapeme
# - Bad config: kubectl get configmap scrapeme-config -n scrapeme -o yaml
# - Resource limits: kubectl describe pod <pod-name> -n scrapeme | grep -A5 "Resources"
```

#### ImagePullBackOff

```bash
# Check image name
kubectl describe pod <pod-name> -n scrapeme | grep "Image:"

# Check registry credentials
kubectl get secrets -n scrapeme | grep regcred

# Create registry secret
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=USERNAME \
  --docker-password=TOKEN \
  -n scrapeme
```

#### Selenium Connection Failed

```bash
# Check Selenium Grid
kubectl get pods -n scrapeme -l app=selenium-hub
kubectl logs -n scrapeme -l app=selenium-hub

# Test connectivity
kubectl exec -it -n scrapeme <scrapeme-pod> -- curl http://scrapeme-selenium-grid-hub:4444/status
```

#### ArgoCD Sync Failed

```bash
# Check application status
argocd app get scrapeme-prod

# View sync errors
argocd app sync scrapeme-prod --dry-run

# Force refresh
argocd app get scrapeme-prod --hard-refresh

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### Resource Issues

```bash
# Check resource usage
kubectl top pods -n scrapeme
kubectl top nodes

# Check resource quotas
kubectl describe resourcequota -n scrapeme

# Increase limits
helm upgrade scrapeme charts/scrapeme -n scrapeme \
  --set resources.limits.memory=1Gi \
  --set resources.limits.cpu=1000m
```

---

## Monitoring

### Health Endpoints

```bash
# Port-forward
kubectl port-forward -n scrapeme svc/scrapeme 9090:9090

# Check health
curl http://localhost:9090/healthz
curl http://localhost:9090/ready
curl http://localhost:9090/metrics
```

### Prometheus Metrics

```bash
# Enable ServiceMonitor
helm upgrade scrapeme charts/scrapeme -n scrapeme \
  --set monitoring.serviceMonitor.enabled=true

# Query metrics
kubectl port-forward -n scrapeme svc/scrapeme 9090:9090
curl -s http://localhost:9090/metrics | grep scrape
```

### ArgoCD Dashboard

```bash
# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open: https://localhost:8080
# Login: admin / <initial-password>
```

---

## Backup & Recovery

### Backup Helm Release

```bash
# Export current values
helm get values scrapeme -n scrapeme -o yaml > backup-values.yaml

# Export all manifests
helm get manifest scrapeme -n scrapeme > backup-manifests.yaml
```

### Backup Configuration

```bash
# Backup ConfigMap
kubectl get configmap scrapeme-config -n scrapeme -o yaml > backup-config.yaml

# Backup Secrets (base64 encoded)
kubectl get secret scrapeme-secrets -n scrapeme -o yaml > backup-secrets.yaml
```

### Restore

```bash
# Restore from backup values
helm install scrapeme charts/scrapeme \
  --namespace scrapeme \
  --create-namespace \
  -f backup-values.yaml

# Apply config backup
kubectl apply -f backup-config.yaml
kubectl apply -f backup-secrets.yaml
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Deploy | `helm install scrapeme charts/scrapeme -n scrapeme --create-namespace` |
| Upgrade | `helm upgrade scrapeme charts/scrapeme -n scrapeme` |
| Rollback | `helm rollback scrapeme -n scrapeme` |
| Restart | `kubectl rollout restart deployment/scrapeme -n scrapeme` |
| Scale | `kubectl scale deployment scrapeme -n scrapeme --replicas=3` |
| Logs | `kubectl logs -n scrapeme -l app.kubernetes.io/name=scrapeme -f` |
| Shell | `kubectl exec -it -n scrapeme <pod> -- /bin/bash` |
| Stop | `kubectl scale deployment scrapeme -n scrapeme --replicas=0` |
| Uninstall | `helm uninstall scrapeme -n scrapeme` |
| Sync (ArgoCD) | `argocd app sync scrapeme-prod` |
