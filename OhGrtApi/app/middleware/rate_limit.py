"""
Rate limiting middleware using Redis or in-memory fallback.

Provides per-user and per-IP rate limiting to prevent abuse.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Dict, Optional, Set, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.exceptions import RateLimitExceededError
from app.logger import logger


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    Used as fallback when Redis is not available.
    Note: Does not work across multiple instances.
    """

    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def _cleanup_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests older than the window."""
        now = time.time()
        cutoff = now - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        with self._lock:
            self._cleanup_old_requests(key, window_seconds)

            current_count = len(self._requests[key])

            if current_count >= max_requests:
                # Calculate when the oldest request will expire
                oldest = min(self._requests[key]) if self._requests[key] else time.time()
                retry_after = int(oldest + window_seconds - time.time()) + 1
                return False, 0, max(retry_after, 1)

            # Add current request
            self._requests[key].append(time.time())
            remaining = max_requests - len(self._requests[key])

            return True, remaining, 0


class RedisRateLimiter:
    """
    Redis-based rate limiter using sliding window log algorithm.

    Works across multiple instances.
    """

    def __init__(self, redis_url: str):
        self._redis = None
        self._redis_url = redis_url
        self._connected = False

    def _get_redis(self):
        """Lazy-load Redis connection."""
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self._redis_url)
                self._redis.ping()
                self._connected = True
                logger.info("rate_limiter_redis_connected")
            except Exception as e:
                logger.warning("rate_limiter_redis_failed", error=str(e))
                self._connected = False
                self._redis = None
        return self._redis

    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self._get_redis() is not None

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit using Redis.

        Uses sliding window log algorithm.
        """
        redis_client = self._get_redis()
        if redis_client is None:
            # Redis not available, allow by default
            return True, max_requests, 0

        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        try:
            pipe = redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)

            # Count current requests in window
            pipe.zcard(redis_key)

            # Execute
            results = pipe.execute()
            current_count = results[1]

            if current_count >= max_requests:
                # Get oldest timestamp to calculate retry_after
                oldest = redis_client.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + window_seconds - now) + 1
                else:
                    retry_after = window_seconds
                return False, 0, max(retry_after, 1)

            # Add current request
            pipe = redis_client.pipeline()
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, window_seconds + 60)  # Extra buffer for cleanup
            pipe.execute()

            remaining = max_requests - current_count - 1
            return True, remaining, 0

        except Exception as e:
            logger.error("rate_limiter_redis_error", error=str(e))
            # On Redis error, allow the request
            return True, max_requests, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Applies rate limits based on:
    - Authenticated user ID (if available)
    - Client IP address (fallback)

    Exempt paths are not rate limited.
    """

    EXEMPT_PATHS: Set[str] = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/health/live",
        "/health/ready",
    }

    EXEMPT_PREFIXES: Tuple[str, ...] = ("/docs", "/redoc")

    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()

        self._enabled = settings.rate_limit_enabled
        self._per_minute = settings.rate_limit_requests_per_minute
        self._per_hour = settings.rate_limit_requests_per_hour

        # Try Redis first, fall back to in-memory
        self._redis_limiter = RedisRateLimiter(settings.redis_url)
        self._memory_limiter = InMemoryRateLimiter()

        logger.info(
            "rate_limiter_initialized",
            enabled=self._enabled,
            per_minute=self._per_minute,
            per_hour=self._per_hour,
        )

    def _get_limiter(self):
        """Get the active rate limiter (Redis if available, else in-memory)."""
        if self._redis_limiter.is_available():
            return self._redis_limiter
        return self._memory_limiter

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Uses user ID from JWT if authenticated, otherwise client IP.
        """
        # Try to get user ID from request state (set by auth dependency)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"

        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip

        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip if rate limiting is disabled
        if not self._enabled:
            return await call_next(request)

        path = request.url.path

        # Skip exempt paths
        if path in self.EXEMPT_PATHS or path.startswith(self.EXEMPT_PREFIXES):
            return await call_next(request)

        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        client_id = self._get_client_identifier(request)
        limiter = self._get_limiter()

        # Check per-minute limit
        minute_key = f"{client_id}:minute"
        allowed_minute, remaining_minute, retry_after_minute = limiter.is_allowed(
            minute_key, self._per_minute, 60
        )

        if not allowed_minute:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                limit_type="per_minute",
                path=path,
            )
            raise RateLimitExceededError(
                message="Too many requests. Please slow down.",
                retry_after=retry_after_minute,
            )

        # Check per-hour limit
        hour_key = f"{client_id}:hour"
        allowed_hour, remaining_hour, retry_after_hour = limiter.is_allowed(
            hour_key, self._per_hour, 3600
        )

        if not allowed_hour:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                limit_type="per_hour",
                path=path,
            )
            raise RateLimitExceededError(
                message="Hourly rate limit exceeded. Please try again later.",
                retry_after=retry_after_hour,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self._per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining_minute)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response
