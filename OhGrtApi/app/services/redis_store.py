"""
Redis-based storage for sessions and nonces.

Provides high-performance, distributed storage for:
- Web chat sessions (replacing in-memory store)
- Security nonces (replacing database queries)

Falls back to in-memory storage if Redis is unavailable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from app.config import get_settings
from app.logger import logger

# Try to import redis, fallback gracefully if not available
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False


class RedisConnectionError(Exception):
    """Raised when Redis connection fails."""
    pass


class RedisStore:
    """
    Redis-based key-value store with automatic fallback.

    Features:
    - Async Redis operations
    - Automatic reconnection
    - In-memory fallback when Redis unavailable
    - TTL support for automatic expiration
    """

    def __init__(self):
        self._redis: Optional[Any] = None
        self._fallback_store: Dict[str, Any] = {}
        self._fallback_expiry: Dict[str, datetime] = {}
        self._connected = False

    async def connect(self) -> bool:
        """
        Establish Redis connection.

        Returns:
            True if connected to Redis, False if using fallback
        """
        if not REDIS_AVAILABLE:
            logger.warning("redis_not_installed", message="redis package not installed, using in-memory fallback")
            return False

        settings = get_settings()
        try:
            self._redis = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("redis_connected", url=settings.redis_url.split("@")[-1])
            return True
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e), message="Using in-memory fallback")
            self._redis = None
            self._connected = False
            return False

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._connected and self._redis is not None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Set a key-value pair with optional TTL.

        Args:
            key: The key to set
            value: Value to store (will be JSON serialized if dict/list)
            ttl_seconds: Optional time-to-live in seconds

        Returns:
            True if successful
        """
        serialized = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

        if self.is_connected:
            try:
                if ttl_seconds:
                    await self._redis.setex(key, ttl_seconds, serialized)
                else:
                    await self._redis.set(key, serialized)
                return True
            except Exception as e:
                logger.error("redis_set_error", key=key, error=str(e))
                # Fall through to fallback

        # Fallback to in-memory
        self._fallback_store[key] = serialized
        if ttl_seconds:
            self._fallback_expiry[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        return True

    async def get(self, key: str) -> Optional[str]:
        """
        Get a value by key.

        Args:
            key: The key to retrieve

        Returns:
            The value or None if not found/expired
        """
        if self.is_connected:
            try:
                return await self._redis.get(key)
            except Exception as e:
                logger.error("redis_get_error", key=key, error=str(e))
                # Fall through to fallback

        # Fallback to in-memory
        self._cleanup_expired_fallback()
        return self._fallback_store.get(key)

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value and parse as JSON."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    async def delete(self, key: str) -> bool:
        """
        Delete a key.

        Args:
            key: The key to delete

        Returns:
            True if deleted
        """
        if self.is_connected:
            try:
                await self._redis.delete(key)
                return True
            except Exception as e:
                logger.error("redis_delete_error", key=key, error=str(e))

        # Fallback
        self._fallback_store.pop(key, None)
        self._fallback_expiry.pop(key, None)
        return True

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.

        Args:
            key: The key to check

        Returns:
            True if key exists and not expired
        """
        if self.is_connected:
            try:
                return await self._redis.exists(key) > 0
            except Exception as e:
                logger.error("redis_exists_error", key=key, error=str(e))

        # Fallback
        self._cleanup_expired_fallback()
        return key in self._fallback_store

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        if self.is_connected:
            try:
                return await self._redis.incr(key)
            except Exception as e:
                logger.error("redis_incr_error", key=key, error=str(e))

        # Fallback
        current = int(self._fallback_store.get(key, 0))
        self._fallback_store[key] = str(current + 1)
        return current + 1

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set expiration on existing key."""
        if self.is_connected:
            try:
                return await self._redis.expire(key, ttl_seconds)
            except Exception as e:
                logger.error("redis_expire_error", key=key, error=str(e))

        # Fallback
        if key in self._fallback_store:
            self._fallback_expiry[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            return True
        return False

    def _cleanup_expired_fallback(self):
        """Remove expired keys from fallback store."""
        now = datetime.now(timezone.utc)
        expired = [k for k, exp in self._fallback_expiry.items() if exp < now]
        for key in expired:
            self._fallback_store.pop(key, None)
            self._fallback_expiry.pop(key, None)


# Global instance
_redis_store: Optional[RedisStore] = None


async def get_redis_store() -> RedisStore:
    """Get or create the Redis store singleton."""
    global _redis_store
    if _redis_store is None:
        _redis_store = RedisStore()
        await _redis_store.connect()
    return _redis_store


async def close_redis_store():
    """Close the Redis store connection."""
    global _redis_store
    if _redis_store:
        await _redis_store.disconnect()
        _redis_store = None


# =============================================================================
# NONCE MANAGEMENT
# =============================================================================

class NonceStore:
    """
    Redis-backed nonce storage for replay attack prevention.

    Replaces database-based nonce storage for better performance.
    """

    NONCE_PREFIX = "nonce:"

    def __init__(self, redis_store: RedisStore):
        self.store = redis_store

    async def check_and_store(self, nonce: str, ttl_hours: int = 24) -> bool:
        """
        Check if nonce exists and store it if not.

        Args:
            nonce: The nonce value to check
            ttl_hours: How long to keep the nonce

        Returns:
            True if nonce is new (not seen before)
            False if nonce was already used (replay attack)
        """
        key = f"{self.NONCE_PREFIX}{nonce}"
        ttl_seconds = ttl_hours * 3600

        if self.store.is_connected:
            try:
                # Use SETNX for atomic check-and-set
                result = await self.store._redis.setnx(key, "1")
                if result:
                    await self.store._redis.expire(key, ttl_seconds)
                    return True
                return False
            except Exception as e:
                logger.error("nonce_check_error", error=str(e))
                # Fall through to fallback

        # Fallback: non-atomic but functional
        if await self.store.exists(key):
            return False
        await self.store.set(key, "1", ttl_seconds=ttl_seconds)
        return True

    async def is_used(self, nonce: str) -> bool:
        """Check if a nonce has been used."""
        key = f"{self.NONCE_PREFIX}{nonce}"
        return await self.store.exists(key)


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

class SessionStore:
    """
    Redis-backed session storage for web chat.

    Replaces in-memory session storage for persistence across instances.
    """

    SESSION_PREFIX = "session:"
    MESSAGE_PREFIX = "messages:"

    def __init__(self, redis_store: RedisStore):
        self.store = redis_store

    async def create_session(
        self,
        session_id: str,
        language: str = "en",
        ttl_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            language: User's preferred language
            ttl_hours: Session TTL in hours

        Returns:
            Session data dict
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=ttl_hours)

        session_data = {
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "language": language,
            "message_count": 0,
        }

        key = f"{self.SESSION_PREFIX}{session_id}"
        await self.store.set(key, session_data, ttl_seconds=ttl_hours * 3600)

        return session_data

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if exists and not expired."""
        key = f"{self.SESSION_PREFIX}{session_id}"
        return await self.store.get_json(key)

    async def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session data."""
        session = await self.get_session(session_id)
        if not session:
            return False

        session.update(kwargs)
        key = f"{self.SESSION_PREFIX}{session_id}"

        # Preserve remaining TTL
        remaining_seconds = 24 * 3600  # Default
        if "expires_at" in session:
            try:
                expires = datetime.fromisoformat(session["expires_at"])
                remaining = (expires - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    remaining_seconds = int(remaining)
            except (ValueError, TypeError):
                pass

        await self.store.set(key, session, ttl_seconds=remaining_seconds)
        return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete session and its messages."""
        await self.store.delete(f"{self.SESSION_PREFIX}{session_id}")
        await self.store.delete(f"{self.MESSAGE_PREFIX}{session_id}")
        return True

    async def add_message(
        self,
        session_id: str,
        message: Dict[str, Any],
        max_messages: int = 100,
    ):
        """Add a message to session history."""
        key = f"{self.MESSAGE_PREFIX}{session_id}"

        if self.store.is_connected:
            try:
                # Use Redis list for efficient message storage
                await self.store._redis.rpush(key, json.dumps(message))
                # Trim to max messages
                await self.store._redis.ltrim(key, -max_messages, -1)
                # Set expiry same as session
                await self.store._redis.expire(key, 24 * 3600)
                return
            except Exception as e:
                logger.error("session_add_message_error", error=str(e))

        # Fallback: store as JSON array
        messages = await self.get_messages(session_id, limit=max_messages)
        messages.append(message)
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
        await self.store.set(key, messages, ttl_seconds=24 * 3600)

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get messages for a session."""
        key = f"{self.MESSAGE_PREFIX}{session_id}"

        if self.store.is_connected:
            try:
                # Get last N messages from Redis list
                raw_messages = await self.store._redis.lrange(key, -limit, -1)
                return [json.loads(m) for m in raw_messages]
            except Exception as e:
                logger.error("session_get_messages_error", error=str(e))

        # Fallback
        data = await self.store.get_json(key)
        if isinstance(data, list):
            return data[-limit:]
        return []

    async def increment_message_count(self, session_id: str) -> int:
        """Increment and return message count."""
        session = await self.get_session(session_id)
        if not session:
            return 0

        count = session.get("message_count", 0) + 1
        await self.update_session(session_id, message_count=count)
        return count

    async def get_message_count(self, session_id: str) -> int:
        """Get current message count."""
        session = await self.get_session(session_id)
        return session.get("message_count", 0) if session else 0
