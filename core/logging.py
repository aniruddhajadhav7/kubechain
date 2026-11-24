"""Structured JSON logging utilities with context propagation."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variables for distributed tracing correlation
trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)
span_id_ctx: ContextVar[str | None] = ContextVar("span_id", default=None)
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_log_context(
    trace_id: str | None = None,
    span_id: str | None = None,
    request_id: str | None = None,
) -> None:
    """Set contextual identifiers for structured log correlation."""
    if trace_id is not None:
        trace_id_ctx.set(trace_id)
    if span_id is not None:
        span_id_ctx.set(span_id)
    if request_id is not None:
        request_id_ctx.set(request_id)


def clear_log_context() -> None:
    """Clear contextual identifiers."""
    trace_id_ctx.set(None)
    span_id_ctx.set(None)
    request_id_ctx.set(None)


class JSONLogFormatter(logging.Formatter):
    """Format log records as structured, single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Inject tracing correlation if present
        trace_id = trace_id_ctx.get()
        if trace_id:
            log_payload["trace_id"] = trace_id

        span_id = span_id_ctx.get()
        if span_id:
            log_payload["span_id"] = span_id

        request_id = request_id_ctx.get()
        if request_id:
            log_payload["request_id"] = request_id

        # Include exception information if available
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if attached to record
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extras:
            log_payload["extra"] = extras

        return json.dumps(log_payload, default=str)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    logger_name: str | None = None,
) -> logging.Logger:
    """Configure and initialize application logging."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to prevent duplicate output
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONLogFormatter())
    else:
        standard_format = (
            "%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)d): %(message)s"
        )
        handler.setFormatter(logging.Formatter(standard_format))

    logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtain a logger instance by name."""
    return logging.getLogger(name)
