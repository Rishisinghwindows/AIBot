"""
Task Scheduler - Background service for executing scheduled tasks.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ohgrt_api.config import get_settings
from ohgrt_api.db.base import SessionLocal, is_db_available
from ohgrt_api.db.models import ScheduledTask
from ohgrt_api.graph.tool_agent import build_tool_agent
from ohgrt_api.logger import logger
from ohgrt_api.tasks.service import ScheduledTaskService


class TaskScheduler:
    """Background scheduler for executing due tasks."""

    def __init__(self, check_interval: int = 60):
        """
        Initialize the task scheduler.

        Args:
            check_interval: How often to check for due tasks (in seconds)
        """
        self.check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.settings = get_settings()

    async def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("scheduler_already_running")
            return

        if not is_db_available():
            logger.warning("scheduler_not_started", reason="Database not available")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("task_scheduler_started", check_interval=self.check_interval)

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("task_scheduler_stopped")

    async def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._process_due_tasks()
            except Exception as e:
                logger.error("scheduler_error", error=str(e))

            await asyncio.sleep(self.check_interval)

    async def _process_due_tasks(self):
        """Process all tasks that are due to run."""
        db = SessionLocal()
        try:
            service = ScheduledTaskService(db)
            due_tasks = service.get_due_tasks(limit=50)

            if due_tasks:
                logger.info("processing_due_tasks", count=len(due_tasks))

            for task in due_tasks:
                await self._execute_task(task, db, service)

        finally:
            db.close()

    async def _execute_task(self, task: ScheduledTask, db: Session, service: ScheduledTaskService):
        """Execute a single scheduled task."""
        logger.info(
            "executing_task",
            task_id=str(task.id),
            title=task.title,
            task_type=task.task_type,
        )

        try:
            # Record execution as running
            execution = service.record_execution(
                task_id=task.id,
                status="running",
            )

            result = None
            error_message = None

            # Execute based on task type
            if task.task_type == "reminder":
                result = await self._execute_reminder(task)
            elif task.task_type == "scheduled_query":
                result = await self._execute_query(task)
            elif task.task_type == "recurring_report":
                result = await self._execute_report(task)
            else:
                error_message = f"Unknown task type: {task.task_type}"

            # Update execution status
            if error_message:
                execution.status = "failed"
                execution.error_message = error_message
            else:
                execution.status = "completed"
                execution.result = result

            execution.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                "task_execution_complete",
                task_id=str(task.id),
                status=execution.status,
            )

            # Send notifications if configured
            if task.notify_via:
                await self._send_notifications(task, result, error_message)

        except Exception as e:
            logger.error(
                "task_execution_failed",
                task_id=str(task.id),
                error=str(e),
            )
            # Record failure
            service.record_execution(
                task_id=task.id,
                status="failed",
                error_message=str(e),
            )

    async def _execute_reminder(self, task: ScheduledTask) -> str:
        """Execute a reminder task."""
        # Reminders just need to trigger notifications
        # The result is the reminder message
        message = task.description or task.title
        return f"Reminder: {message}"

    async def _execute_query(self, task: ScheduledTask) -> str:
        """Execute a scheduled query using the AI agent."""
        if not task.agent_prompt:
            return "No query prompt specified"

        try:
            # Build agent and execute query
            agent = build_tool_agent(self.settings)
            result = await agent.invoke(task.agent_prompt)

            response = result.get("response", "No response from agent")
            return response

        except Exception as e:
            logger.error("agent_query_failed", task_id=str(task.id), error=str(e))
            raise

    async def _execute_report(self, task: ScheduledTask) -> str:
        """Execute a recurring report task."""
        if not task.agent_prompt:
            return "No report prompt specified"

        try:
            # Build agent and generate report
            agent = build_tool_agent(self.settings)
            result = await agent.invoke(task.agent_prompt)

            response = result.get("response", "No response from agent")
            return f"Report generated:\n\n{response}"

        except Exception as e:
            logger.error("report_generation_failed", task_id=str(task.id), error=str(e))
            raise

    async def _send_notifications(self, task: ScheduledTask, result: Optional[str], error: Optional[str]):
        """Send notifications based on task configuration."""
        notify_config = task.notify_via or {}

        message = error if error else result
        title = f"Task: {task.title}"

        if notify_config.get("push"):
            await self._send_push_notification(task, title, message)

        if notify_config.get("email"):
            await self._send_email_notification(task, title, message)

        if notify_config.get("whatsapp"):
            await self._send_whatsapp_notification(task, title, message)

    async def _send_push_notification(self, task: ScheduledTask, title: str, message: str):
        """Send push notification (placeholder for future implementation)."""
        logger.info(
            "push_notification_sent",
            task_id=str(task.id),
            title=title,
        )

    async def _send_email_notification(self, task: ScheduledTask, title: str, message: str):
        """Send email notification (placeholder for future implementation)."""
        logger.info(
            "email_notification_sent",
            task_id=str(task.id),
            title=title,
        )

    async def _send_whatsapp_notification(self, task: ScheduledTask, title: str, message: str):
        """Send WhatsApp notification (placeholder for future implementation)."""
        logger.info(
            "whatsapp_notification_sent",
            task_id=str(task.id),
            title=title,
        )


# Global scheduler instance
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


async def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler."""
    global _scheduler
    if _scheduler:
        await _scheduler.stop()
        _scheduler = None
