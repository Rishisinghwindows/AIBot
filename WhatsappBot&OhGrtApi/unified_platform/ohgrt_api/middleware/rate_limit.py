"""
Rate Limiting Middleware.

Implements per-user/IP rate limiting.
"""

import logging
from typing import Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ohgrt_api.config import settings
from common.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Paths exempt from rate limiting
EXEMPT_PATHS: Set[str] = {
    "/",
    "/health",
    "/health/live",
    "/health/ready",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# Rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=settings.rate_limit_requests_per_minute,
            requests_per_hour=settings.rate_limit_requests_per_hour,
            redis_url=settings.redis_url if settings.is_production else None,
        )
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits."""

    async def dispatch(self, request: Request, call_next):
        # Skip if rate limiting is disabled
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Skip for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get rate limit key (user ID or IP)
        rate_key = self._get_rate_key(request)

        # Check rate limit
        limiter = get_rate_limiter()
        allowed, retry_after = limiter.check(rate_key)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {rate_key}")
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                },
            )
            if retry_after:
                response.headers["Retry-After"] = str(retry_after)
            return response

        response = await call_next(request)

        # Add rate limit headers
        remaining = limiter.get_remaining(rate_key)
        response.headers["X-RateLimit-Limit"] = str(
            settings.rate_limit_requests_per_minute
        )
        response.headers["X-RateLimit-Remaining"] = str(
            remaining.get("minute_remaining", 0)
        )

        return response

    def _get_rate_key(self, request: Request) -> str:
        """
        Get rate limiting key from request.

        Prioritizes user ID from auth, falls back to IP.
        """
        # Try to get user ID from authorization
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Extract user ID from token (simplified)
            from ohgrt_api.auth.jwt_handler import decode_token
            token = auth_header[7:]
            payload = decode_token(token)
            if payload and payload.get("sub"):
                return f"user:{payload['sub']}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"
