"""Unit tests for structured JSON logging utilities."""

import json
import logging

from core.logging import (
    JSONLogFormatter,
    clear_log_context,
    get_logger,
    set_log_context,
    setup_logging,
)


def test_json_log_formatter_structure() -> None:
    """Verify that JSONLogFormatter outputs valid structured JSON with core fields."""
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path.py",
        lineno=42,
        msg="Transaction routed to backend",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Transaction routed to backend"
    assert parsed["line"] == 42
    assert "timestamp" in parsed


def test_json_log_formatter_with_context() -> None:
    """Verify trace and request correlation IDs are injected into log records."""
    formatter = JSONLogFormatter()
    set_log_context(trace_id="trace_abc123", request_id="req_xyz789")

    try:
        record = logging.LogRecord(
            name="gateway_logger",
            level=logging.WARNING,
            pathname="gateway.py",
            lineno=100,
            msg="Backend connection timeout",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["trace_id"] == "trace_abc123"
        assert parsed["request_id"] == "req_xyz789"
        assert parsed["level"] == "WARNING"
    finally:
        clear_log_context()


def test_setup_logging_and_get_logger() -> None:
    """Verify setup_logging configures logger handlers and levels."""
    logger = setup_logging(level="DEBUG", json_format=True, logger_name="kubechain_test")
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0].formatter, JSONLogFormatter)

    retrieved = get_logger("kubechain_test")
    assert retrieved is logger
