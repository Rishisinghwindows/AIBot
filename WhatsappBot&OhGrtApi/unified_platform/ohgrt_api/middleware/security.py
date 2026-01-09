"""
Security Headers Middleware.

Validates request security headers.
"""

import logging
import time
from typing import Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ohgrt_api.config import settings

logger = logging.getLogger(__name__)

# Paths exempt from security header checks
EXEMPT_PATHS: Set[str] = {
    "/",
    "/health",
    "/health/live",
    "/health/ready",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/whatsapp/webhook",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to validate security headers."""

    async def dispatch(self, request: Request, call_next):
        # Skip for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # In development, headers are optional
        if settings.is_development:
            return await call_next(request)

        # Validate X-Request-ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing X-Request-ID header"},
            )

        # Validate X-Timestamp
        timestamp_str = request.headers.get("X-Timestamp")
        if timestamp_str:
            try:
                timestamp = int(timestamp_str)
                now = int(time.time())
                diff = abs(now - timestamp)

                if diff > settings.request_timestamp_tolerance_seconds:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Request timestamp too old or too new"},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid X-Timestamp header"},
                )

        response = await call_next(request)

        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if request_id:
            response.headers["X-Request-ID"] = request_id

        return response
