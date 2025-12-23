"""
Structured logging with correlation ID support.

Provides request-scoped logging with automatic correlation ID injection
for distributed tracing and request tracking.
"""
from __future__ import annotations

import logging
import os
import uuid
from contextvars import ContextVar
from typing import Any, Callable, MutableMapping, Optional

import structlog


# Context variable for request-scoped correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID from context."""
    return correlation_id_var.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set the correlation ID in context.

    Args:
        correlation_id: Optional ID to set. If None, generates a new UUID.

    Returns:
        The correlation ID that was set.
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    correlation_id_var.set(None)


def add_correlation_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """
    Structlog processor to add correlation ID to log events.

    This processor automatically injects the current request's correlation ID
    into every log message.
    """
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_service_info(
    logger: logging.Logger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """
    Structlog processor to add service information to log events.
    """
    event_dict["service"] = "ohgrt-api"
    event_dict["version"] = os.getenv("APP_VERSION", "2.1.0")
    return event_dict


def configure_logging(level: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Configure structlog to emit JSON logs with consistent metadata.

    Features:
    - Automatic correlation ID injection
    - Service identification
    - ISO timestamp format
    - JSON output for log aggregation
    """
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_correlation_id,
            add_service_info,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logger = structlog.get_logger()
    logger.info("logger_initialized", level=log_level)
    return logger


def get_logger(**initial_values: Any) -> structlog.stdlib.BoundLogger:
    """
    Get a bound logger with optional initial values.

    Args:
        **initial_values: Key-value pairs to bind to all log messages.

    Returns:
        A bound structlog logger.

    Example:
        logger = get_logger(user_id="123", action="chat")
        logger.info("message_sent")  # Includes user_id and action
    """
    return structlog.get_logger().bind(**initial_values)


logger = configure_logging()
