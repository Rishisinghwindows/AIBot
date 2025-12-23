"""
Redis Store Service

Provides Redis-backed storage for sessions, nonces, and rate limiting.
Falls back to in-memory storage when Redis is unavailable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.logger import logger


class InMemoryFallback:
    """In-memory fallback when Redis is unavailable."""

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._messages: Dict[str, List[Dict[str, Any]]] = {}
        self._nonces: Dict[str, datetime] = {}
        self._counters: Dict[str, int] = {}

    def _cleanup_expired_fallback(self):
        """Remove expired entries."""
        now = datetime.now(timezone.utc)
        expired_sessions = [
            k for k, v in self._data.items()
            if v.get("expires_at") and datetime.fromisoformat(v["expires_at"]) < now
        ]
        for k in expired_sessions:
            del self._data[k]
            self._messages.pop(k, None)
            self._counters.pop(k, None)

        expired_nonces = [k for k, v in self._nonces.items() if v < now]
        for k in expired_nonces:
            del self._nonces[k]


class RedisStore:
    """Redis store with in-memory fallback."""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._fallback = InMemoryFallback()
        self.is_connected = redis_client is not None

    async def get(self, key: str) -> Optional[str]:
        if self._redis:
            try:
                return await self._redis.get(key)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        return self._fallback._data.get(key, {}).get("value")

    async def set(self, key: str, value: str, ex: int = None):
        if self._redis:
            try:
                await self._redis.set(key, value, ex=ex)
                return
            except Exception as e:
                logger.warning(f"Redis set error: {e}")

        expires_at = None
        if ex:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ex)).isoformat()
        self._fallback._data[key] = {"value": value, "expires_at": expires_at}

    async def delete(self, key: str):
        if self._redis:
            try:
                await self._redis.delete(key)
                return
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        self._fallback._data.pop(key, None)

    async def incr(self, key: str) -> int:
        if self._redis:
            try:
                return await self._redis.incr(key)
            except Exception as e:
                logger.warning(f"Redis incr error: {e}")

        self._fallback._counters[key] = self._fallback._counters.get(key, 0) + 1
        return self._fallback._counters[key]

    async def lpush(self, key: str, value: str):
        if self._redis:
            try:
                await self._redis.lpush(key, value)
                return
            except Exception as e:
                logger.warning(f"Redis lpush error: {e}")

        if key not in self._fallback._messages:
            self._fallback._messages[key] = []
        self._fallback._messages[key].insert(0, json.loads(value))

    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        if self._redis:
            try:
                return await self._redis.lrange(key, start, end)
            except Exception as e:
                logger.warning(f"Redis lrange error: {e}")

        messages = self._fallback._messages.get(key, [])
        if end == -1:
            return [json.dumps(m) for m in messages[start:]]
        return [json.dumps(m) for m in messages[start:end + 1]]


class SessionStore:
    """Session store backed by Redis or in-memory fallback."""

    def __init__(self, store: RedisStore):
        self.store = store

    async def create_session(
        self,
        session_id: str,
        language: str = "en",
        ttl_hours: int = 24,
    ) -> Dict[str, Any]:
        """Create a new session."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        session_data = {
            "session_id": session_id,
            "language": language,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
            "message_count": 0,
        }

        await self.store.set(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=ttl_hours * 3600,
        )
        return session_data

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        data = await self.store.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None

    async def update_session(self, session_id: str, **kwargs):
        """Update session data."""
        session = await self.get_session(session_id)
        if session:
            session.update(kwargs)
            # Preserve TTL
            expires_at = datetime.fromisoformat(session["expires_at"])
            remaining = (expires_at - datetime.now(timezone.utc)).total_seconds()
            if remaining > 0:
                await self.store.set(
                    f"session:{session_id}",
                    json.dumps(session),
                    ex=int(remaining),
                )

    async def delete_session(self, session_id: str):
        """Delete session and its messages."""
        await self.store.delete(f"session:{session_id}")
        await self.store.delete(f"messages:{session_id}")
        await self.store.delete(f"msg_count:{session_id}")

    async def add_message(self, session_id: str, message: Dict[str, Any]):
        """Add a message to session history."""
        await self.store.lpush(f"messages:{session_id}", json.dumps(message))

    async def get_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for session."""
        messages_raw = await self.store.lrange(f"messages:{session_id}", 0, limit - 1)
        messages = []
        for msg_str in messages_raw:
            try:
                if isinstance(msg_str, bytes):
                    msg_str = msg_str.decode()
                messages.append(json.loads(msg_str))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        # Reverse to get chronological order
        return list(reversed(messages))

    async def increment_message_count(self, session_id: str):
        """Increment message count for rate limiting."""
        await self.store.incr(f"msg_count:{session_id}")

    async def get_message_count(self, session_id: str) -> int:
        """Get message count for session."""
        count = await self.store.get(f"msg_count:{session_id}")
        if count:
            return int(count)
        return 0


class NonceStore:
    """Nonce store for replay attack prevention."""

    def __init__(self, store: RedisStore):
        self.store = store

    async def check_and_store(self, nonce: str, ttl_hours: int = 24) -> bool:
        """
        Check if nonce is new and store it.
        Returns True if nonce is new, False if already used.
        """
        key = f"nonce:{nonce}"
        existing = await self.store.get(key)
        if existing:
            return False

        await self.store.set(key, "1", ex=ttl_hours * 3600)
        return True


# Global Redis store instance
_redis_store: Optional[RedisStore] = None


async def get_redis_store() -> RedisStore:
    """Get or create the Redis store."""
    global _redis_store

    if _redis_store is not None:
        return _redis_store

    settings = get_settings()
    redis_client = None

    # Try to connect to Redis if configured
    if hasattr(settings, 'redis_url') and settings.redis_url:
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url)
            # Test connection
            await redis_client.ping()
            logger.info("redis_connected", url=settings.redis_url[:20] + "...")
        except ImportError:
            logger.warning("redis package not installed, using in-memory fallback")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory fallback")
            redis_client = None

    _redis_store = RedisStore(redis_client)

    if not _redis_store.is_connected:
        logger.info("redis_using_fallback", storage="in-memory")

    return _redis_store
