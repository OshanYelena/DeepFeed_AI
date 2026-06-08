"""
DeepFeed AI - Logging Framework
Structured JSON logging with trace_id propagation.
All services must include trace_id in every log entry.
"""
import logging
import sys
from typing import Any
import structlog
from config import settings


def configure_logging() -> None:
    """Configure structlog for structured JSON output."""

    # Use stdlib logging integration to support add_logger_name
    shared_processors_no_name = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.app_env in ("local", "test"):
        # Pretty console output for local/test development
        structlog.configure(
            processors=shared_processors_no_name + [
                structlog.dev.ConsoleRenderer(colors=False),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=False,
        )
    else:
        # JSON output for all other environments
        structlog.configure(
            processors=shared_processors_no_name + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )

    # Route standard library logging through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.app_debug else logging.INFO,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a named logger. Usage: logger = get_logger(__name__)"""
    return structlog.get_logger(name)


def bind_trace_id(trace_id: str) -> None:
    """Bind trace_id to current context (call per request)."""
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def clear_context() -> None:
    """Clear context variables (call after request)."""
    structlog.contextvars.clear_contextvars()
