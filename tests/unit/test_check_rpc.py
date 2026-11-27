"""Unit tests for the local JSON-RPC smoke test script and Phase 1 manifests."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_check_rpc_module() -> Any:
    script_path = REPO_ROOT / "scripts" / "check-rpc.py"
    spec = importlib.util.spec_from_file_location("check_rpc", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase1_files_exist() -> None:
    """Verify all Phase 1 infrastructure manifests, scripts, and docs exist."""
    expected_files = [
        REPO_ROOT / "deploy" / "local" / "kind" / "kind-config.yaml",
        REPO_ROOT / "deploy" / "local" / "kind" / "namespaces.yaml",
        REPO_ROOT / "deploy" / "local" / "anvil" / "pvc.yaml",
        REPO_ROOT / "deploy" / "local" / "anvil" / "deployment.yaml",
        REPO_ROOT / "deploy" / "local" / "anvil" / "service.yaml",
        REPO_ROOT / "scripts" / "local-up.sh",
        REPO_ROOT / "scripts" / "local-down.sh",
        REPO_ROOT / "scripts" / "check-rpc.py",
        REPO_ROOT / "docs" / "local-development.md",
    ]
    for path in expected_files:
        assert path.is_file(), f"Missing Phase 1 file: {path}"


def test_run_smoke_tests_success() -> None:
    """Verify run_smoke_tests passes when upstream returns valid deterministic responses."""
    check_rpc = _load_check_rpc_module()

    responses = {
        "eth_chainId": {"jsonrpc": "2.0", "id": 1, "result": "0x7a69"},
        "eth_blockNumber": {"jsonrpc": "2.0", "id": 2, "result": "0x5"},
        "eth_accounts": {
            "jsonrpc": "2.0",
            "id": 3,
            "result": ["0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"],
        },
        "eth_getBalance": {"jsonrpc": "2.0", "id": 4, "result": "0x21e19e0c9bab2400000"},
    }

    def fake_urlopen(req: Any, timeout: float = 5.0) -> MagicMock:
        payload = json.loads(req.data.decode("utf-8"))
        method = payload["method"]
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(responses[method]).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        check_rpc.run_smoke_tests("http://localhost:8545", expected_chain_id=31337)


def test_run_smoke_tests_chain_id_mismatch() -> None:
    """Verify run_smoke_tests fails fast when chain ID does not match."""
    check_rpc = _load_check_rpc_module()

    def fake_urlopen(req: Any, timeout: float = 5.0) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(
            {"jsonrpc": "2.0", "id": 1, "result": "0x1"}
        ).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False
        return mock_resp

    with (
        patch("urllib.request.urlopen", side_effect=fake_urlopen),
        pytest.raises(RuntimeError, match="Chain ID mismatch"),
    ):
        check_rpc.run_smoke_tests("http://localhost:8545", expected_chain_id=31337)
