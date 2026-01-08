"""
Pydantic models for scheduled tasks API.
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TaskScheduleConfig(BaseModel):
    """Schedule configuration for a task."""
    schedule_type: str = Field(..., description="Schedule type: one_time, daily, weekly, monthly, cron")
    scheduled_at: Optional[datetime] = Field(None, description="For one-time tasks: when to run")
    cron_expression: Optional[str] = Field(None, description="For recurring tasks: cron expression")
    timezone: str = Field("UTC", description="Timezone for the schedule")

    @field_validator('schedule_type')
    @classmethod
    def validate_schedule_type(cls, v):
        valid_types = ['one_time', 'daily', 'weekly', 'monthly', 'cron']
        if v not in valid_types:
            raise ValueError(f"schedule_type must be one of: {', '.join(valid_types)}")
        return v


class TaskNotifyConfig(BaseModel):
    """Notification configuration for a task."""
    push: bool = Field(False, description="Send push notification")
    email: bool = Field(False, description="Send email notification")
    whatsapp: bool = Field(False, description="Send WhatsApp notification")


class ScheduledTaskCreate(BaseModel):
    """Request model for creating a scheduled task."""
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    task_type: str = Field("reminder", description="Task type: reminder, scheduled_query, recurring_report")
    schedule: TaskScheduleConfig = Field(..., description="Schedule configuration")
    agent_prompt: Optional[str] = Field(None, description="Prompt for the AI agent to execute")
    agent_config: Dict = Field(default_factory=dict, description="Additional agent configuration")
    notify_via: TaskNotifyConfig = Field(default_factory=TaskNotifyConfig, description="Notification settings")
    max_runs: Optional[int] = Field(None, description="Maximum number of runs (null for unlimited)")

    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v):
        valid_types = ['reminder', 'scheduled_query', 'recurring_report']
        if v not in valid_types:
            raise ValueError(f"task_type must be one of: {', '.join(valid_types)}")
        return v


class ScheduledTaskUpdate(BaseModel):
    """Request model for updating a scheduled task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    schedule: Optional[TaskScheduleConfig] = None
    agent_prompt: Optional[str] = None
    agent_config: Optional[Dict] = None
    notify_via: Optional[TaskNotifyConfig] = None
    status: Optional[str] = None
    max_runs: Optional[int] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        valid_statuses = ['active', 'paused', 'completed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v


class ScheduledTaskResponse(BaseModel):
    """Response model for a scheduled task."""
    id: UUID
    title: str
    description: Optional[str]
    task_type: str
    schedule_type: str
    scheduled_at: Optional[datetime]
    cron_expression: Optional[str]
    timezone: str
    agent_prompt: Optional[str]
    agent_config: Dict
    notify_via: Dict
    status: str
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    run_count: int
    max_runs: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskExecutionResponse(BaseModel):
    """Response model for a task execution."""
    id: UUID
    task_id: UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[str]
    error_message: Optional[str]
    execution_metadata: Dict
    notification_sent: bool
    notification_channels: Dict

    class Config:
        from_attributes = True


class ScheduledTaskListResponse(BaseModel):
    """Response model for listing scheduled tasks."""
    tasks: List[ScheduledTaskResponse]
    total: int
    has_more: bool


class TaskExecutionListResponse(BaseModel):
    """Response model for listing task executions."""
    executions: List[TaskExecutionResponse]
    total: int
    has_more: bool


class SchedulePreview(BaseModel):
    """Preview upcoming run times for a schedule."""
    next_runs: List[datetime]
    schedule_description: str
