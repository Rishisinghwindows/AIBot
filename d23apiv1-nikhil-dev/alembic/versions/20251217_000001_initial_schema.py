"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-12-17

Creates all initial tables for OhGrt application.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create schema if not exists
    op.execute(text("CREATE SCHEMA IF NOT EXISTS agentic"))

    # Note: pgvector extension can be enabled manually if needed:
    # CREATE EXTENSION IF NOT EXISTS vector;

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('firebase_uid', sa.String(128), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        schema='agentic'
    )
    op.create_index('idx_users_firebase_uid', 'users', ['firebase_uid'], schema='agentic')
    op.create_index('idx_users_email', 'users', ['email'], schema='agentic')

    # Refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentic.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('device_info', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        schema='agentic'
    )
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], schema='agentic')
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'], schema='agentic')

    # Chat messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentic.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='ck_chat_messages_role'),
        schema='agentic'
    )
    op.create_index('idx_chat_messages_user_id', 'chat_messages', ['user_id'], schema='agentic')
    op.create_index('idx_chat_messages_conversation_id', 'chat_messages', ['conversation_id'], schema='agentic')
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'], schema='agentic')

    # Used nonces table (for replay attack prevention)
    op.create_table(
        'used_nonces',
        sa.Column('nonce', sa.String(64), primary_key=True),
        sa.Column('used_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        schema='agentic'
    )
    op.create_index('idx_used_nonces_expires_at', 'used_nonces', ['expires_at'], schema='agentic')

    # Integration credentials table
    op.create_table(
        'integration_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentic.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'provider', name='uq_integration_credentials_user_provider'),
        schema='agentic'
    )
    op.create_index('idx_integration_credentials_user_provider', 'integration_credentials', ['user_id', 'provider'], schema='agentic')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('integration_credentials', schema='agentic')
    op.drop_table('used_nonces', schema='agentic')
    op.drop_table('chat_messages', schema='agentic')
    op.drop_table('refresh_tokens', schema='agentic')
    op.drop_table('users', schema='agentic')

    # Don't drop schema or extension as they may be used by other things
