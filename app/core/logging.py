"""
OpsPilot — Structured Logging.

JSON-formatted logging with correlation IDs for request tracing.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

from app.core.config import get_settings

# ── Context Variables (set per-request by middleware) ─────────
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


class StructuredFormatter(logging.Formatter):
    """
    Produces structured log lines.
    In production, outputs JSON. In development, outputs human-readable lines.
    """

    def format(self, record: logging.LogRecord) -> str:
        request_id = request_id_ctx.get()
        if request_id:
            record.request_id = request_id
        else:
            record.request_id = "-"

        record.module_name = record.name

        settings = get_settings()
        if settings.is_production:
            import orjson

            log_data = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "request_id": record.request_id,
            }
            if record.exc_info and record.exc_info[1]:
                log_data["exception"] = self.formatException(record.exc_info)

            return orjson.dumps(log_data).decode()
        else:
            return (
                f"{self.formatTime(record)} | {record.levelname:<8} | "
                f"{record.request_id} | {record.name} | {record.getMessage()}"
            )


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quieten noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use module __name__ as the name."""
    return logging.getLogger(f"opspilot.{name}")
