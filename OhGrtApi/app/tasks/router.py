"""
Scheduled Tasks Router - API endpoints for managing scheduled tasks.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_optional_user
from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import User
from app.logger import logger
from app.tasks.models import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
    ScheduledTaskListResponse,
    TaskExecutionResponse,
    TaskExecutionListResponse,
    SchedulePreview,
    TaskScheduleConfig,
)
from app.tasks.service import ScheduledTaskService

router = APIRouter(prefix="/tasks", tags=["scheduled-tasks"])


def _task_to_response(task) -> ScheduledTaskResponse:
    """Convert a ScheduledTask model to response."""
    return ScheduledTaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        schedule_type=task.schedule_type,
        scheduled_at=task.scheduled_at,
        cron_expression=task.cron_expression,
        timezone=task.timezone,
        agent_prompt=task.agent_prompt,
        agent_config=task.agent_config or {},
        notify_via=task.notify_via or {},
        status=task.status,
        next_run_at=task.next_run_at,
        last_run_at=task.last_run_at,
        run_count=task.run_count,
        max_runs=task.max_runs,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _execution_to_response(execution) -> TaskExecutionResponse:
    """Convert a TaskExecution model to response."""
    return TaskExecutionResponse(
        id=execution.id,
        task_id=execution.task_id,
        status=execution.status,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        result=execution.result,
        error_message=execution.error_message,
        execution_metadata=execution.execution_metadata or {},
        notification_sent=execution.notification_sent,
        notification_channels=execution.notification_channels or {},
    )


# =============================================================================
# AUTHENTICATED ENDPOINTS
# =============================================================================


@router.post(
    "",
    response_model=ScheduledTaskResponse,
    status_code=201,
    summary="Create a scheduled task",
    description="""
Create a new scheduled task for the authenticated user.

## Task Types
- `reminder`: Simple reminder notification
- `scheduled_query`: AI agent query that runs at scheduled time
- `recurring_report`: Periodic report generation

## Schedule Types
- `one_time`: Runs once at the specified time
- `daily`: Runs every day at 9:00 AM
- `weekly`: Runs every Monday at 9:00 AM
- `monthly`: Runs on the 1st of every month
- `cron`: Custom cron expression for advanced scheduling
    """,
)
async def create_task(
    request: ScheduledTaskCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Create a new scheduled task."""
    service = ScheduledTaskService(db)

    task = service.create_task(
        user_id=user.id,
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        schedule_type=request.schedule.schedule_type,
        scheduled_at=request.schedule.scheduled_at,
        cron_expression=request.schedule.cron_expression,
        task_timezone=request.schedule.timezone,
        agent_prompt=request.agent_prompt,
        agent_config=request.agent_config,
        notify_via=request.notify_via.model_dump() if request.notify_via else {},
        max_runs=request.max_runs,
    )

    return _task_to_response(task)


@router.get(
    "",
    response_model=ScheduledTaskListResponse,
    summary="List scheduled tasks",
)
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status: active, paused, completed, cancelled"),
    limit: int = Query(50, ge=1, le=100, description="Maximum tasks to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledTaskListResponse:
    """List all scheduled tasks for the authenticated user."""
    service = ScheduledTaskService(db)
    tasks, total, has_more = service.get_tasks(
        user_id=user.id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return ScheduledTaskListResponse(
        tasks=[_task_to_response(task) for task in tasks],
        total=total,
        has_more=has_more,
    )


@router.get(
    "/{task_id}",
    response_model=ScheduledTaskResponse,
    summary="Get a scheduled task",
)
async def get_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Get details of a specific scheduled task."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)
    task = service.get_task(task_uuid, user_id=user.id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_to_response(task)


@router.put(
    "/{task_id}",
    response_model=ScheduledTaskResponse,
    summary="Update a scheduled task",
)
async def update_task(
    task_id: str,
    request: ScheduledTaskUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Update a scheduled task."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)

    # Build update kwargs
    update_kwargs = {}
    if request.title is not None:
        update_kwargs["title"] = request.title
    if request.description is not None:
        update_kwargs["description"] = request.description
    if request.schedule is not None:
        update_kwargs["schedule_type"] = request.schedule.schedule_type
        update_kwargs["scheduled_at"] = request.schedule.scheduled_at
        update_kwargs["cron_expression"] = request.schedule.cron_expression
        update_kwargs["timezone"] = request.schedule.timezone
    if request.agent_prompt is not None:
        update_kwargs["agent_prompt"] = request.agent_prompt
    if request.agent_config is not None:
        update_kwargs["agent_config"] = request.agent_config
    if request.notify_via is not None:
        update_kwargs["notify_via"] = request.notify_via.model_dump()
    if request.status is not None:
        update_kwargs["status"] = request.status
    if request.max_runs is not None:
        update_kwargs["max_runs"] = request.max_runs

    task = service.update_task(task_uuid, user_id=user.id, **update_kwargs)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_to_response(task)


@router.delete(
    "/{task_id}",
    summary="Delete a scheduled task",
)
async def delete_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a scheduled task."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)
    deleted = service.delete_task(task_uuid, user_id=user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted successfully"}


@router.post(
    "/{task_id}/pause",
    response_model=ScheduledTaskResponse,
    summary="Pause a scheduled task",
)
async def pause_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Pause a scheduled task."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)
    task = service.pause_task(task_uuid, user_id=user.id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_to_response(task)


@router.post(
    "/{task_id}/resume",
    response_model=ScheduledTaskResponse,
    summary="Resume a paused task",
)
async def resume_task(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Resume a paused scheduled task."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)
    task = service.resume_task(task_uuid, user_id=user.id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not paused")

    return _task_to_response(task)


@router.get(
    "/{task_id}/executions",
    response_model=TaskExecutionListResponse,
    summary="Get task execution history",
)
async def get_task_executions(
    task_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskExecutionListResponse:
    """Get execution history for a scheduled task."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)

    # Verify task ownership
    task = service.get_task(task_uuid, user_id=user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    executions, total, has_more = service.get_executions(task_uuid, limit=limit, offset=offset)

    return TaskExecutionListResponse(
        executions=[_execution_to_response(ex) for ex in executions],
        total=total,
        has_more=has_more,
    )


@router.post(
    "/preview",
    response_model=SchedulePreview,
    summary="Preview schedule",
)
async def preview_schedule(
    schedule: TaskScheduleConfig,
    count: int = Query(5, ge=1, le=10, description="Number of upcoming runs to preview"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SchedulePreview:
    """Preview upcoming run times for a schedule configuration."""
    service = ScheduledTaskService(db)

    next_runs, description = service.preview_schedule(
        schedule_type=schedule.schedule_type,
        scheduled_at=schedule.scheduled_at,
        cron_expression=schedule.cron_expression,
        task_timezone=schedule.timezone,
        count=count,
    )

    return SchedulePreview(next_runs=next_runs, schedule_description=description)


# =============================================================================
# PUBLIC ENDPOINTS (for anonymous users via web session)
# =============================================================================


web_router = APIRouter(prefix="/web/tasks", tags=["web-scheduled-tasks"])


@web_router.post(
    "",
    response_model=ScheduledTaskResponse,
    status_code=201,
    summary="Create a scheduled task (anonymous)",
)
async def create_web_task(
    request: ScheduledTaskCreate,
    session_id: str = Query(..., description="Anonymous session ID"),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Create a new scheduled task for an anonymous web session."""
    service = ScheduledTaskService(db)

    task = service.create_task(
        session_id=session_id,
        title=request.title,
        description=request.description,
        task_type=request.task_type,
        schedule_type=request.schedule.schedule_type,
        scheduled_at=request.schedule.scheduled_at,
        cron_expression=request.schedule.cron_expression,
        task_timezone=request.schedule.timezone,
        agent_prompt=request.agent_prompt,
        agent_config=request.agent_config,
        notify_via=request.notify_via.model_dump() if request.notify_via else {},
        max_runs=request.max_runs,
    )

    return _task_to_response(task)


@web_router.get(
    "",
    response_model=ScheduledTaskListResponse,
    summary="List scheduled tasks (anonymous)",
)
async def list_web_tasks(
    session_id: str = Query(..., description="Anonymous session ID"),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ScheduledTaskListResponse:
    """List scheduled tasks for an anonymous web session."""
    service = ScheduledTaskService(db)
    tasks, total, has_more = service.get_tasks(
        session_id=session_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return ScheduledTaskListResponse(
        tasks=[_task_to_response(task) for task in tasks],
        total=total,
        has_more=has_more,
    )


@web_router.get(
    "/{task_id}",
    response_model=ScheduledTaskResponse,
)
async def get_web_task(
    task_id: str,
    session_id: str = Query(..., description="Anonymous session ID"),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Get a scheduled task for an anonymous session."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)
    task = service.get_task(task_uuid, session_id=session_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_to_response(task)


@web_router.put(
    "/{task_id}",
    response_model=ScheduledTaskResponse,
)
async def update_web_task(
    task_id: str,
    request: ScheduledTaskUpdate,
    session_id: str = Query(..., description="Anonymous session ID"),
    db: Session = Depends(get_db),
) -> ScheduledTaskResponse:
    """Update a scheduled task for an anonymous session."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)

    # Build update kwargs
    update_kwargs = {}
    if request.title is not None:
        update_kwargs["title"] = request.title
    if request.description is not None:
        update_kwargs["description"] = request.description
    if request.schedule is not None:
        update_kwargs["schedule_type"] = request.schedule.schedule_type
        update_kwargs["scheduled_at"] = request.schedule.scheduled_at
        update_kwargs["cron_expression"] = request.schedule.cron_expression
        update_kwargs["timezone"] = request.schedule.timezone
    if request.agent_prompt is not None:
        update_kwargs["agent_prompt"] = request.agent_prompt
    if request.agent_config is not None:
        update_kwargs["agent_config"] = request.agent_config
    if request.notify_via is not None:
        update_kwargs["notify_via"] = request.notify_via.model_dump()
    if request.status is not None:
        update_kwargs["status"] = request.status
    if request.max_runs is not None:
        update_kwargs["max_runs"] = request.max_runs

    task = service.update_task(task_uuid, session_id=session_id, **update_kwargs)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_to_response(task)


@web_router.delete(
    "/{task_id}",
)
async def delete_web_task(
    task_id: str,
    session_id: str = Query(..., description="Anonymous session ID"),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a scheduled task for an anonymous session."""
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    service = ScheduledTaskService(db)
    deleted = service.delete_task(task_uuid, session_id=session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted successfully"}
