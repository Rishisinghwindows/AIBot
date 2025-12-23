"""add scheduled tasks

Revision ID: 000003
Revises: 000002
Create Date: 2025-12-21 15:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scheduled_tasks table
    op.create_table(
        'scheduled_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('schedule_type', sa.String(20), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('timezone', sa.String(50), server_default='UTC'),
        sa.Column('agent_prompt', sa.Text(), nullable=True),
        sa.Column('agent_config', postgresql.JSONB(), server_default='{}'),
        sa.Column('notify_via', postgresql.JSONB(), server_default='{}'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_count', sa.Integer(), server_default='0'),
        sa.Column('max_runs', sa.Integer(), nullable=True),
        sa.Column('task_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint(
            "schedule_type IN ('one_time', 'daily', 'weekly', 'monthly', 'cron')",
            name='check_schedule_type'
        ),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'cancelled')",
            name='check_task_status'
        ),
        sa.CheckConstraint(
            "user_id IS NOT NULL OR session_id IS NOT NULL",
            name='check_owner_exists'
        ),
    )

    # Create indexes for scheduled_tasks
    op.create_index('idx_scheduled_tasks_user_id', 'scheduled_tasks', ['user_id'])
    op.create_index('idx_scheduled_tasks_session_id', 'scheduled_tasks', ['session_id'])
    op.create_index('idx_scheduled_tasks_next_run', 'scheduled_tasks', ['next_run_at'])
    op.create_index('idx_scheduled_tasks_status', 'scheduled_tasks', ['status'])

    # Create task_executions table
    op.create_table(
        'task_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scheduled_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('notification_sent', sa.Boolean(), server_default='false'),
        sa.Column('notification_channels', postgresql.JSONB(), server_default='{}'),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name='check_execution_status'
        ),
    )

    # Create indexes for task_executions
    op.create_index('idx_task_executions_task_id', 'task_executions', ['task_id'])
    op.create_index('idx_task_executions_status', 'task_executions', ['status'])
    op.create_index('idx_task_executions_started_at', 'task_executions', ['started_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_task_executions_started_at')
    op.drop_index('idx_task_executions_status')
    op.drop_index('idx_task_executions_task_id')
    op.drop_index('idx_scheduled_tasks_status')
    op.drop_index('idx_scheduled_tasks_next_run')
    op.drop_index('idx_scheduled_tasks_session_id')
    op.drop_index('idx_scheduled_tasks_user_id')

    # Drop tables
    op.drop_table('task_executions')
    op.drop_table('scheduled_tasks')
