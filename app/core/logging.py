"""Structured (JSON) logging configuration for the application."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

_RESERVED_ATTRS = frozenset(logging.LogRecord(name="", level=0, pathname="", lineno=0, msg="", args=None, exc_info=None).__dict__.keys())


class JSONFormatter(logging.Formatter):
    """Render log records as single-line JSON objects for log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extras = {k: v for k, v in record.__dict__.items() if k not in _RESERVED_ATTRS}
        if extras:
            payload.update(extras)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the root logger with a JSON stream handler."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # Quiet down noisy third-party loggers while keeping our own at configured level.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)
