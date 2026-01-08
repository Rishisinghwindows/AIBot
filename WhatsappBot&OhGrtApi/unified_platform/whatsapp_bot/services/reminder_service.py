"""
Reminder Service.

Manages user reminders with background scheduler.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import heapq
import threading

logger = logging.getLogger(__name__)


@dataclass(order=True)
class Reminder:
    """Reminder data class."""

    time: datetime
    phone: str = field(compare=False)
    text: str = field(compare=False)
    id: str = field(compare=False, default="")


class ReminderService:
    """
    Service for managing and scheduling reminders.

    Uses a heap-based priority queue for efficient scheduling.
    """

    _instance: Optional["ReminderService"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._reminders: List[Reminder] = []
        self._reminder_dict: Dict[str, Reminder] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._id_counter = 0
        self._initialized = True

    def _generate_id(self) -> str:
        """Generate unique reminder ID."""
        self._id_counter += 1
        return f"rem_{self._id_counter}_{datetime.now().timestamp()}"

    async def add_reminder(
        self,
        phone: str,
        text: str,
        time: datetime,
    ) -> Reminder:
        """
        Add a new reminder.

        Args:
            phone: User's phone number
            text: Reminder text
            time: Reminder time

        Returns:
            Created Reminder
        """
        reminder = Reminder(
            time=time,
            phone=phone,
            text=text,
            id=self._generate_id(),
        )

        heapq.heappush(self._reminders, reminder)
        self._reminder_dict[reminder.id] = reminder

        logger.info(f"Reminder created: {reminder.id} for {phone} at {time}")
        return reminder

    async def remove_reminder(self, reminder_id: str) -> bool:
        """
        Remove a reminder by ID.

        Args:
            reminder_id: Reminder ID

        Returns:
            True if removed
        """
        if reminder_id in self._reminder_dict:
            del self._reminder_dict[reminder_id]
            # Note: We don't remove from heap, just mark as deleted
            logger.info(f"Reminder removed: {reminder_id}")
            return True
        return False

    async def get_user_reminders(self, phone: str) -> List[Reminder]:
        """
        Get all reminders for a user.

        Args:
            phone: User's phone number

        Returns:
            List of reminders
        """
        return [
            r for r in self._reminder_dict.values()
            if r.phone == phone and r.time > datetime.now()
        ]

    def start_scheduler(self) -> None:
        """Start the reminder scheduler."""
        if self._running:
            return

        self._running = True
        logger.info("Reminder scheduler started")

    def stop_scheduler(self) -> None:
        """Stop the reminder scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Reminder scheduler stopped")

    async def _check_reminders(self) -> None:
        """Background task to check and send reminders."""
        while self._running:
            try:
                await self._process_due_reminders()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reminder scheduler error: {e}")
                await asyncio.sleep(60)

    async def _process_due_reminders(self) -> None:
        """Process reminders that are due."""
        now = datetime.now()

        while self._reminders:
            reminder = self._reminders[0]

            # Check if still valid
            if reminder.id not in self._reminder_dict:
                heapq.heappop(self._reminders)
                continue

            # Check if due
            if reminder.time > now:
                break

            # Pop and process
            heapq.heappop(self._reminders)
            del self._reminder_dict[reminder.id]

            await self._send_reminder(reminder)

    async def _send_reminder(self, reminder: Reminder) -> None:
        """
        Send a reminder to the user.

        Args:
            reminder: Reminder to send
        """
        try:
            from common.whatsapp.client import get_whatsapp_client

            client = get_whatsapp_client()
            await client.send_text_message(
                to=reminder.phone,
                text=f"Reminder: {reminder.text}",
            )
            logger.info(f"Reminder sent: {reminder.id} to {reminder.phone}")
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder.id}: {e}")


# Global service instance
_reminder_service: Optional[ReminderService] = None


def get_reminder_service() -> ReminderService:
    """Get the reminder service singleton."""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service


async def create_reminder(
    phone: str,
    text: str,
    time: datetime,
) -> Reminder:
    """
    Create a new reminder.

    Args:
        phone: User's phone number
        text: Reminder text
        time: Reminder time

    Returns:
        Created Reminder
    """
    service = get_reminder_service()
    return await service.add_reminder(phone, text, time)
