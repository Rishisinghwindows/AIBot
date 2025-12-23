"""
Scheduled Tasks Service - handles CRUD operations for scheduled tasks.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID
import uuid

from croniter import croniter
from sqlalchemy.orm import Session

from app.db.models import ScheduledTask, TaskExecution
from app.logger import logger


class ScheduledTaskService:
    """Service for managing scheduled tasks."""

    def __init__(self, db: Session):
        self.db = db

    def create_task(
        self,
        title: str,
        task_type: str,
        schedule_type: str,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        cron_expression: Optional[str] = None,
        task_timezone: str = "UTC",
        agent_prompt: Optional[str] = None,
        agent_config: Optional[dict] = None,
        notify_via: Optional[dict] = None,
        max_runs: Optional[int] = None,
    ) -> ScheduledTask:
        """Create a new scheduled task."""
        # Calculate next run time
        next_run_at = self._calculate_next_run(
            schedule_type=schedule_type,
            scheduled_at=scheduled_at,
            cron_expression=cron_expression,
            task_timezone=task_timezone,
        )

        task = ScheduledTask(
            id=uuid.uuid4(),
            user_id=user_id,
            session_id=session_id,
            title=title,
            description=description,
            task_type=task_type,
            schedule_type=schedule_type,
            scheduled_at=scheduled_at,
            cron_expression=cron_expression,
            timezone=task_timezone,
            agent_prompt=agent_prompt,
            agent_config=agent_config or {},
            notify_via=notify_via or {},
            status="active",
            next_run_at=next_run_at,
            run_count=0,
            max_runs=max_runs,
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        logger.info(
            "scheduled_task_created",
            task_id=str(task.id),
            title=title,
            schedule_type=schedule_type,
            next_run_at=str(next_run_at) if next_run_at else None,
        )

        return task

    def get_task(self, task_id: UUID, user_id: Optional[UUID] = None, session_id: Optional[str] = None) -> Optional[ScheduledTask]:
        """Get a task by ID, optionally filtered by owner."""
        query = self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id)

        if user_id:
            query = query.filter(ScheduledTask.user_id == user_id)
        elif session_id:
            query = query.filter(ScheduledTask.session_id == session_id)

        return query.first()

    def get_tasks(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ScheduledTask], int, bool]:
        """Get tasks for a user or session."""
        query = self.db.query(ScheduledTask)

        if user_id:
            query = query.filter(ScheduledTask.user_id == user_id)
        elif session_id:
            query = query.filter(ScheduledTask.session_id == session_id)

        if status:
            query = query.filter(ScheduledTask.status == status)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        tasks = query.order_by(ScheduledTask.created_at.desc()).offset(offset).limit(limit + 1).all()

        has_more = len(tasks) > limit
        if has_more:
            tasks = tasks[:limit]

        return tasks, total, has_more

    def update_task(
        self,
        task_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Optional[ScheduledTask]:
        """Update a scheduled task."""
        task = self.get_task(task_id, user_id=user_id, session_id=session_id)
        if not task:
            return None

        # Update fields
        for key, value in kwargs.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)

        # Recalculate next_run_at if schedule changed
        if 'schedule_type' in kwargs or 'scheduled_at' in kwargs or 'cron_expression' in kwargs:
            task.next_run_at = self._calculate_next_run(
                schedule_type=task.schedule_type,
                scheduled_at=task.scheduled_at,
                cron_expression=task.cron_expression,
                task_timezone=task.timezone,
            )

        self.db.commit()
        self.db.refresh(task)

        logger.info("scheduled_task_updated", task_id=str(task_id))

        return task

    def delete_task(self, task_id: UUID, user_id: Optional[UUID] = None, session_id: Optional[str] = None) -> bool:
        """Delete a scheduled task."""
        task = self.get_task(task_id, user_id=user_id, session_id=session_id)
        if not task:
            return False

        self.db.delete(task)
        self.db.commit()

        logger.info("scheduled_task_deleted", task_id=str(task_id))

        return True

    def pause_task(self, task_id: UUID, user_id: Optional[UUID] = None, session_id: Optional[str] = None) -> Optional[ScheduledTask]:
        """Pause a scheduled task."""
        return self.update_task(task_id, user_id=user_id, session_id=session_id, status="paused")

    def resume_task(self, task_id: UUID, user_id: Optional[UUID] = None, session_id: Optional[str] = None) -> Optional[ScheduledTask]:
        """Resume a paused task."""
        task = self.get_task(task_id, user_id=user_id, session_id=session_id)
        if not task or task.status != "paused":
            return None

        # Recalculate next run time
        task.next_run_at = self._calculate_next_run(
            schedule_type=task.schedule_type,
            scheduled_at=task.scheduled_at,
            cron_expression=task.cron_expression,
            task_timezone=task.timezone,
        )
        task.status = "active"

        self.db.commit()
        self.db.refresh(task)

        return task

    def get_due_tasks(self, limit: int = 100) -> List[ScheduledTask]:
        """Get tasks that are due to run."""
        now = datetime.now(timezone.utc)

        return (
            self.db.query(ScheduledTask)
            .filter(
                ScheduledTask.status == "active",
                ScheduledTask.next_run_at <= now,
            )
            .limit(limit)
            .all()
        )

    def record_execution(
        self,
        task_id: UUID,
        status: str,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        execution_metadata: Optional[dict] = None,
    ) -> TaskExecution:
        """Record a task execution."""
        now = datetime.now(timezone.utc)

        execution = TaskExecution(
            id=uuid.uuid4(),
            task_id=task_id,
            status=status,
            started_at=now,
            completed_at=now if status in ["completed", "failed"] else None,
            result=result,
            error_message=error_message,
            execution_metadata=execution_metadata or {},
        )

        self.db.add(execution)

        # Update the task
        task = self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            task.last_run_at = now
            task.run_count += 1

            # Check if task should be completed
            if task.schedule_type == "one_time":
                task.status = "completed"
                task.next_run_at = None
            elif task.max_runs and task.run_count >= task.max_runs:
                task.status = "completed"
                task.next_run_at = None
            else:
                # Calculate next run time
                task.next_run_at = self._calculate_next_run(
                    schedule_type=task.schedule_type,
                    scheduled_at=task.scheduled_at,
                    cron_expression=task.cron_expression,
                    task_timezone=task.timezone,
                    from_time=now,
                )

        self.db.commit()
        self.db.refresh(execution)

        logger.info(
            "task_execution_recorded",
            task_id=str(task_id),
            execution_id=str(execution.id),
            status=status,
        )

        return execution

    def get_executions(
        self,
        task_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[TaskExecution], int, bool]:
        """Get execution history for a task."""
        query = self.db.query(TaskExecution).filter(TaskExecution.task_id == task_id)

        total = query.count()

        executions = (
            query.order_by(TaskExecution.started_at.desc())
            .offset(offset)
            .limit(limit + 1)
            .all()
        )

        has_more = len(executions) > limit
        if has_more:
            executions = executions[:limit]

        return executions, total, has_more

    def _calculate_next_run(
        self,
        schedule_type: str,
        scheduled_at: Optional[datetime] = None,
        cron_expression: Optional[str] = None,
        task_timezone: str = "UTC",
        from_time: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """Calculate the next run time based on schedule configuration."""
        now = from_time or datetime.now(timezone.utc)

        if schedule_type == "one_time":
            if scheduled_at and scheduled_at > now:
                return scheduled_at
            return None

        elif schedule_type == "daily":
            # Run at the same time tomorrow
            next_run = now + timedelta(days=1)
            return next_run.replace(hour=9, minute=0, second=0, microsecond=0)

        elif schedule_type == "weekly":
            # Run next week at the same time
            days_until_next = 7 - now.weekday()
            next_run = now + timedelta(days=days_until_next)
            return next_run.replace(hour=9, minute=0, second=0, microsecond=0)

        elif schedule_type == "monthly":
            # Run on the 1st of next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_run = now.replace(month=now.month + 1, day=1)
            return next_run.replace(hour=9, minute=0, second=0, microsecond=0)

        elif schedule_type == "cron" and cron_expression:
            try:
                cron = croniter(cron_expression, now)
                return cron.get_next(datetime)
            except Exception as e:
                logger.error("cron_parse_error", expression=cron_expression, error=str(e))
                return None

        return None

    def preview_schedule(
        self,
        schedule_type: str,
        scheduled_at: Optional[datetime] = None,
        cron_expression: Optional[str] = None,
        task_timezone: str = "UTC",
        count: int = 5,
    ) -> Tuple[List[datetime], str]:
        """Preview upcoming run times for a schedule."""
        next_runs = []
        current_time = datetime.now(timezone.utc)

        for _ in range(count):
            next_run = self._calculate_next_run(
                schedule_type=schedule_type,
                scheduled_at=scheduled_at,
                cron_expression=cron_expression,
                task_timezone=task_timezone,
                from_time=current_time,
            )
            if next_run:
                next_runs.append(next_run)
                current_time = next_run + timedelta(seconds=1)
            else:
                break

        # Generate human-readable description
        description = self._schedule_description(schedule_type, cron_expression)

        return next_runs, description

    def _schedule_description(self, schedule_type: str, cron_expression: Optional[str] = None) -> str:
        """Generate a human-readable description of the schedule."""
        if schedule_type == "one_time":
            return "Runs once at the scheduled time"
        elif schedule_type == "daily":
            return "Runs every day at 9:00 AM"
        elif schedule_type == "weekly":
            return "Runs every Monday at 9:00 AM"
        elif schedule_type == "monthly":
            return "Runs on the 1st of every month at 9:00 AM"
        elif schedule_type == "cron" and cron_expression:
            return f"Custom schedule: {cron_expression}"
        return "Unknown schedule"
