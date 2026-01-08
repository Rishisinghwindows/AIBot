"""
Pending Location Store

Tracks users who have been asked for their location for "near me" searches.
Uses in-memory storage with TTL-based expiry.
"""

import logging
import asyncio
from typing import Optional, Dict
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


class PendingLocationStore:
    """
    Store for tracking pending location requests.

    When a user asks "restaurants near me", we ask for their location
    and store what they were searching for. When they send location,
    we retrieve the pending search and complete it.
    """

    def __init__(self, max_entries: int = 10000, expiry_minutes: int = 10):
        """
        Initialize pending location store.

        Args:
            max_entries: Maximum pending requests to track
            expiry_minutes: How long to wait for location before expiring
        """
        self.max_entries = max_entries
        self.expiry_minutes = expiry_minutes
        self._pending: OrderedDict[str, Dict] = OrderedDict()
        self._lock = asyncio.Lock()

        logger.info(f"PendingLocationStore initialized: max={max_entries}, expiry={expiry_minutes}min")

    async def save_pending_search(
        self,
        phone: str,
        search_query: str,
        original_message: str,
    ) -> bool:
        """
        Save a pending search that needs location.

        Args:
            phone: User's phone number
            search_query: The extracted search term (e.g., "restaurants")
            original_message: The original user message

        Returns:
            True if saved successfully
        """
        async with self._lock:
            self._pending[phone] = {
                "search_query": search_query,
                "original_message": original_message,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=self.expiry_minutes),
            }

            # Move to end (most recent)
            self._pending.move_to_end(phone)

            # Evict oldest if over capacity
            while len(self._pending) > self.max_entries:
                self._pending.popitem(last=False)

            logger.info(f"Saved pending search for {phone}: {search_query}")
            return True

    async def get_pending_search(self, phone: str) -> Optional[Dict]:
        """
        Get and remove pending search for a user.

        Args:
            phone: User's phone number

        Returns:
            Pending search data or None if not found/expired
        """
        async with self._lock:
            if phone not in self._pending:
                return None

            pending = self._pending[phone]

            # Check if expired
            if datetime.now() > pending["expires_at"]:
                del self._pending[phone]
                logger.debug(f"Pending search expired for {phone}")
                return None

            # Remove and return
            del self._pending[phone]
            logger.info(f"Retrieved pending search for {phone}")
            return pending

    async def has_pending_search(self, phone: str) -> bool:
        """Check if user has a pending location search."""
        async with self._lock:
            if phone not in self._pending:
                return False

            pending = self._pending[phone]
            if datetime.now() > pending["expires_at"]:
                del self._pending[phone]
                return False

            return True

    async def peek_pending_search(self, phone: str) -> Optional[Dict]:
        """
        Peek at pending search for a user WITHOUT removing it.

        Use this to check what type of pending search exists
        before routing. Use get_pending_search to actually consume it.

        Args:
            phone: User's phone number

        Returns:
            Pending search data or None if not found/expired
        """
        async with self._lock:
            if phone not in self._pending:
                return None

            pending = self._pending[phone]

            # Check if expired
            if datetime.now() > pending["expires_at"]:
                del self._pending[phone]
                logger.debug(f"Pending search expired for {phone}")
                return None

            # Return without removing
            return pending

    async def clear_pending(self, phone: str) -> bool:
        """Clear pending search for a user."""
        async with self._lock:
            if phone in self._pending:
                del self._pending[phone]
            return True


# Singleton instance
_store: Optional[PendingLocationStore] = None


def get_pending_location_store() -> PendingLocationStore:
    """Get the singleton PendingLocationStore instance."""
    global _store
    if _store is None:
        _store = PendingLocationStore()
    return _store
