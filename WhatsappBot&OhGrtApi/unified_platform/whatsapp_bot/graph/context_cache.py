"""
Simple in-memory context cache for follow-up handling.
"""

import time
import json
from typing import Dict, Any, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from common.config.settings import settings

DEFAULT_TTL_SECONDS = 600
KEY_PREFIX = "whatsapp:context:"
_cache: Dict[str, Dict[str, Any]] = {}
_redis_client = None


def _get_redis_client():
    """
    Lazy Redis client initializer.

    This keeps the cache implementation isolated so migrating to a DB-backed
    context store later only needs changes here.
    """
    global _redis_client
    if _redis_client is not None or not REDIS_AVAILABLE:
        return _redis_client
    try:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = None
        return None


def _redis_key(phone: str) -> str:
    return f"{KEY_PREFIX}{phone}"


def get_context(phone: str, max_age_seconds: Optional[int] = DEFAULT_TTL_SECONDS) -> Optional[Dict[str, Any]]:
    """
    Fetch recent context for a user.

    If Redis is available, use it as the shared cache; otherwise fall back to
    in-memory storage. This boundary makes DB migration straightforward.
    """
    if not phone:
        return None

    client = _get_redis_client()
    if client:
        raw = client.get(_redis_key(phone))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    data = _cache.get(phone)
    if not data:
        return None
    ts = data.get("ts")
    if max_age_seconds is not None and ts:
        if (time.time() - ts) > max_age_seconds:
            _cache.pop(phone, None)
            return None
    return data


def set_context(phone: str, data: Dict[str, Any]) -> None:
    """
    Persist recent context for a user.

    Redis is preferred for multi-instance deployments; fallback keeps local
    development simple. Swap this to a DB store later if needed.
    """
    if not phone:
        return
    payload = dict(data)
    payload["ts"] = time.time()

    client = _get_redis_client()
    if client:
        try:
            client.setex(_redis_key(phone), DEFAULT_TTL_SECONDS, json.dumps(payload))
            return
        except Exception:
            pass

    _cache[phone] = payload
