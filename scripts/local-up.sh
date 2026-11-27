#!/usr/bin/env bash
# Start the local KubeChain Kubernetes (kind) and Anvil environment.

set -euo pipefail

CLUSTER_NAME="kubechain-local"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIND_CONFIG="${REPO_ROOT}/deploy/local/kind/kind-config.yaml"
NAMESPACES_MANIFEST="${REPO_ROOT}/deploy/local/kind/namespaces.yaml"
ANVIL_DIR="${REPO_ROOT}/deploy/local/anvil"
CHECK_RPC_SCRIPT="${REPO_ROOT}/scripts/check-rpc.py"

echo "=== KubeChain Local Environment Startup ==="

# 1. Verify required CLI tools
for cmd in docker kubectl kind; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "ERROR: Required tool '${cmd}' is not installed."
    echo "See docs/local-development.md for macOS installation instructions."
    exit 1
  fi
done

# 2. Verify Docker daemon is running
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not running or not reachable."
  echo "Please start Docker Desktop (or OrbStack) and retry."
  exit 1
fi

# 3. Create kind cluster if it does not already exist
if kind get clusters | grep -qx "${CLUSTER_NAME}"; then
  echo "kind cluster '${CLUSTER_NAME}' already exists. Reusing existing cluster."
else
  echo "Creating kind cluster '${CLUSTER_NAME}'..."
  kind create cluster --config "${KIND_CONFIG}"
fi

# 4. Switch kubectl context explicitly to the local kind cluster
kubectl config use-context "kind-${CLUSTER_NAME}"

echo "Verifying Kubernetes node readiness..."
kubectl wait --for=condition=Ready nodes --all --timeout=90s

# 5. Apply namespaces and Anvil manifests
echo "Applying KubeChain namespaces..."
kubectl apply -f "${NAMESPACES_MANIFEST}"

echo "Deploying deterministic Anvil node..."
kubectl apply -f "${ANVIL_DIR}/pvc.yaml"
kubectl apply -f "${ANVIL_DIR}/deployment.yaml"
kubectl apply -f "${ANVIL_DIR}/service.yaml"

# 6. Wait for Anvil pod to become Ready
echo "Waiting for Anvil deployment rollout..."
kubectl rollout status deployment/anvil-dev -n kubechain-nodes --timeout=120s

# 7. Run JSON-RPC smoke test
echo "Running JSON-RPC smoke test against http://localhost:8545..."
PYTHON_BIN="${REPO_ROOT}/.venv/bin/python3"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" "${CHECK_RPC_SCRIPT}" --url "http://localhost:8545" --expected-chain-id 31337

echo "=== Local environment is UP and verified ==="
