"""
Structured logging configuration for the PIM AI Coach.

Configures JSON-formatted logs with request ID correlation for production,
and human-readable logs for local development.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar

# Per-request ID for log correlation
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Inject the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")  # type: ignore[attr-defined]
        return True


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


def setup_logging() -> None:
    """Configure root logger with structured output."""
    log_level = os.environ.get("PIM_LOG_LEVEL", "INFO").upper()
    use_json = os.environ.get("PIM_LOG_FORMAT", "").lower() == "json"

    root = logging.getLogger()
    root.setLevel(log_level)

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if use_json:
        fmt = (
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","request_id":"%(request_id)s",'
            '"message":"%(message)s"}'
        )
    else:
        fmt = "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s — %(message)s"

    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
