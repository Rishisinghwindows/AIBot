from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Set

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.logger import logger

# Lazy import to avoid circular dependencies
_nonce_store: Optional["NonceStore"] = None


async def get_nonce_store():
    """Get or create the nonce store (lazy initialization)."""
    global _nonce_store
    if _nonce_store is None:
        from app.services.redis_store import get_redis_store, NonceStore
        redis_store = await get_redis_store()
        _nonce_store = NonceStore(redis_store)
    return _nonce_store


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate security headers on incoming requests.

    Validates:
    - X-Request-ID: Unique identifier for request tracing
    - X-Nonce: One-time value to prevent replay attacks
    - X-Timestamp: Unix timestamp to prevent stale requests

    Exempt paths (public/auth endpoints) skip validation.
    """

    EXEMPT_PATHS: Set[str] = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/health/live",
        "/health/ready",
        "/metrics",
        "/auth/google",
        "/auth/refresh",
    }

    EXEMPT_PREFIXES: tuple = ("/docs", "/redoc", "/web", "/whatsapp", "/pdf", "/auth", "/mcp", "/chat")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        logger.info(f"path: {path}")

        settings = get_settings()

        # Skip all security validation in LITE_MODE (development/testing only)
        # SECURITY: Only allow lite_mode bypass in non-production environments
        if settings.lite_mode:
            if settings.environment.lower() in ("production", "prod"):
                logger.warning(
                    "security_lite_mode_blocked",
                    reason="LITE_MODE cannot be enabled in production",
                    path=path,
                )
                # Do NOT bypass security in production, even if lite_mode is set
            else:
                logger.debug("security_bypassed_lite_mode", path=path)
                return await call_next(request)

        # Skip validation for exempt paths
        if path in self.EXEMPT_PATHS or path.startswith(self.EXEMPT_PREFIXES):
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract required headers
        request_id = request.headers.get("X-Request-ID")
        nonce = request.headers.get("X-Nonce")
        timestamp_str = request.headers.get("X-Timestamp")

        # Validate presence of required headers
        if not all([request_id, nonce, timestamp_str]):
            missing = []
            if not request_id:
                missing.append("X-Request-ID")
            if not nonce:
                missing.append("X-Nonce")
            if not timestamp_str:
                missing.append("X-Timestamp")

            logger.warning("security_missing_headers", missing=missing, path=path)
            raise HTTPException(
                status_code=400,
                detail=f"Missing required security headers: {', '.join(missing)}",
            )

        # Validate timestamp format and freshness
        try:
            timestamp = float(timestamp_str)
            request_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            diff_seconds = abs((now - request_time).total_seconds())

            if diff_seconds > settings.request_timestamp_tolerance_seconds:
                logger.warning(
                    "security_timestamp_expired",
                    diff_seconds=diff_seconds,
                    tolerance=settings.request_timestamp_tolerance_seconds,
                    path=path,
                )
                raise HTTPException(
                    status_code=400,
                    detail="Request timestamp expired or too far in future",
                )
        except ValueError:
            logger.warning("security_invalid_timestamp", timestamp=timestamp_str, path=path)
            raise HTTPException(
                status_code=400,
                detail="Invalid timestamp format. Expected Unix timestamp.",
            )

        # Validate nonce hasn't been used (prevent replay attacks)
        # Uses Redis for high-performance nonce checking
        try:
            nonce_store = await get_nonce_store()
            is_new_nonce = await nonce_store.check_and_store(
                nonce,
                ttl_hours=settings.nonce_expiry_hours
            )

            if not is_new_nonce:
                logger.warning("security_nonce_reused", nonce=nonce[:8] + "...", path=path)
                raise HTTPException(
                    status_code=400,
                    detail="Nonce has already been used",
                )

            logger.debug(
                "security_validated",
                request_id=request_id,
                path=path,
            )

        except HTTPException:
            raise
        except asyncio.TimeoutError:
            logger.error("security_nonce_timeout", path=path)
            raise HTTPException(
                status_code=503,
                detail="Security validation timed out",
            )
        except Exception as e:
            logger.error("security_validation_error", error=str(e), path=path)
            raise HTTPException(
                status_code=500,
                detail="Security validation failed",
            )

        # Process request
        response = await call_next(request)

        # Add request ID to response for tracing
        response.headers["X-Request-ID"] = request_id

        return response


async def cleanup_expired_nonces() -> int:
    """
    Cleanup task for expired nonces.

    Note: When using Redis, nonces auto-expire via TTL.
    This function now only logs status for monitoring.

    Returns:
        0 (Redis handles expiration automatically)
    """
    try:
        nonce_store = await get_nonce_store()
        if nonce_store.store.is_connected:
            logger.info("nonce_cleanup_skipped", reason="Redis TTL handles expiration automatically")
        else:
            # For in-memory fallback, cleanup is handled internally
            nonce_store.store._cleanup_expired_fallback()
            logger.info("nonce_cleanup_completed", storage="fallback")
        return 0
    except Exception as e:
        logger.error("nonce_cleanup_failed", error=str(e))
        return 0
