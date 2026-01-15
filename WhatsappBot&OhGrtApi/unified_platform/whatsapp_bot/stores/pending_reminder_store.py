"""
Pending Reminder Store

Tracks users who are in a multi-step reminder flow.
"""

import asyncio
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PendingReminderStore:
    """Store for tracking pending reminder setup steps."""

    def __init__(self, max_entries: int = 10000, expiry_minutes: int = 10):
        self.max_entries = max_entries
        self.expiry_minutes = expiry_minutes
        self._pending: OrderedDict[str, Dict] = OrderedDict()
        self._lock = asyncio.Lock()

        logger.info(
            "PendingReminderStore initialized: max=%s, expiry=%smin",
            max_entries,
            expiry_minutes,
        )

    async def save_pending(self, phone: str, reminder_text: str) -> bool:
        """Save pending reminder data for a user."""
        async with self._lock:
            self._pending[phone] = {
                "reminder_text": reminder_text,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(minutes=self.expiry_minutes),
            }

            self._pending.move_to_end(phone)
            while len(self._pending) > self.max_entries:
                self._pending.popitem(last=False)

            logger.info("Saved pending reminder for %s", phone)
            return True

    async def peek_pending(self, phone: str) -> Optional[Dict]:
        """Peek at pending reminder without removing it."""
        async with self._lock:
            if phone not in self._pending:
                return None

            pending = self._pending[phone]
            if datetime.now() > pending["expires_at"]:
                del self._pending[phone]
                logger.debug("Pending reminder expired for %s", phone)
                return None

            return pending

    async def clear_pending(self, phone: str) -> bool:
        """Clear pending reminder for a user."""
        async with self._lock:
            if phone in self._pending:
                del self._pending[phone]
            return True


_store: Optional[PendingReminderStore] = None


def get_pending_reminder_store() -> PendingReminderStore:
    """Get the singleton PendingReminderStore instance."""
    global _store
    if _store is None:
        _store = PendingReminderStore()
    return _store
