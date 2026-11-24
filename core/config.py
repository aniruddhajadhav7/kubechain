"""Application environment configuration using Pydantic Settings."""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    """Settings governing the asynchronous JSON-RPC Gateway."""

    model_config = SettingsConfigDict(env_prefix="GATEWAY_", env_file=".env", extra="ignore")

    host: str = Field(default="0.0.0.0", description="Network host interface to bind.")
    port: int = Field(default=8000, ge=1024, le=65535, description="Port for HTTP RPC traffic.")
    debug: bool = Field(default=False, description="Enable debug mode.")
    log_level: str = Field(default="INFO", description="Log level for gateway.")


class ChainSettings(BaseSettings):
    """Settings governing target blockchain network and identity."""

    model_config = SettingsConfigDict(env_prefix="CHAIN_", env_file=".env", extra="ignore")

    id: int = Field(default=31337, ge=1, description="Expected EVM Chain ID.")
    name: str = Field(default="local-anvil", description="Target chain identifier.")
    network: str = Field(default="anvil-dev", description="Target network name.")


class UpstreamSettings(BaseSettings):
    """Settings governing upstream blockchain RPC backend routing."""

    model_config = SettingsConfigDict(env_prefix="UPSTREAM_", env_file=".env", extra="ignore")

    backend_urls: str = Field(
        default="http://localhost:8545",
        description="Comma-separated list of upstream RPC endpoints.",
    )
    timeout_seconds: float = Field(default=5.0, gt=0, description="Socket timeout in seconds.")
    max_retries: int = Field(
        default=2, ge=0, description="Max retry attempts for idempotent reads."
    )
    max_connections: int = Field(default=100, ge=1, description="Connection pool size limit.")
    max_keepalive_connections: int = Field(
        default=20, ge=1, description="Max idle keepalive connections."
    )

    @property
    def url_list(self) -> list[str]:
        """Parse comma-separated backend URLs into a clean list."""
        return [url.strip() for url in self.backend_urls.split(",") if url.strip()]


class HealthSettings(BaseSettings):
    """Settings governing active node health probing."""

    model_config = SettingsConfigDict(env_prefix="HEALTH_", env_file=".env", extra="ignore")

    probe_interval_seconds: float = Field(default=5.0, gt=0, description="Interval between probes.")
    probe_timeout_seconds: float = Field(
        default=2.0, gt=0, description="Socket timeout for probe calls."
    )
    max_block_lag: int = Field(default=5, ge=0, description="Max block delta before LAGGING state.")


class AuthSettings(BaseSettings):
    """Settings governing API authentication and rate limiting."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    auth_enabled: bool = Field(default=True, description="Enforce API key verification.")
    auth_api_keys: str = Field(
        default="kc_dev_secret_key_1,kc_dev_secret_key_2",
        description="Comma-separated authorized API keys for local dev.",
    )
    rate_limit_enabled: bool = Field(
        default=True, description="Enforce Compute Unit rate limiting."
    )
    rate_limit_compute_units_per_second: int = Field(
        default=100, gt=0, description="Compute Unit quota per second."
    )
    rate_limit_burst_capacity: int = Field(
        default=200, gt=0, description="Maximum burst capacity in Compute Units."
    )

    @property
    def api_keys_list(self) -> list[str]:
        """Parse comma-separated API keys into a list."""
        return [k.strip() for k in self.auth_api_keys.split(",") if k.strip()]


class RedisSettings(BaseSettings):
    """Settings governing the Redis caching and rate-limiting backend."""

    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", extra="ignore")

    host: str = Field(default="localhost", description="Redis server host.")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port.")
    db: int = Field(default=0, ge=0, description="Redis database index.")
    password: str | None = Field(default=None, description="Optional Redis password.")
    timeout_seconds: float = Field(default=1.0, gt=0, description="Redis socket timeout.")


class CacheSettings(BaseSettings):
    """Settings governing deterministic JSON-RPC response caching."""

    model_config = SettingsConfigDict(env_prefix="CACHE_", env_file=".env", extra="ignore")

    enabled: bool = Field(default=True, description="Enable response caching.")
    default_ttl_seconds: int = Field(
        default=300, ge=1, description="Default TTL for dynamic state."
    )
    finalized_ttl_seconds: int = Field(
        default=86400, ge=1, description="TTL for finalized immutable blocks."
    )


class OperatorSettings(BaseSettings):
    """Settings governing the Kopf Kubernetes Operator controller."""

    model_config = SettingsConfigDict(env_prefix="OPERATOR_", env_file=".env", extra="ignore")

    namespace: str = Field(default="default", description="Namespace watched by operator.")
    log_level: str = Field(default="INFO", description="Log level for operator controller.")
    reconcile_interval_seconds: int = Field(default=30, gt=0, description="Periodic sync interval.")


class ObservabilitySettings(BaseSettings):
    """Settings governing Prometheus metrics and OpenTelemetry tracing."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    metrics_port: int = Field(
        default=9090, ge=1024, le=65535, description="Port for Prometheus /metrics."
    )
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317", description="OTLP collector endpoint."
    )
    otel_service_name: str = Field(
        default="kubechain-gateway", description="Service name for OpenTelemetry."
    )
    otel_traces_enabled: bool = Field(default=False, description="Enable trace export.")


class Settings(BaseSettings):
    """Aggregated platform configuration settings."""

    gateway: GatewaySettings = Field(default_factory=GatewaySettings)
    chain: ChainSettings = Field(default_factory=ChainSettings)
    upstream: UpstreamSettings = Field(default_factory=UpstreamSettings)
    health: HealthSettings = Field(default_factory=HealthSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    operator: OperatorSettings = Field(default_factory=OperatorSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    @field_validator("gateway", mode="before")
    @classmethod
    def assemble_gateway(cls, v: Any) -> Any:
        return v or GatewaySettings()


def get_settings() -> Settings:
    """Create and return a loaded settings instance."""
    return Settings()
