"""Structured logging configuration with context."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

import structlog
from structlog.typing import EventDict, WrappedLogger

__all__ = ["configure_logging"]


def configure_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    json_logs: bool = False,
) -> structlog.stdlib.BoundLogger:
    """Configure structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        json_logs: Use JSON formatting for machine parsing

    Returns:
        Configured logger
    """
    # Configure standard logging
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper()),
        handlers=handlers,
    )

    # Configure structlog processors
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Cast to correct return type
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger())
