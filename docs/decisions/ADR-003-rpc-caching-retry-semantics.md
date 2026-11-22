# ADR-003: Deterministic Caching & Safe Retry Semantics for JSON-RPC

## Status
Accepted

## Context
Ethereum JSON-RPC 2.0 multiplexes both read-only operations and state-mutating transactions over HTTP POST requests to a single URI endpoint (`/`). 

In distributed systems, blind retry policies and naive caching cause catastrophic failures:
1. Retrying non-idempotent operations like `eth_sendRawTransaction` on connection drops can trigger nonce collisions or unintended state modifications.
2. Caching unfinalized chain data (`eth_getBlockByNumber("latest")`) leads to serving poisoned or stale state during chain reorganizations.

## Decision
We implement deterministic classification and execution rules for all JSON-RPC methods handled by the Gateway:

### 1. Retry Semantics
- **Idempotent Methods**: `eth_chainId`, `eth_blockNumber`, `eth_getBalance`, `eth_getBlockByNumber`, `eth_getTransactionByHash`, `eth_getTransactionReceipt`, `eth_getCode`, `eth_call` (with fixed block parameters).
  - *Policy*: May retry up to `N` times against alternate healthy backends using exponential backoff with jitter on HTTP 5xx or TCP socket resets.
- **Non-Idempotent Methods**: `eth_sendRawTransaction`, `eth_sendTransaction`.
  - *Policy*: **Zero retries**. If upstream fails ambiguously or times out, return a standardized JSON-RPC `-32000` execution error with upstream diagnostic metadata. Resubmission ownership remains strictly with the client.

### 2. Cache Key Canonicalization & TTL Matrix
Cache keys are deterministically generated:
```
key = "kubechain:cache:" + chain_id + ":" + method + ":" + sha256(canonical_json(params))
```
- Parameters are normalized (hex strings zero-padded or normalized to lowercase; object keys alphabetically sorted).
- Queries referencing `pending` or `latest` are **never** cached immutably.
- Finalized blocks (`blockNumber <= currentHeight - reorgSafetyDepth`) are cached with long TTL (24h+).
- In the event of Redis outage, the gateway fails open: requests bypass cache and query the backend directly without dropping traffic.

## Consequences
- **Positive**: Eliminates duplicate transaction submissions; prevents cache poisoning during chain reorganizations; guarantees deterministic response payloads.
- **Negative**: Adds parameter canonicalization overhead on cache lookups (mitigated by fast SHA256 and Pydantic validation).
