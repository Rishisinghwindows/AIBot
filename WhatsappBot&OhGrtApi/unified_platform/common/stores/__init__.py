"""
Data stores for persistent state management.

Provides:
- UserStore: PostgreSQL-backed user profile persistence
- MemoryStore: In-memory storage (for lite mode)
- get_store(): Auto-selects based on LITE_MODE config
- BaseStore: Abstract interface for custom implementations
"""

from common.stores.base_store import BaseStore, UserProfile
from common.stores.user_store import (
    UserStore,
    UserProfile as PGUserProfile,
    get_user_store,
    UserStoreError,
    DatabaseConnectionError,
    DatabaseOperationError,
)
from common.stores.memory_store import MemoryStore, get_memory_store
from common.stores.pending_location_store import PendingLocationStore, get_pending_location_store


def get_store() -> BaseStore:
    """
    Get the appropriate store based on configuration.

    Returns:
        MemoryStore if LITE_MODE=True, otherwise UserStore (PostgreSQL)

    Usage:
        store = get_store()
        await store.save_birth_details(phone, date, time, place)
    """
    from common.config.settings import settings

    if settings.LITE_MODE:
        return get_memory_store()
    else:
        return get_user_store()


__all__ = [
    # Base interface
    "BaseStore",
    "UserProfile",

    # Implementations
    "UserStore",
    "MemoryStore",
    "PendingLocationStore",

    # Factory functions
    "get_store",
    "get_user_store",
    "get_memory_store",
    "get_pending_location_store",

    # Exceptions
    "UserStoreError",
    "DatabaseConnectionError",
    "DatabaseOperationError",
]
