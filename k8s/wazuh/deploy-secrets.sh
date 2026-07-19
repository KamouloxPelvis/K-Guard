#!/bin/bash
# K-Guard Infrastructure - Deployment Script
# Description: Deploys secrets and the entire Wazuh stack.

# 1. Validation
if [ -z "$1" ]; then
  echo "Error: You must provide a password as an argument."
  exit 1
fi

# 2. Deploy Secret
kubectl create secret generic wazuh-indexer-credentials \
  -n k-guard \
  --from-literal=admin-password="$1" \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Apply infrastructure manifests
echo "Applying Wazuh manifests..."
kubectl apply -f .

# 4. Success message
echo "Deployment initiated successfully!"
echo "Wait for pods to be ready: 'kubectl get pods -n wazuh'"
