# ADR-001 (Consolidated): Initial Technical Architecture for KubeChain V1

## Status
Accepted

## Context
KubeChain is an engineering platform for orchestrating, managing, and exposing EVM-compatible blockchain RPC infrastructure on Kubernetes. Operating stateful blockchain infrastructure alongside low-latency public JSON-RPC gateways introduces significant challenges:
1. Ethereum JSON-RPC multiplexes idempotent reads and non-idempotent stateful writes over a single HTTP POST endpoint.
2. Blockchain nodes require stateful persistence, stable network identities, and active synchronization monitoring.
3. Caching unfinalized chain state can poison client applications during blockchain reorganizations.
4. Tightly coupling public gateway traffic with Kubernetes API operations risks cluster-wide control plane collapse.

## Decision

We establish the initial technical architecture for KubeChain Version 1 as follows:

### 1. Three-Tier Architectural Partitioning
- **Control Plane (`operator/`)**: Written in Python 3.12+ using Kopf and `kubernetes-asyncio`. Solely responsible for reconciling `BlockchainNode` custom resources into StatefulSets, headless peer discovery services, cluster routing services, and PodDisruptionBudgets.
- **Data Plane (`gateway/`)**: Written in Python using FastAPI, Uvicorn, and HTTPX. Handles JSON-RPC 2.0 parsing, API key authentication, Redis sliding-window Compute Unit rate limiting, and reorg-aware caching.
- **Node Workloads (`node_manager/`)**: StatefulSet-managed EVM nodes. V1 uses Foundry/Anvil configured for deterministic local development, abstracted behind a generic `NodeHealthEvaluator` interface.

### 2. Strict Gateway Isolation Invariant
The Gateway has **zero infrastructure mutation privileges**. It never creates, deletes, or scales Kubernetes pods or services. It discovers backend nodes via Kubernetes internal DNS (`<cr>-internal.<namespace>.svc`) or an active background discovery pool.

### 3. JSON-RPC Execution & Retry Semantics
- **Idempotent Methods** (`eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, `eth_call`, `eth_getTransactionReceipt`): Permitted bounded retries with exponential backoff and jitter on upstream 5xx errors or socket timeouts.
- **Stateful Write Methods** (`eth_sendRawTransaction`): **Zero retries**. Upstream timeouts or disconnections immediately return a standardized JSON-RPC `-32000` execution error to prevent double-spending or nonce collision.

### 4. Deterministic Caching Policy
- Cache keys: `kubechain:cache:<chain_id>:<method>:<sha256(canonical_json(params))>`.
- Canonicalization normalizes hex formatting and dictionary sorting.
- Unfinalized blocks (`pending`, `latest`): Never cached immutably (short TTL of 1-2s or bypass).
- Finalized blocks: Cached long-term (24h+).
- **Fail-Open Policy**: If Redis crashes, requests bypass cache and route upstream without failing.

### 5. Local Development Environment
V1 deploys locally onto `kind` (Kubernetes-in-Docker) clusters with port mappings for host-level testing (`8000` for Gateway, `8545` for RPC, `9090` for Metrics).

## Consequences
- **Positive**: Complete fault isolation between data plane and control plane; safe and reliable RPC semantics; robust defense-in-depth security model; testable locally with minimal resource footprint.
- **Negative**: Gateway cannot unilaterally auto-scale pods on traffic bursts (scaling must be mediated by Kubernetes HPA or operator); Anvil local nodes do not test true P2P consensus sync stages (addressed in future milestones).
