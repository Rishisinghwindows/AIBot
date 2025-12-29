"""
In-Memory Session Store

Lightweight storage for lite mode - no database required.
Perfect for testing, development, and resource-constrained environments.

Features:
- Thread-safe with asyncio locks
- TTL-based auto-expiry
- LRU eviction when max capacity reached
- Same interface as PostgreSQL store
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict

from bot.stores.base_store import BaseStore, UserProfile

logger = logging.getLogger(__name__)


class MemoryStore(BaseStore):
    """
    In-memory implementation of user/context storage.

    Usage:
        store = MemoryStore(max_users=10000)
        await store.save_birth_details(phone, date, time, place)
        profile = await store.get_user(phone)
    """

    def __init__(self, max_users: int = 10000, max_contexts: int = 50000):
        """
        Initialize memory store.

        Args:
            max_users: Maximum user profiles to keep (LRU eviction)
            max_contexts: Maximum context entries to keep
        """
        self.max_users = max_users
        self.max_contexts = max_contexts

        # Storage
        self._users: OrderedDict[str, UserProfile] = OrderedDict()
        self._contexts: Dict[str, Dict[str, Any]] = {}  # phone:context_type -> data
        self._flow_states: Dict[str, Dict[str, Any]] = {}  # phone -> flow_state

        # Locks for thread safety
        self._user_lock = asyncio.Lock()
        self._context_lock = asyncio.Lock()
        self._flow_lock = asyncio.Lock()

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(f"MemoryStore initialized: max_users={max_users}, max_contexts={max_contexts}")

    async def start_cleanup_task(self):
        """Start background task to clean expired entries."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Periodically clean expired contexts and flow states."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now()

        # Clean expired contexts
        async with self._context_lock:
            expired_contexts = [
                key for key, ctx in self._contexts.items()
                if ctx.get("expires_at") and ctx["expires_at"] < now
            ]
            for key in expired_contexts:
                del self._contexts[key]
            if expired_contexts:
                logger.debug(f"Cleaned {len(expired_contexts)} expired contexts")

        # Clean expired flow states
        async with self._flow_lock:
            expired_flows = [
                phone for phone, state in self._flow_states.items()
                if state.get("expires_at") and state["expires_at"] < now
            ]
            for phone in expired_flows:
                del self._flow_states[phone]
            if expired_flows:
                logger.debug(f"Cleaned {len(expired_flows)} expired flow states")

    def _evict_lru_users(self):
        """Evict least recently used users if over capacity."""
        while len(self._users) > self.max_users:
            self._users.popitem(last=False)  # Remove oldest

    # =========================================================================
    # USER PROFILE METHODS
    # =========================================================================

    async def get_user(self, phone: str) -> Optional[UserProfile]:
        """Get user profile by phone number."""
        async with self._user_lock:
            if phone in self._users:
                # Move to end (most recently used)
                self._users.move_to_end(phone)
                return self._users[phone]
            return None

    async def save_birth_details(
        self,
        phone: str,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        name: str = None
    ) -> bool:
        """Save user's birth details."""
        async with self._user_lock:
            now = datetime.now()

            if phone in self._users:
                user = self._users[phone]
                user.birth_date = birth_date
                user.birth_time = birth_time
                user.birth_place = birth_place
                if name:
                    user.name = name
                user.updated_at = now
                self._users.move_to_end(phone)
            else:
                self._users[phone] = UserProfile(
                    phone_number=phone,
                    name=name,
                    birth_date=birth_date,
                    birth_time=birth_time,
                    birth_place=birth_place,
                    created_at=now,
                    updated_at=now
                )
                self._evict_lru_users()

            logger.info(f"Saved birth details for {phone}")
            return True

    async def save_chart_data(
        self,
        phone: str,
        moon_sign: str = None,
        sun_sign: str = None,
        ascendant: str = None,
        moon_nakshatra: str = None
    ) -> bool:
        """Save calculated chart data."""
        async with self._user_lock:
            if phone not in self._users:
                # Create user if doesn't exist
                self._users[phone] = UserProfile(
                    phone_number=phone,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

            user = self._users[phone]
            if moon_sign:
                user.moon_sign = moon_sign
            if sun_sign:
                user.sun_sign = sun_sign
            if ascendant:
                user.ascendant = ascendant
            if moon_nakshatra:
                user.moon_nakshatra = moon_nakshatra
            user.updated_at = datetime.now()

            self._users.move_to_end(phone)
            return True

    async def get_birth_details(self, phone: str) -> Optional[Dict[str, str]]:
        """Get just the birth details for a user."""
        user = await self.get_user(phone)
        if user and user.has_birth_details():
            return {
                "birth_date": user.birth_date,
                "birth_time": user.birth_time,
                "birth_place": user.birth_place,
            }
        return None

    async def save_user_language(self, phone: str, language: str) -> bool:
        """Save user's preferred language."""
        async with self._user_lock:
            if phone not in self._users:
                self._users[phone] = UserProfile(
                    phone_number=phone,
                    preferred_language=language,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                self._users[phone].preferred_language = language
                self._users[phone].updated_at = datetime.now()
                self._users.move_to_end(phone)
            return True

    async def get_user_language(self, phone: str) -> str:
        """Get user's preferred language (default: 'en')."""
        user = await self.get_user(phone)
        return user.preferred_language if user else "en"

    # =========================================================================
    # CONTEXT METHODS (for ConversationManager)
    # =========================================================================

    async def save_context(
        self,
        phone: str,
        context_type: str,
        context_data: dict,
        expires_in_minutes: int = 30
    ) -> bool:
        """Save conversation context for multi-turn flows."""
        async with self._context_lock:
            key = f"{phone}:{context_type}"
            self._contexts[key] = {
                **context_data,
                "expires_at": datetime.now() + timedelta(minutes=expires_in_minutes),
                "created_at": datetime.now()
            }

            # Evict if over capacity
            while len(self._contexts) > self.max_contexts:
                # Remove oldest entry
                oldest_key = next(iter(self._contexts))
                del self._contexts[oldest_key]

            return True

    async def get_context(self, phone: str, context_type: str) -> Optional[dict]:
        """Get conversation context if not expired."""
        async with self._context_lock:
            key = f"{phone}:{context_type}"
            if key in self._contexts:
                ctx = self._contexts[key]
                if ctx.get("expires_at") and datetime.now() < ctx["expires_at"]:
                    return ctx
                else:
                    # Expired, remove it
                    del self._contexts[key]
            return None

    async def clear_context(self, phone: str, context_type: str = None) -> bool:
        """Clear conversation context."""
        async with self._context_lock:
            if context_type:
                key = f"{phone}:{context_type}"
                if key in self._contexts:
                    del self._contexts[key]
            else:
                # Clear all contexts for this phone
                keys_to_delete = [k for k in self._contexts if k.startswith(f"{phone}:")]
                for key in keys_to_delete:
                    del self._contexts[key]
            return True

    # =========================================================================
    # FLOW STATE METHODS (for step-based flows)
    # =========================================================================

    async def save_flow_state(
        self,
        phone: str,
        flow_name: str,
        current_step: str,
        collected_data: dict,
        expires_in_minutes: int = 10
    ) -> bool:
        """Save current flow state for step-based conversations."""
        async with self._flow_lock:
            self._flow_states[phone] = {
                "flow_name": flow_name,
                "current_step": current_step,
                "collected_data": collected_data,
                "expires_at": datetime.now() + timedelta(minutes=expires_in_minutes),
                "created_at": datetime.now()
            }
            return True

    async def get_flow_state(self, phone: str) -> Optional[dict]:
        """Get active flow state if not expired."""
        async with self._flow_lock:
            if phone in self._flow_states:
                state = self._flow_states[phone]
                if state.get("expires_at") and datetime.now() < state["expires_at"]:
                    return state
                else:
                    # Expired
                    del self._flow_states[phone]
            return None

    async def clear_flow_state(self, phone: str) -> bool:
        """Clear flow state (flow completed or cancelled)."""
        async with self._flow_lock:
            if phone in self._flow_states:
                del self._flow_states[phone]
            return True

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def get_stats(self) -> dict:
        """Get storage statistics."""
        return {
            "users_count": len(self._users),
            "contexts_count": len(self._contexts),
            "flow_states_count": len(self._flow_states),
            "max_users": self.max_users,
            "max_contexts": self.max_contexts
        }

    async def clear_all(self):
        """Clear all data (for testing)."""
        async with self._user_lock:
            self._users.clear()
        async with self._context_lock:
            self._contexts.clear()
        async with self._flow_lock:
            self._flow_states.clear()


# Singleton instance
_memory_store: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    """Get the singleton MemoryStore instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
