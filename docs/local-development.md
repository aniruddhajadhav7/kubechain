# KubeChain Local Infrastructure Environment (Phase 1)

This guide explains how to install local prerequisites on macOS and run the reproducible **kind + Anvil** Kubernetes environment for KubeChain.

---

## 1. Architectural Notes & Anvil Limitations

Before launching the local cluster, keep these engineering boundaries in mind:

- **Anvil is a local development EVM node**, not a production Ethereum execution/consensus client (such as Geth + Lighthouse).
- **Single-node state**: Multiple independently started Anvil pods **do not** peer over DevP2P or share blockchain state. Therefore, `deploy/local/anvil/deployment.yaml` runs `replicas: 1`.
- **Persistence model**: Unlike Geth or Besu, which store Merkle-Patricia Trie data in PebbleDB/RocksDB, Anvil operates in memory. We attach a `1Gi` `PersistentVolumeClaim` (`anvil-dev-state`) at `/data` and pass `--state /data/anvil-state.json --state-interval 10` so local development state survives pod restarts. If you want a fresh chain on every restart, you can delete the PVC or switch the volume to `emptyDir`.
- **Blockchain-aware health probes**: The Anvil deployment uses `cast chain-id` and `cast block-number` for `startupProbe`, `livenessProbe`, and `readinessProbe` rather than a TCP socket check, ensuring the JSON-RPC server is actively answering EVM queries.

---

## 2. macOS Installation Requirements

Install the required tooling on macOS using [Homebrew](https://brew.sh/):

### A. Docker Runtime
Install **Docker Desktop** (or **OrbStack**):
```bash
brew install --cask docker
```
After installation, launch **Docker Desktop** from `/Applications` and verify the daemon is running:
```bash
docker info
```

### B. Kubernetes CLI (`kubectl`), `kind`, and `Helm`
```bash
brew install kubectl kind helm
```
Verify installations:
```bash
kubectl version --client
kind version
helm version
```

### C. Foundry / Anvil (Optional Host CLI)
Anvil runs inside Kubernetes via `ghcr.io/foundry-rs/foundry:latest`, so host installation is optional. However, having `cast` and `anvil` locally is useful for debugging:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
anvil --version
```

---

## 3. Cluster Topology

The `kind` configuration ([deploy/local/kind/kind-config.yaml](../deploy/local/kind/kind-config.yaml)) provisions a 2-node cluster (`kubechain-local`):
- `control-plane` (with host port mappings)
- `worker`

### Namespaces ([deploy/local/kind/namespaces.yaml](../deploy/local/kind/namespaces.yaml))
- `kubechain-system`: Reserved for the KubeChain Operator, RPC Gateway, Redis, and observability stack.
- `kubechain-nodes`: Hosts blockchain node workloads (`anvil-dev`).

### Port Mappings
| Service | Kubernetes NodePort | Host Port | Local URL |
| :--- | :--- | :--- | :--- |
| Anvil JSON-RPC | `30545` | `8545` | `http://localhost:8545` |
| Gateway (Future) | `30800` | `8000` | `http://localhost:8000` |
| Metrics (Future) | `30090` | `9090` | `http://localhost:9090` |

Internal cluster DNS for the Anvil node is:
`http://anvil-dev-rpc.kubechain-nodes.svc.cluster.local:8545`

---

## 4. Starting & Verifying the Environment

### Start the cluster and Anvil node
```bash
./scripts/local-up.sh
```
This script:
1. Validates `docker`, `kubectl`, `kind`, and the Docker daemon.
2. Creates the `kubechain-local` cluster if not already present.
3. Applies namespaces and Anvil manifests (`pvc.yaml`, `deployment.yaml`, `service.yaml`).
4. Waits for the Anvil pod to pass its `cast` readiness probe.
5. Executes `scripts/check-rpc.py` to validate `eth_chainId` (`31337`), `eth_blockNumber`, `eth_accounts`, and `eth_getBalance`.

### Run the RPC smoke test manually
```bash
python3 scripts/check-rpc.py --url http://localhost:8545 --expected-chain-id 31337
```

### Manual `kubectl` verification
```bash
kubectl get nodes
kubectl get pods -n kubechain-nodes
kubectl get svc -n kubechain-nodes
```

### Tear down the environment
```bash
./scripts/local-down.sh
```
