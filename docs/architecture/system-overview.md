# KubeChain Architecture Overview

## 1. System Vision & Objective

KubeChain provides an enterprise-grade, declarative platform for deploying and operating EVM-compatible blockchain RPC nodes on Kubernetes. It abstracts the operational complexity of stateful node synchronization, health validation, traffic routing, caching, and rate limiting into native Kubernetes Custom Resources.

---

## 2. Component Architecture

```
                                  +-------------------------------------------------------+
                                  |                     CLIENT REQUEST                    |
                                  +---------------------------+---------------------------+
                                                              |
                                                              v
+-------------------------------------------------------------+-------------------------------------------------------------+
|                                                   DATA PLANE: RPC GATEWAY                                                 |
|                                                                                                                           |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|   | 1. Authentication & Security Layer                                                                                |   |
|   |    - API Key Extraction & SHA-256 Validation                                                                      |   |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|                                                              | Validated                                                  |
|                                                              v                                                            |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|   | 2. Rate Limiting Engine (Redis Token Bucket / Sliding Window)                                                     |   |
|   |    - Method Weighting (Compute Units: eth_blockNumber=10, eth_call=26, eth_sendRawTransaction=100)                  |   |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|                                                              | Within Quota                                               |
|                                                              v                                                            |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|   | 3. Cache Engine (Redis)                                                                                           |   |
|   |    - Canonical Parameter Hashing                                                                                  |   |
|   |    - Fail-Open Circuit Breaker                                                                                    |   |
|   +---------------------------------------+---------------------------------------------------------------------------+   |
|                                           | Cache Miss / Non-Cacheable                                                    |
|                                           v                                                                               |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|   | 4. Health-Aware Dynamic Routing & Discovery Pool                                                                  |   |
|   |    - Active Probing (eth_chainId, eth_blockNumber, eth_syncing, latency)                                          |   |
|   |    - State Classification: HEALTHY | SYNCING | LAGGING | DEGRADED | UNREACHABLE                                    |   |
|   +---------------------------------------+---------------------------------------------------------------------------+   |
|                                           |                                                                               |
|                                           v                                                                               |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|   | 5. Upstream HTTP Forwarder & Retry Controller                                                                     |   |
|   |    - Idempotent Reads: Bounded Retries                                                                            |   |
|   |    - Stateful Writes: Zero Retries                                                                                |   |
|   +---------------------------------------+---------------------------------------------------------------------------+   |
+-------------------------------------------|-------------------------------------------------------------------------------+
                                            |
                                            v Forwarded JSON-RPC
                      +---------------------+---------------------+
                      |                                           |
                      v                                           v
         +--------------------------+                +--------------------------+
         |     node-0 (Anvil Pod)   |                |     node-1 (Anvil Pod)   |
         |    Headless: 8545        |                |    Headless: 8545        |
         +--------------------------+                +--------------------------+
                      ^                                           ^
                      |                                           |
                      +---------------------+---------------------+
                                            |
                                            | Managed by StatefulSet
                                            |
+-------------------------------------------+-------------------------------------------------------------------------------+
|                                            CONTROL PLANE: KUBERNETES OPERATOR                                             |
|                                                                                                                           |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|   | 1. Custom Resource Definition: BlockchainNode (infra.kubechain.io/v1alpha1)                                       |   |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|                                                           | Watches CR Changes                                            |
|                                                           v                                                               |
|   +-------------------------------------------------------------------------------------------------------------------+   |
|   | 2. Kopf Operator Reconciler Loop                                                                                  |   |
|   |    - Reconciles StatefulSet (node replicas, storage volumes, resource limits)                                     |   |
|   |    - Reconciles Headless Service (peer discovery) and ClusterIP Service (RPC routing)                             |   |
|   |    - Reconciles PodDisruptionBudget (high availability guarantees)                                                |   |
|   |    - Detects Configuration Drift & Recovers from Pod/Node Failures                                                |   |
|   |    - Emits Kubernetes Status Conditions & Events                                                                  |   |
|   +-------------------------------------------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Communication & Security Standards

1. **Non-Root Execution**: Every container runs as an unprivileged user (`UID 10001` or `nobody`).
2. **Minimalist Attack Surface**: Public clients interact solely with the Gateway (`/v1/rpc`). Node pods are isolated within an internal network policy.
3. **Structured Observability**: Logs are emitted as structured JSON containing trace IDs. Prometheus metrics adhere to strict bounded cardinality.
