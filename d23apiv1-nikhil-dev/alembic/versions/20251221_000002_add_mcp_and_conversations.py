"""Add MCP tools and conversations tables

Revision ID: 002
Revises: 001
Create Date: 2025-12-21

Adds tables for:
- conversations: Named conversation threads
- mcp_tools: User-configured MCP tool integrations
- user_birth_details: Astrology data for users
- web_sessions: Web chat sessions
- web_chat_history: Web chat messages
- conversation_contexts: LangGraph conversation context
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentic.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='agentic'
    )
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'], schema='agentic')
    op.create_index('idx_conversations_updated_at', 'conversations', ['updated_at'], schema='agentic')

    # MCP Tools table
    op.create_table(
        'mcp_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentic.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tool_type', sa.String(50), nullable=False),
        sa.Column('config', postgresql.JSONB(), default={}),
        sa.Column('enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'name', name='uq_mcp_tools_user_name'),
        schema='agentic'
    )
    op.create_index('idx_mcp_tools_user_id', 'mcp_tools', ['user_id'], schema='agentic')

    # User birth details table (for astrology)
    op.create_table(
        'user_birth_details',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentic.users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('birth_date', sa.String(20), nullable=True),
        sa.Column('birth_time', sa.String(10), nullable=True),
        sa.Column('birth_place', sa.String(255), nullable=True),
        sa.Column('zodiac_sign', sa.String(20), nullable=True),
        sa.Column('moon_sign', sa.String(20), nullable=True),
        sa.Column('nakshatra', sa.String(50), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='agentic'
    )
    op.create_index('idx_user_birth_details_user_id', 'user_birth_details', ['user_id'], schema='agentic')

    # Web sessions table
    op.create_table(
        'web_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_token', sa.String(64), nullable=False, unique=True),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('context_summary', sa.Text(), nullable=True),
        sa.Column('session_metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        schema='agentic'
    )
    op.create_index('idx_web_sessions_token', 'web_sessions', ['session_token'], schema='agentic')
    op.create_index('idx_web_sessions_expires_at', 'web_sessions', ['expires_at'], schema='agentic')

    # Web chat history table
    op.create_table(
        'web_chat_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentic.web_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('media_url', sa.Text(), nullable=True),
        sa.Column('message_metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='ck_web_chat_history_role'),
        schema='agentic'
    )
    op.create_index('idx_web_chat_history_session_id', 'web_chat_history', ['session_id'], schema='agentic')
    op.create_index('idx_web_chat_history_created_at', 'web_chat_history', ['created_at'], schema='agentic')

    # Conversation contexts table (for LangGraph)
    op.create_table(
        'conversation_contexts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('thread_id', sa.String(128), nullable=False, unique=True),
        sa.Column('client_type', sa.String(20), nullable=False),
        sa.Column('client_id', sa.String(128), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('key_entities', postgresql.JSONB(), default={}),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('last_intent', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='agentic'
    )
    op.create_index('idx_conversation_contexts_thread_id', 'conversation_contexts', ['thread_id'], schema='agentic')
    op.create_index('idx_conversation_contexts_client', 'conversation_contexts', ['client_type', 'client_id'], schema='agentic')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('conversation_contexts', schema='agentic')
    op.drop_table('web_chat_history', schema='agentic')
    op.drop_table('web_sessions', schema='agentic')
    op.drop_table('user_birth_details', schema='agentic')
    op.drop_table('mcp_tools', schema='agentic')
    op.drop_table('conversations', schema='agentic')
