"""Structured JSON logging.

Emits one JSON object per line with arbitrary extra fields, so logs are easy to
ship/parse (thread_id, user_id, intent, tools, latency_ms, ...).
"""

import json
import logging
import sys

_LOGGER_NAME = "defi"


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            data.update(extra)
        return json.dumps(data, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    logger = logging.getLogger(_LOGGER_NAME)
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)


def log_event(event: str, **fields) -> None:
    """Emit a structured log line: the event name plus arbitrary fields."""
    get_logger().info(event, extra={"extra_fields": fields})
