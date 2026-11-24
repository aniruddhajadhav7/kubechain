"""Unit tests for core configuration settings."""

import os
from unittest.mock import patch

from core.config import (
    AuthSettings,
    ChainSettings,
    GatewaySettings,
    HealthSettings,
    RedisSettings,
    UpstreamSettings,
    get_settings,
)


def test_default_settings_instantiation() -> None:
    """Verify that default settings instantiate with expected defaults."""
    settings = get_settings()

    assert settings.gateway.host == "0.0.0.0"
    assert settings.gateway.port == 8000
    assert settings.gateway.debug is False

    assert settings.chain.id == 31337
    assert settings.chain.name == "local-anvil"
    assert settings.chain.network == "anvil-dev"

    assert "http://localhost:8545" in settings.upstream.url_list
    assert settings.upstream.timeout_seconds == 5.0
    assert settings.upstream.max_retries == 2

    assert settings.health.probe_interval_seconds == 5.0
    assert settings.health.max_block_lag == 5

    assert settings.auth.auth_enabled is True
    assert len(settings.auth.api_keys_list) >= 1

    assert settings.redis.host == "localhost"
    assert settings.redis.port == 6379

    assert settings.cache.enabled is True
    assert settings.cache.finalized_ttl_seconds == 86400

    assert settings.operator.namespace == "default"
    assert settings.operator.reconcile_interval_seconds == 30


def test_upstream_urls_parsing() -> None:
    """Verify comma-separated URL string parsing into a list."""
    upstream = UpstreamSettings(
        backend_urls="http://node-0:8545, http://node-1:8545,  http://node-2:8545 "
    )
    assert upstream.url_list == [
        "http://node-0:8545",
        "http://node-1:8545",
        "http://node-2:8545",
    ]


def test_auth_api_keys_parsing() -> None:
    """Verify comma-separated API keys string parsing."""
    auth = AuthSettings(auth_api_keys="key_alpha, key_beta, key_gamma ")
    assert auth.api_keys_list == ["key_alpha", "key_beta", "key_gamma"]


def test_settings_environment_override() -> None:
    """Verify that environment variables override default settings."""
    env_overrides = {
        "GATEWAY_PORT": "9999",
        "CHAIN_ID": "1",
        "CHAIN_NAME": "ethereum-mainnet",
        "REDIS_PORT": "6380",
        "HEALTH_MAX_BLOCK_LAG": "12",
    }
    with patch.dict(os.environ, env_overrides):
        gateway = GatewaySettings()
        chain = ChainSettings()
        redis = RedisSettings()
        health = HealthSettings()

        assert gateway.port == 9999
        assert chain.id == 1
        assert chain.name == "ethereum-mainnet"
        assert redis.port == 6380
        assert health.max_block_lag == 12
