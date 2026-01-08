"""Add profile fields and persona models

Revision ID: 004
Revises: 003
Create Date: 2025-12-21

Adds:
- User profile fields (bio, preferences)
- Persona tables for AI persona feature
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add profile fields to users table
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('preferences', postgresql.JSONB(), server_default='{}', nullable=False))

    # Create personas table
    op.create_table(
        'personas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('handle', sa.String(50), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('tagline', sa.String(200), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('personality', postgresql.JSONB(), server_default='{}'),
        sa.Column('professional', postgresql.JSONB(), server_default='{}'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='true'),
        sa.Column('chat_limit', sa.Integer(), server_default='0'),
        sa.Column('total_chats', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_personas_user_id', 'personas', ['user_id'])
    op.create_index('idx_personas_handle', 'personas', ['handle'])
    op.create_index('idx_personas_is_public', 'personas', ['is_public'])

    # Create persona_documents table
    op.create_table(
        'persona_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('persona_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('personas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), server_default='0'),
        sa.Column('chunk_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_persona_documents_persona_id', 'persona_documents', ['persona_id'])

    # Create persona_chats table
    op.create_table(
        'persona_chats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('persona_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('personas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('visitor_session', sa.String(64), nullable=False),
        sa.Column('visitor_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_persona_chats_persona_id', 'persona_chats', ['persona_id'])
    op.create_index('idx_persona_chats_visitor_session', 'persona_chats', ['visitor_session'])

    # Create persona_chat_messages table
    op.create_table(
        'persona_chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('persona_chats.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='check_persona_message_role'),
    )
    op.create_index('idx_persona_chat_messages_chat_id', 'persona_chat_messages', ['chat_id'])
    op.create_index('idx_persona_chat_messages_created_at', 'persona_chat_messages', ['created_at'])


def downgrade() -> None:
    # Drop indexes and tables in reverse order
    op.drop_index('idx_persona_chat_messages_created_at')
    op.drop_index('idx_persona_chat_messages_chat_id')
    op.drop_table('persona_chat_messages')

    op.drop_index('idx_persona_chats_visitor_session')
    op.drop_index('idx_persona_chats_persona_id')
    op.drop_table('persona_chats')

    op.drop_index('idx_persona_documents_persona_id')
    op.drop_table('persona_documents')

    op.drop_index('idx_personas_is_public')
    op.drop_index('idx_personas_handle')
    op.drop_index('idx_personas_user_id')
    op.drop_table('personas')

    # Remove profile fields from users
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'bio')
