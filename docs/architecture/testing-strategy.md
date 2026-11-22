# KubeChain Comprehensive Testing & Verification Strategy

## 1. Testing Pyramid Overview

Quality and resilience in KubeChain are enforced through a layered testing hierarchy:

```
        / \
       /   \        Chaos & Fault Injection (Pod deletion, Redis partition, latency)
      / Chaos\
     /---------\     E2E System Tests on kind (Full operator + Gateway + Anvil)
    /    E2E    \
   /-------------\    Integration Tests (FastAPI + Testcontainers Redis + Upstream Mock)
  /  Integration  \
 /-----------------\   Unit Tests (Protocol validation, Lua rate-limiting, CRD logic)
/       Unit        \
---------------------
```

---

## 2. Test Layer Specifications

### Layer 1: Unit Testing (`tests/unit/`)
* **Execution Time**: < 5 seconds.
* **Scope**:
  - `test_jsonrpc_models.py`: Validates JSON-RPC 2.0 requests, responses, batch schemas, and error objects.
  - `test_cache_rules.py`: Asserts deterministic parameter normalization and SHA-256 cache key generation across various permutations of identical parameters.
  - `test_rate_limiter.py`: Mathematical verification of sliding-window algorithms and compute-unit weighting.
  - `test_health_evaluator.py`: Asserts state classifications (`HEALTHY`, `SYNCING`, `LAGGING`, `DEGRADED`, `UNREACHABLE`) against synthetic backend payloads.
  - `test_crd_schema.py`: Verifies Pydantic CRD schema validation rules (e.g., rejecting negative replicas, invalid client names, non-hex parameters).

### Layer 2: Integration Testing (`tests/integration/`)
* **Execution Time**: < 30 seconds.
* **Scope**:
  - Gateway HTTP pipeline verification using `httpx.AsyncClient` and FastAPI `TestClient`.
  - Testing against real Redis (via testcontainers or local ephemeral instance) for Lua rate limiter atomicity and fail-open resilience.
  - Testing Kopf handler triggers with mocked Kubernetes AsyncIO client to ensure reconciliation idempotency without requiring a live cluster.

### Layer 3: End-to-End Testing on `kind` (`tests/e2e/`)
* **Execution Time**: 1–3 minutes.
* **Prerequisites**: Running local `kind` cluster with applied CRD and operator.
* **Verification Flow**:
  1. Apply `BlockchainNode` manifest (`replicas: 2`).
  2. Wait for Kubernetes StatefulSet pods `node-0` and `node-1` to transition to `Running`.
  3. Verify operator updates `.status.phase` to `Running` and sets `status.conditions`.
  4. Send live `eth_blockNumber` and `eth_sendRawTransaction` through the Gateway service.
  5. Scale CR replicas from 2 to 3 and assert StatefulSet scaling and dynamic discovery pool registration.

### Layer 4: Chaos & Reliability Testing (`chaos/`)
* **Scenarios**:
  - **Scenario A (Pod Termination)**: Delete the primary Anvil pod while executing continuous load. Assert Gateway seamlessly routes in-flight idempotent requests to the secondary pod with zero 5xx errors returned to client.
  - **Scenario B (Redis Crash / Network Partition)**: Sever connection to Redis. Assert Gateway logs warning, emits metric `kubechain_cache_errors_total`, and fails open to upstream without dropping client requests.
  - **Scenario C (Operator Crash / Restart)**: Kill the operator pod. Assert running StatefulSets and Gateway continue uninterrupted. When operator restarts, assert zero state drift or redundant pod restarts.
  - **Scenario D (High Latency Injection)**: Inject 2000ms latency on `node-1`. Assert health engine classifies `node-1` as `DEGRADED` and drains traffic to `node-0`.

### Layer 5: Performance & Load Testing with k6 (`tests/load/`)
* **Key Targets**:
  - Sustained load: 1,000 requests/second.
  - Cache Hit Latency (p99): < 5ms.
  - Gateway Overhead (routing + auth + rate limit): < 3ms added latency.
  - Rate Limiter Accuracy: Zero requests permitted beyond configured CU window.
