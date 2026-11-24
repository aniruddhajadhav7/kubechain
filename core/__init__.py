"""KubeChain Core Foundation Package.

Provides shared configuration, structured logging utilities, and domain exception hierarchies.
"""

from core.exceptions import (
    CacheError,
    ConfigurationError,
    JSONRPCError,
    KubeChainError,
    NodeHealthError,
    RateLimitExceededError,
    ReconciliationError,
    UpstreamBackendError,
)
from core.logging import get_logger, setup_logging

__all__ = [
    "KubeChainError",
    "ConfigurationError",
    "JSONRPCError",
    "NodeHealthError",
    "UpstreamBackendError",
    "RateLimitExceededError",
    "CacheError",
    "ReconciliationError",
    "setup_logging",
    "get_logger",
]
