"""
Correlation ID middleware for request tracing.

Extracts or generates a correlation ID for each request and makes it available
throughout the request lifecycle via context variables.
"""
from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logger import clear_correlation_id, get_logger, set_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage request correlation IDs.

    For each request:
    1. Extracts X-Request-ID header or generates new UUID
    2. Sets correlation ID in context for logging
    3. Logs request start/end with timing
    4. Adds correlation ID to response headers
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Set in context for logging
        set_correlation_id(correlation_id)

        # Get request-scoped logger
        logger = get_logger(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            client_ip=self._get_client_ip(request),
        )

        # Log request start
        start_time = time.time()
        logger.info(
            "request_started",
            query_params=str(request.query_params) if request.query_params else None,
            user_agent=request.headers.get("User-Agent"),
        )

        try:
            response = await call_next(request)

            # Log request completion
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Log request failure
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "request_failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=round(duration_ms, 2),
            )
            raise

        finally:
            # Clear correlation ID from context
            clear_correlation_id()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxy headers."""
        # Check X-Forwarded-For first (for requests behind load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP (nginx style)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"
