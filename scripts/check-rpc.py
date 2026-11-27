#!/usr/bin/env python3
"""JSON-RPC connectivity and smoke test script for local KubeChain EVM nodes."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def json_rpc_call(
    url: str,
    method: str,
    params: list[Any] | None = None,
    request_id: int = 1,
    timeout: float = 5.0,
) -> dict[str, Any]:
    """Execute a JSON-RPC 2.0 POST request and return the parsed response payload."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": request_id,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status != 200:
                raise RuntimeError(f"Unexpected HTTP status {status} from {url}")
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to connect to RPC endpoint {url}: {exc}") from exc

    parsed: dict[str, Any] = json.loads(body)
    if parsed.get("jsonrpc") != "2.0":
        raise RuntimeError(f"Invalid JSON-RPC version in response: {parsed}")
    if parsed.get("id") != request_id:
        raise RuntimeError(f"Mismatched JSON-RPC id: expected {request_id}, got {parsed.get('id')}")
    if "error" in parsed:
        raise RuntimeError(f"JSON-RPC error from {method}: {parsed['error']}")
    if "result" not in parsed:
        raise RuntimeError(f"Missing 'result' field in response for {method}: {parsed}")

    return parsed


def run_smoke_tests(url: str, expected_chain_id: int, timeout: float = 5.0) -> None:
    """Run deterministic EVM JSON-RPC smoke checks against a target node."""
    # 1. Verify eth_chainId
    chain_resp = json_rpc_call(url, "eth_chainId", request_id=1, timeout=timeout)
    chain_id_hex = chain_resp["result"]
    actual_chain_id = int(chain_id_hex, 16)
    if actual_chain_id != expected_chain_id:
        raise RuntimeError(
            f"Chain ID mismatch: expected {expected_chain_id}, got {actual_chain_id} ({chain_id_hex})"
        )
    print(f"[PASS] eth_chainId -> {actual_chain_id} ({chain_id_hex})")

    # 2. Verify eth_blockNumber
    block_resp = json_rpc_call(url, "eth_blockNumber", request_id=2, timeout=timeout)
    block_hex = block_resp["result"]
    block_num = int(block_hex, 16)
    if block_num < 0:
        raise RuntimeError(f"Invalid block number: {block_num}")
    print(f"[PASS] eth_blockNumber -> {block_num} ({block_hex})")

    # 3. Verify deterministic dev accounts exist (eth_accounts)
    accounts_resp = json_rpc_call(url, "eth_accounts", request_id=3, timeout=timeout)
    accounts = accounts_resp["result"]
    if not isinstance(accounts, list) or len(accounts) == 0:
        raise RuntimeError(f"Expected non-empty deterministic accounts list, got: {accounts}")
    primary_account = accounts[0]
    print(f"[PASS] eth_accounts -> {len(accounts)} accounts (primary: {primary_account})")

    # 4. Verify eth_getBalance on primary deterministic account
    balance_resp = json_rpc_call(
        url, "eth_getBalance", params=[primary_account, "latest"], request_id=4, timeout=timeout
    )
    balance_wei = int(balance_resp["result"], 16)
    if balance_wei <= 0:
        raise RuntimeError(f"Expected positive balance for {primary_account}, got {balance_wei}")
    print(f"[PASS] eth_getBalance -> {balance_wei} wei")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Verify EVM JSON-RPC connectivity.")
    parser.add_argument(
        "--url",
        default="http://localhost:8545",
        help="Target JSON-RPC HTTP endpoint (default: http://localhost:8545)",
    )
    parser.add_argument(
        "--expected-chain-id",
        type=int,
        default=31337,
        help="Expected EVM chain ID in decimal (default: 31337)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP request timeout in seconds (default: 5.0)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    try:
        run_smoke_tests(
            url=args.url,
            expected_chain_id=args.expected_chain_id,
            timeout=args.timeout,
        )
    except Exception as exc:
        print(f"[FAIL] RPC verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
