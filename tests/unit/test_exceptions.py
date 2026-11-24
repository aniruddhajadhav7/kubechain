"""Unit tests for core exception hierarchy and JSON-RPC error framing."""

from core.exceptions import (
    ConfigurationError,
    JSONRPCError,
    KubeChainError,
    NodeHealthError,
    RateLimitExceededError,
    UpstreamBackendError,
)


def test_kubechain_base_error_representation() -> None:
    """Verify base error message and details formatting."""
    err = KubeChainError("Cluster error", details={"cluster": "kind-dev", "code": 500})
    assert str(err) == "Cluster error"
    assert err.details["cluster"] == "kind-dev"
    assert "KubeChainError" in repr(err)


def test_domain_subclass_exceptions() -> None:
    """Verify domain-specific exceptions inherit from KubeChainError."""
    config_err = ConfigurationError("Missing REDIS_HOST")
    assert isinstance(config_err, KubeChainError)

    health_err = NodeHealthError("Node block lag exceeded limit")
    assert isinstance(health_err, KubeChainError)

    upstream_err = UpstreamBackendError(
        "Connection refused", backend_url="http://node-0:8545", status_code=502
    )
    assert isinstance(upstream_err, KubeChainError)
    assert upstream_err.backend_url == "http://node-0:8545"
    assert upstream_err.status_code == 502

    rate_err = RateLimitExceededError("Too Many Requests", retry_after=2.5, tenant_id="tenant_1")
    assert isinstance(rate_err, KubeChainError)
    assert rate_err.retry_after == 2.5
    assert rate_err.tenant_id == "tenant_1"


def test_jsonrpc_error_serialization() -> None:
    """Verify JSON-RPC 2.0 error framing compliance."""
    err = JSONRPCError(
        code=JSONRPCError.INVALID_PARAMS,
        message="Invalid hex block number",
        data={"param": "0xINVALID"},
        rpc_id=101,
    )
    frame = err.to_dict()

    assert frame["jsonrpc"] == "2.0"
    assert frame["id"] == 101
    assert frame["error"]["code"] == -32602
    assert frame["error"]["message"] == "Invalid hex block number"
    assert frame["error"]["data"] == {"param": "0xINVALID"}


def test_jsonrpc_error_factories() -> None:
    """Verify standard JSON-RPC 2.0 error factory constructors."""
    parse_err = JSONRPCError.parse_error(rpc_id=None)
    assert parse_err.code == -32700
    assert parse_err.to_dict()["id"] is None

    method_err = JSONRPCError.method_not_found("eth_unknownMethod", rpc_id=42)
    assert method_err.code == -32601
    assert method_err.to_dict()["id"] == 42
    assert "eth_unknownMethod" in method_err.rpc_message

    req_err = JSONRPCError.invalid_request(rpc_id=1)
    assert req_err.code == -32600

    internal_err = JSONRPCError.internal_error(rpc_id=2)
    assert internal_err.code == -32603

    exec_err = JSONRPCError.execution_error("Transaction execution reverted", rpc_id=3)
    assert exec_err.code == -32000
