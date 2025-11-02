# Security Incident Response Runbook

## Immediate Response

### Container Security Breach
```bash
# Immediately isolate affected pods
kubectl patch deployment scrapeme-app -p '{"spec":{"replicas":0}}'

# Create network isolation
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: emergency-isolation
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: scrapeme-app
  policyTypes: ["Ingress", "Egress"]
EOF

# Collect forensic data
kubectl logs deployment/scrapeme-app --all-containers --previous > incident-logs.txt
kubectl describe pods -l app.kubernetes.io/name=scrapeme-app > incident-pods.txt
```

### Secret Compromise
```bash
# Rotate compromised secrets immediately
kubectl delete secret scrapeme-secrets
# Trigger External Secrets refresh
kubectl annotate externalsecret scrapeme-secrets force-sync=true

# Update Vault secrets
vault kv put secret/scrapeme/credentials username=new_user password=new_password
```

### Policy Violation Detection
```bash
# Check policy violations
kubectl get events --field-selector reason=PolicyViolation
kubectl get cpol,pol -A  # Check Kyverno policies

# Review admission controller logs
kubectl logs -n kyverno deployment/kyverno-admission-controller
```

## Investigation Procedures

### Audit Log Analysis
```bash
# Search audit logs for suspicious activity
kubectl logs -n kube-system kube-apiserver | grep "user=\|verb=\|objectRef"

# Check RBAC usage
kubectl auth can-i --list --as=system:serviceaccount:scrapeme:scrapeme-app
```

### Container Runtime Analysis
```bash
# Check for runtime security violations
falco -k 8s-audit.yaml -r falco-rules.yaml

# Analyze container behavior
kubectl exec -it deployment/scrapeme-app -- ps aux
kubectl exec -it deployment/scrapeme-app -- netstat -tulpn
```

## Recovery Steps

1. **Contain**: Isolate affected workloads
2. **Investigate**: Collect logs and forensic data
3. **Remediate**: Apply security patches/updates
4. **Recover**: Restore from clean backup if needed
5. **Monitor**: Enhanced monitoring for recurrence

## Prevention Measures

- Regular security scans via Trivy/Snyk
- Policy enforcement with Kyverno/OPA
- Network segmentation with NetworkPolicies
- Least-privilege RBAC
- Immutable container images with digests
- External secret rotation