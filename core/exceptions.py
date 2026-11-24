"""KubeChain Core Domain Exceptions."""

from typing import Any


class KubeChainError(Exception):
    """Base class for all KubeChain domain exceptions."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


class ConfigurationError(KubeChainError):
    """Raised when application or environment configuration is invalid."""


class NodeHealthError(KubeChainError):
    """Raised when node health evaluation or status classification fails."""


class UpstreamBackendError(KubeChainError):
    """Raised when communication with an upstream blockchain node fails."""

    def __init__(
        self,
        message: str,
        backend_url: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = details or {}
        if backend_url:
            merged_details["backend_url"] = backend_url
        if status_code:
            merged_details["status_code"] = status_code
        super().__init__(message, details=merged_details)
        self.backend_url = backend_url
        self.status_code = status_code


class RateLimitExceededError(KubeChainError):
    """Raised when a client or tenant exceeds their Compute Unit rate limit quota."""

    def __init__(
        self,
        message: str = "Rate limit quota exceeded",
        retry_after: float = 1.0,
        tenant_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged_details = details or {}
        merged_details["retry_after"] = retry_after
        if tenant_id:
            merged_details["tenant_id"] = tenant_id
        super().__init__(message, details=merged_details)
        self.retry_after = retry_after
        self.tenant_id = tenant_id


class CacheError(KubeChainError):
    """Raised when a cache backend operation encounters an error."""


class ReconciliationError(KubeChainError):
    """Raised when the operator reconciler encounters an unrecoverable state."""


class JSONRPCError(KubeChainError):
    """Standard JSON-RPC 2.0 error representation.

    Specification: https://www.jsonrpc.org/specification#error_object
    Standard Error Codes:
      -32700: Parse error
      -32600: Invalid Request
      -32601: Method not found
      -32602: Invalid params
      -32603: Internal error
      -32000 to -32099: Server error (reserved for implementation-defined server-errors)
    """

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_EXECUTION = -32000
    SERVER_ERROR_TIMEOUT = -32001
    SERVER_ERROR_BACKEND_UNAVAILABLE = -32002

    def __init__(
        self,
        code: int,
        message: str,
        data: Any = None,
        rpc_id: int | str | None = None,
    ) -> None:
        super().__init__(f"JSON-RPC Error {code}: {message}", details={"code": code, "data": data})
        self.code = code
        self.rpc_message = message
        self.data = data
        self.rpc_id = rpc_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize into a valid JSON-RPC 2.0 error frame."""
        frame: dict[str, Any] = {
            "jsonrpc": "2.0",
            "error": {
                "code": self.code,
                "message": self.rpc_message,
            },
            "id": self.rpc_id,
        }
        if self.data is not None:
            frame["error"]["data"] = self.data
        return frame

    @classmethod
    def parse_error(cls, data: Any = None, rpc_id: int | str | None = None) -> "JSONRPCError":
        return cls(cls.PARSE_ERROR, "Parse error", data=data, rpc_id=rpc_id)

    @classmethod
    def invalid_request(cls, data: Any = None, rpc_id: int | str | None = None) -> "JSONRPCError":
        return cls(cls.INVALID_REQUEST, "Invalid Request", data=data, rpc_id=rpc_id)

    @classmethod
    def method_not_found(cls, method_name: str, rpc_id: int | str | None = None) -> "JSONRPCError":
        return cls(
            cls.METHOD_NOT_FOUND,
            f"The method {method_name} does not exist / is not available.",
            data={"method": method_name},
            rpc_id=rpc_id,
        )

    @classmethod
    def invalid_params(cls, data: Any = None, rpc_id: int | str | None = None) -> "JSONRPCError":
        return cls(cls.INVALID_PARAMS, "Invalid params", data=data, rpc_id=rpc_id)

    @classmethod
    def internal_error(cls, data: Any = None, rpc_id: int | str | None = None) -> "JSONRPCError":
        return cls(cls.INTERNAL_ERROR, "Internal error", data=data, rpc_id=rpc_id)

    @classmethod
    def execution_error(
        cls, message: str, data: Any = None, rpc_id: int | str | None = None
    ) -> "JSONRPCError":
        return cls(cls.SERVER_ERROR_EXECUTION, message, data=data, rpc_id=rpc_id)
