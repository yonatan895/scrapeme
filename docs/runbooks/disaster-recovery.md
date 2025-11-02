# Enterprise Disaster Recovery Runbook

## Overview
This runbook covers disaster recovery procedures for the ScrapeMe Kubernetes platform.

## Backup Procedures

### Velero Backup Verification
```bash
# Check backup status
velero backup get
velero backup describe scrapeme-backup-<timestamp>

# Verify backup contents
velero backup logs scrapeme-backup-<timestamp>
```

### Manual Backup
```bash
# Create immediate backup
velero backup create scrapeme-manual-$(date +%Y%m%d-%H%M%S) \
  --include-namespaces scrapeme,scrapeme-staging \
  --storage-location default \
  --ttl 720h0m0s
```

## Restore Procedures

### Full Namespace Restore
```bash
# List available backups
velero backup get

# Restore from backup
velero restore create scrapeme-restore-$(date +%Y%m%d-%H%M%S) \
  --from-backup scrapeme-backup-<timestamp> \
  --namespace-mappings scrapeme:scrapeme-restored

# Monitor restore progress
velero restore get
velero restore describe scrapeme-restore-<timestamp>
```

### Selective Resource Restore
```bash
# Restore specific resources only
velero restore create scrapeme-pvc-restore \
  --from-backup scrapeme-backup-<timestamp> \
  --include-resources persistentvolumeclaims \
  --namespace-mappings scrapeme:scrapeme
```

## Recovery Scenarios

### Scenario 1: Complete Cluster Loss
1. Provision new cluster with same storage backend
2. Install Velero with same storage configuration
3. Restore namespaces and persistent volumes
4. Verify application functionality
5. Update DNS/ingress as needed

### Scenario 2: Namespace Corruption
1. Create backup of current state (if possible)
2. Delete corrupted namespace
3. Restore from latest known-good backup
4. Verify data integrity

### Scenario 3: Data Corruption
1. Stop application pods to prevent further corruption
2. Restore PVCs from backup
3. Restart application pods
4. Validate data consistency

## Contact Information
- Platform Team: platform-team@company.com
- On-call: +1-555-ONCALL
- Escalation: cto@company.com