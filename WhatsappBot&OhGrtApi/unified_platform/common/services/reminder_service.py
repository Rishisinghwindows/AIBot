"""
Reminder Service

Manages scheduling and sending of reminders via WhatsApp.
"""

from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import pytz
from typing import Dict, Any, Optional

from common.whatsapp.client import get_whatsapp_client


class ReminderService:
    _scheduler: AsyncIOScheduler = None
    _reminders: Dict[str, Dict[str, Any]] = {} # In-memory store for reminders

    @classmethod
    def start_scheduler(cls):
        if cls._scheduler is None:
            cls._scheduler = AsyncIOScheduler(timezone=pytz.utc)
            cls._scheduler.start()
            print("Reminder scheduler started.")

    @classmethod
    def shutdown_scheduler(cls):
        if cls._scheduler is not None:
            cls._scheduler.shutdown()
            cls._scheduler = None
            print("Reminder scheduler shut down.")

    @classmethod
    async def _send_reminder_message(cls, to_number: str, message: str, reminder_id: str):
        whatsapp_client = get_whatsapp_client()
        await whatsapp_client.send_text_message(to=to_number, text=f"Reminder: {message}")
        print(f"Reminder {reminder_id} sent to {to_number}: {message}")
        cls._reminders.pop(reminder_id, None) # Remove reminder after sending

    @classmethod
    def add_reminder(cls, reminder_time: datetime, to_number: str, message: str) -> str:
        if cls._scheduler is None:
            raise Exception("Reminder scheduler is not running.")

        # Generate a unique ID for the reminder
        reminder_id = f"reminder_{len(cls._reminders)}_{datetime.now().timestamp()}"

        cls._scheduler.add_job(
            cls._send_reminder_message,
            DateTrigger(run_date=reminder_time),
            args=[to_number, message, reminder_id],
            id=reminder_id,
            name=f"Reminder for {to_number}",
        )
        cls._reminders[reminder_id] = {
            "time": reminder_time,
            "to_number": to_number,
            "message": message,
            "status": "scheduled",
        }
        print(f"Reminder scheduled: {reminder_id} for {reminder_time}")
        return reminder_id

    @classmethod
    def get_reminders(cls) -> Dict[str, Dict[str, Any]]:
        return cls._reminders

    @classmethod
    def get_reminder_by_id(cls, reminder_id: str) -> Optional[Dict[str, Any]]:
        return cls._reminders.get(reminder_id)
