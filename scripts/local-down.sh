#!/usr/bin/env bash
# Tear down the local KubeChain Kubernetes (kind) environment.

set -euo pipefail

CLUSTER_NAME="kubechain-local"

echo "=== KubeChain Local Environment Teardown ==="

if ! command -v kind >/dev/null 2>&1; then
  echo "ERROR: 'kind' is not installed."
  exit 1
fi

if kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  echo "Deleting kind cluster '${CLUSTER_NAME}'..."
  kind delete cluster --name "${CLUSTER_NAME}"
  echo "Cluster '${CLUSTER_NAME}' deleted."
else
  echo "kind cluster '${CLUSTER_NAME}' does not exist. Nothing to tear down."
fi
