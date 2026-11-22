# KubeChain Data Flow & Sequence Specifications

## 1. Control Plane: CRD Reconciliation Flow

This sequence illustrates the end-to-end lifecycle when a user or GitOps workflow applies a `BlockchainNode` Custom Resource into the Kubernetes cluster.

```mermaid
sequenceDiagram
    autonumber
    actor User as Platform Engineer / CI
    participant K8s as Kubernetes API Server
    participant Kopf as Kopf Operator Loop
    participant Reconciler as Reconciler Engine
    participant K8sClient as Kubernetes Async Client
    participant STS as K8s StatefulSet
    participant Svc as K8s Services & PDB

    User->>K8s: kubectl apply -f node.yaml (BlockchainNode)
    K8s-->>Kopf: Watch Event: ADDED / MODIFIED (BlockchainNode)
    Kopf->>Reconciler: reconcile_node(spec, status, meta)
    
    Reconciler->>K8sClient: Get live Headless Service (<name>-internal)
    alt Service Missing or Drifted
        Reconciler->>K8sClient: Create/Update Headless Service
    end

    Reconciler->>K8sClient: Get live ClusterIP Service (<name>-rpc)
    alt Service Missing or Drifted
        Reconciler->>K8sClient: Create/Update ClusterIP Service
    end

    Reconciler->>K8sClient: Get live PodDisruptionBudget (<name>-pdb)
    alt PDB Missing or Drifted
        Reconciler->>K8sClient: Create/Update PDB
    end

    Reconciler->>K8sClient: Get live StatefulSet (<name>-sts)
    alt StatefulSet Missing
        Reconciler->>K8sClient: Create StatefulSet (spec, replicas, PVC template)
    else StatefulSet Drifted (Replicas, Image, Resources)
        Reconciler->>K8sClient: Patch StatefulSet Spec
    end

    Reconciler->>K8sClient: Read live StatefulSet.status (readyReplicas, currentReplicas)
    Reconciler->>Kopf: Build Status Conditions (Ready, Degraded, Healthy)
    Kopf->>K8s: Update Custom Resource .status subresource
    K8s-->>User: Status reflected in kubectl get bcn
```

---

## 2. Data Plane: JSON-RPC Request Execution Flow

This sequence models the complete lifecycle of a client JSON-RPC request through the Gateway, showing the interplay between authentication, rate-limiting, caching, and upstream routing.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Web3 dApp / Wallet
    participant GW as FastAPI RPC Gateway
    participant Auth as Auth Middleware
    participant RL as Rate Limiter (Lua)
    participant Redis as Redis Store
    participant Cache as Cache Engine
    participant Pool as Backend Routing Pool
    participant Node as Anvil / EVM Node

    Client->>GW: POST /v1/rpc {jsonrpc: "2.0", method: "eth_getBlockByNumber", params: ["0x10", false], id: 1}
    Note over Client,GW: Headers: X-API-Key: kc_live_...
    
    GW->>Auth: validate_api_key(headers)
    Auth->>Auth: Compute SHA-256(key)
    Auth-->>GW: Key Authenticated (Tenant: "team-a", Tier: "standard")

    GW->>RL: check_rate_limit("team-a", method="eth_getBlockByNumber", cu=30)
    RL->>Redis: EVALSHA sliding_window_limiter.lua
    Redis-->>RL: Allow (Current: 45/1000 CUs, Remaining: 955)
    RL-->>GW: Rate Limit OK

    GW->>Cache: lookup(chain_id=31337, method="eth_getBlockByNumber", params=["0x10", false])
    Cache->>Cache: Canonicalize params -> sha256_hash
    Cache->>Redis: GET kubechain:cache:31337:eth_getBlockByNumber:<hash>
    
    alt Cache Hit
        Redis-->>Cache: Return Cached JSON String
        Cache-->>GW: Cache Hit Data
        GW-->>Client: HTTP 200 {jsonrpc: "2.0", result: {...}, id: 1} (X-Cache: HIT)
    else Cache Miss
        Redis-->>Cache: nil (Cache Miss)
        Cache-->>GW: Cache Miss Proceed
        
        GW->>Pool: select_backend()
        Pool-->>GW: Selected Backend: node-0 (Status: HEALTHY, Latency: 12ms)
        
        GW->>Node: POST http://node-0:8545 {jsonrpc: "2.0", method: "eth_getBlockByNumber", ...}
        Node-->>GW: Upstream HTTP 200 {jsonrpc: "2.0", result: {...}, id: 1}
        
        opt Is Cacheable (Finalized Block)
            GW->>Cache: store(key, result, ttl=86400)
            Cache->>Redis: SETEX kubechain:cache:... 86400 <result>
        end
        
        GW-->>Client: HTTP 200 {jsonrpc: "2.0", result: {...}, id: 1} (X-Cache: MISS)
    end
```

---

## 3. Node Health Probing & Dynamic Routing Updates

This sequence models the background asynchronous discovery and health evaluation loop.

```mermaid
sequenceDiagram
    autonumber
    participant Probe as Health Probe Engine
    participant Pool as In-Memory Routing Pool
    participant Node0 as node-0.internal:8545
    participant Node1 as node-1.internal:8545
    participant Prom as Prometheus Metrics Registry

    loop Every 5 Seconds
        Probe->>Node0: POST {method: "eth_chainId"} & {method: "eth_blockNumber"}
        Node0-->>Probe: chainId: 31337, blockHeight: 1420 (Latency: 15ms)
        
        Probe->>Node1: POST {method: "eth_chainId"} & {method: "eth_blockNumber"}
        Node1-->>Probe: chainId: 31337, blockHeight: 1405 (Latency: 18ms)
        
        Note over Probe: Evaluate Cluster Head: max(1420, 1405) = 1420<br/>node-0 lag: 0 (HEALTHY)<br/>node-1 lag: 15 (maxBlockLag=10 -> LAGGING)
        
        Probe->>Pool: Update node-0 -> State: HEALTHY, Latency: 15ms
        Probe->>Pool: Update node-1 -> State: LAGGING, Latency: 18ms
        
        Probe->>Prom: kubechain_backend_status{backend="node-0"} = 1 (HEALTHY)
        Probe->>Prom: kubechain_backend_status{backend="node-1"} = 2 (LAGGING)
        Probe->>Prom: kubechain_backend_block_lag{backend="node-1"} = 15
    end
```

---

## 4. Resilience Flow: Redis Outage & Fail-Open Behavior

This sequence models the system's resilience when the Redis cache/rate-limiting cluster experiences a partition or crash.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Web3 Client
    participant GW as Gateway
    participant RL as Rate Limiter
    participant Cache as Cache Engine
    participant Redis as Redis (Down / Unreachable)
    participant Pool as Routing Pool
    participant Node as Upstream Node
    participant Prom as Prometheus Metrics

    Client->>GW: POST /v1/rpc (Request)
    GW->>RL: check_rate_limit()
    RL->>Redis: Query Lua Script
    Redis--xRL: ConnectionRefusedError / Timeout
    
    Note over RL: Catch RedisError<br/>Log Warning: Redis unavailable<br/>Fail-Open: Permit request
    RL->>Prom: Inc kubechain_ratelimit_errors_total
    RL-->>GW: Proceed (Fail-Open)

    GW->>Cache: lookup()
    Cache->>Redis: GET cache_key
    Redis--xCache: ConnectionRefusedError / Timeout
    
    Note over Cache: Catch RedisError<br/>Log Warning: Cache bypass<br/>Fail-Open: Treat as Cache Miss
    Cache->>Prom: Inc kubechain_cache_errors_total
    Cache-->>GW: Cache Miss (Fallback)

    GW->>Pool: select_backend()
    Pool-->>GW: Selected node-0
    GW->Node: Forward RPC Request
    Node-->>GW: Return Upstream Result
    GW-->>Client: HTTP 200 {result: ...} (X-Cache: BYPASS-ERROR)
```
