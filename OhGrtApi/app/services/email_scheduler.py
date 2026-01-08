"""
Background scheduler for sending scheduled emails.
Uses APScheduler to run periodic checks and send due emails.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.base import SessionLocal
from app.db.models import ScheduledTask, TaskExecution, User
from app.logger import logger
from app.services.gmail_service import GmailService


class EmailSchedulerService:
    """Service to process and send scheduled emails."""

    _instance: Optional["EmailSchedulerService"] = None
    _scheduler: Optional[AsyncIOScheduler] = None

    def __init__(self):
        self.settings = get_settings()

    @classmethod
    def get_instance(cls) -> "EmailSchedulerService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self):
        """Start the background scheduler."""
        if self._scheduler is not None and self._scheduler.running:
            logger.info("email_scheduler_already_running")
            return

        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._process_scheduled_emails,
            trigger=IntervalTrigger(seconds=30),  # Check every 30 seconds
            id="process_scheduled_emails",
            name="Process scheduled emails",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("email_scheduler_started")

    def stop(self):
        """Stop the background scheduler."""
        if self._scheduler is not None and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("email_scheduler_stopped")

    async def _process_scheduled_emails(self):
        """Process all due scheduled emails."""
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)

            # Find all active scheduled emails that are due
            due_tasks = (
                db.query(ScheduledTask)
                .filter(
                    ScheduledTask.task_type == "scheduled_email",
                    ScheduledTask.status == "active",
                    ScheduledTask.next_run_at <= now,
                )
                .all()
            )

            if not due_tasks:
                return

            logger.info("processing_scheduled_emails", count=len(due_tasks))

            for task in due_tasks:
                await self._send_scheduled_email(db, task)

        except Exception as e:
            logger.error("scheduled_email_processor_error", error=str(e))
        finally:
            db.close()

    async def _send_scheduled_email(self, db: Session, task: ScheduledTask):
        """Send a single scheduled email."""
        # Create execution record
        execution = TaskExecution(
            task_id=task.id,
            status="running",
        )
        db.add(execution)
        db.commit()

        try:
            # Get user credentials
            user = db.query(User).filter(User.id == task.user_id).first()
            if not user:
                raise Exception("User not found")

            # Load Gmail credentials
            from app.chat.service import ChatService
            service = ChatService(self.settings, db)
            credentials = service._load_credentials(user)

            gmail_cred = credentials.get("gmail")
            if not gmail_cred:
                raise Exception("Gmail not connected")

            # Initialize Gmail service
            gmail_service = GmailService(self.settings, credential=gmail_cred)
            if not gmail_service.available:
                raise Exception("Gmail service not available")

            # Get email details from task metadata
            email_data = task.task_metadata
            to = email_data.get("to")
            subject = email_data.get("subject")
            body = email_data.get("body")
            cc = email_data.get("cc")
            bcc = email_data.get("bcc")

            # Send the email
            result = await gmail_service.send_email(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
            )

            if result.get("success"):
                # Mark task as completed
                task.status = "completed"
                task.last_run_at = datetime.now(timezone.utc)
                task.run_count += 1

                # Update execution
                execution.status = "completed"
                execution.completed_at = datetime.now(timezone.utc)
                execution.result = f"Email sent successfully. Message ID: {result.get('message_id')}"
                execution.execution_metadata = {"message_id": result.get("message_id")}

                logger.info(
                    "scheduled_email_sent",
                    task_id=str(task.id),
                    to=to,
                    message_id=result.get("message_id"),
                )
            else:
                raise Exception("Failed to send email")

        except Exception as e:
            # Mark execution as failed
            execution.status = "failed"
            execution.completed_at = datetime.now(timezone.utc)
            execution.error_message = str(e)

            logger.error(
                "scheduled_email_failed",
                task_id=str(task.id),
                error=str(e),
            )

        finally:
            db.commit()


# Global scheduler instance
email_scheduler = EmailSchedulerService.get_instance()


def start_email_scheduler():
    """Start the email scheduler (call from app startup)."""
    email_scheduler.start()


def stop_email_scheduler():
    """Stop the email scheduler (call from app shutdown)."""
    email_scheduler.stop()
