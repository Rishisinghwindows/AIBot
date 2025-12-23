from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Profile fields
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)  # language, theme, AI settings

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    integration_credentials: Mapped[list["IntegrationCredential"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    birth_details: Mapped[Optional["UserBirthDetails"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    mcp_tools: Mapped[list["MCPTool"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    scheduled_tasks: Mapped[list["ScheduledTask"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    personas: Mapped[list["Persona"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_firebase_uid", "firebase_uid"),
        Index("idx_users_email", "email"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_expires_at", "expires_at"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="chat_messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_role"),
        Index("idx_chat_messages_user_id", "user_id"),
        Index("idx_chat_messages_conversation_id", "conversation_id"),
        Index("idx_chat_messages_created_at", "created_at"),
    )


class UsedNonce(Base):
    __tablename__ = "used_nonces"

    nonce: Mapped[str] = mapped_column(String(64), primary_key=True)
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_used_nonces_expires_at", "expires_at"),)


class IntegrationCredential(Base):
    """
    Stores external provider credentials (API key/OAuth token) per user.
    """

    __tablename__ = "integration_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    user: Mapped["User"] = relationship(back_populates="integration_credentials")

    __table_args__ = (
        Index("idx_integration_credentials_user_provider", "user_id", "provider", unique=True),
    )


class UserBirthDetails(Base):
    """
    Stores birth details for astrology features.
    """

    __tablename__ = "user_birth_details"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # DD-MM-YYYY
    birth_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    birth_place: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    zodiac_sign: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    moon_sign: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nakshatra: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)  # For additional astro data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    user: Mapped["User"] = relationship(back_populates="birth_details")

    __table_args__ = (
        Index("idx_user_birth_details_user_id", "user_id"),
    )


class WebSession(Base):
    """
    Persistent web chat sessions for long-term context.
    Stores session data and chat history in PostgreSQL.
    """

    __tablename__ = "web_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    message_count: Mapped[int] = mapped_column(default=0)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    context_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # LLM-generated summary
    session_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    messages: Mapped[list["WebChatHistory"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_web_sessions_token", "session_token"),
        Index("idx_web_sessions_expires_at", "expires_at"),
    )


class WebChatHistory(Base):
    """
    Stores individual chat messages for web sessions.
    Enables long-term context persistence.
    """

    __tablename__ = "web_chat_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("web_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Detected intent
    media_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    # Relationships
    session: Mapped["WebSession"] = relationship(back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_web_chat_role"),
        Index("idx_web_chat_history_session_id", "session_id"),
        Index("idx_web_chat_history_created_at", "created_at"),
    )


class Conversation(Base):
    """
    Named conversation threads for authenticated users.
    """

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations")

    __table_args__ = (
        Index("idx_conversations_user_id", "user_id"),
        Index("idx_conversations_updated_at", "updated_at"),
    )


class MCPTool(Base):
    """
    User-configured MCP tools/integrations.
    """

    __tablename__ = "mcp_tools"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_type: Mapped[str] = mapped_column(String(50), nullable=False)  # oauth, api_key, mcp
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="mcp_tools")

    __table_args__ = (
        Index("idx_mcp_tools_user_id", "user_id"),
        Index("idx_mcp_tools_name", "user_id", "name", unique=True),
    )


class ConversationContext(Base):
    """
    Stores conversation context summaries for long-term memory.
    Periodically summarized by LLM to maintain context window.
    """

    __tablename__ = "conversation_contexts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    thread_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)  # LangGraph thread ID
    client_type: Mapped[str] = mapped_column(String(20), nullable=False)  # web, ios, whatsapp
    client_id: Mapped[str] = mapped_column(String(128), nullable=False)  # session_id, user_id, phone
    summary: Mapped[str] = mapped_column(Text, nullable=False)  # LLM-generated context summary
    key_entities: Mapped[dict] = mapped_column(JSONB, default=dict)  # Extracted entities (names, dates, etc.)
    message_count: Mapped[int] = mapped_column(default=0)
    last_intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("idx_conversation_contexts_thread_id", "thread_id"),
        Index("idx_conversation_contexts_client", "client_type", "client_id"),
    )


class ScheduledTask(Base):
    """
    User-scheduled tasks and reminders.
    Supports both one-time and recurring schedules.
    """

    __tablename__ = "scheduled_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # For anonymous users

    # Task details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # reminder, scheduled_query, recurring_report

    # Schedule configuration
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False)  # one_time, daily, weekly, monthly, cron
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # For one-time
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # For recurring
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    # Agent configuration
    agent_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # What the agent should do
    agent_config: Mapped[dict] = mapped_column(JSONB, default=dict)  # Additional config (tools, etc.)

    # Notification settings
    notify_via: Mapped[dict] = mapped_column(JSONB, default=dict)  # {push: true, email: false, whatsapp: true}

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, paused, completed, cancelled
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(default=0)
    max_runs: Mapped[Optional[int]] = mapped_column(nullable=True)  # Null = unlimited for recurring

    # Metadata
    task_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="scheduled_tasks")
    executions: Mapped[list["TaskExecution"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "schedule_type IN ('one_time', 'daily', 'weekly', 'monthly', 'cron')",
            name="check_schedule_type"
        ),
        CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'cancelled')",
            name="check_task_status"
        ),
        CheckConstraint(
            "user_id IS NOT NULL OR session_id IS NOT NULL",
            name="check_owner_exists"
        ),
        Index("idx_scheduled_tasks_user_id", "user_id"),
        Index("idx_scheduled_tasks_session_id", "session_id"),
        Index("idx_scheduled_tasks_next_run", "next_run_at"),
        Index("idx_scheduled_tasks_status", "status"),
    )


class TaskExecution(Base):
    """
    Logs execution history for scheduled tasks.
    """

    __tablename__ = "task_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scheduled_tasks.id", ondelete="CASCADE"), nullable=False
    )

    # Execution details
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, running, completed, failed
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Results
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Agent response
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)  # Timing, tokens used, etc.

    # Notification tracking
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_channels: Mapped[dict] = mapped_column(JSONB, default=dict)  # Which channels were notified

    # Relationships
    task: Mapped["ScheduledTask"] = relationship(back_populates="executions")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="check_execution_status"
        ),
        Index("idx_task_executions_task_id", "task_id"),
        Index("idx_task_executions_status", "status"),
        Index("idx_task_executions_started_at", "started_at"),
    )


# =====================
# AI Persona Models
# =====================

class Persona(Base):
    """
    AI Persona created by users.
    Trained with questionnaire data and optional documents.
    Accessible via shareable public URL.
    """

    __tablename__ = "personas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    handle: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # @username style
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tagline: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Short description
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Questionnaire data
    personality: Mapped[dict] = mapped_column(JSONB, default=dict)  # tone, style, interests
    professional: Mapped[dict] = mapped_column(JSONB, default=dict)  # role, skills, industry

    # System prompt generated from questionnaire
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    chat_limit: Mapped[int] = mapped_column(default=0)  # 0 = unlimited

    # Stats
    total_chats: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="personas")
    documents: Mapped[list["PersonaDocument"]] = relationship(
        back_populates="persona", cascade="all, delete-orphan"
    )
    chats: Mapped[list["PersonaChat"]] = relationship(
        back_populates="persona", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_personas_user_id", "user_id"),
        Index("idx_personas_handle", "handle"),
        Index("idx_personas_is_public", "is_public"),
    )


class PersonaDocument(Base):
    """
    Documents uploaded to train a persona (PDFs, etc.).
    Used for RAG-based persona responses.
    """

    __tablename__ = "persona_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(default=0)  # bytes
    chunk_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    # Relationships
    persona: Mapped["Persona"] = relationship(back_populates="documents")

    __table_args__ = (
        Index("idx_persona_documents_persona_id", "persona_id"),
    )


class PersonaChat(Base):
    """
    Chat sessions with a public persona.
    Anonymous visitors use session-based identification.
    """

    __tablename__ = "persona_chats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    persona_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False
    )
    visitor_session: Mapped[str] = mapped_column(String(64), nullable=False)  # Anonymous session ID
    visitor_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    persona: Mapped["Persona"] = relationship(back_populates="chats")
    messages: Mapped[list["PersonaChatMessage"]] = relationship(
        back_populates="chat", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_persona_chats_persona_id", "persona_id"),
        Index("idx_persona_chats_visitor_session", "visitor_session"),
    )


class PersonaChatMessage(Base):
    """
    Individual messages in a persona chat session.
    """

    __tablename__ = "persona_chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persona_chats.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    # Relationships
    chat: Mapped["PersonaChat"] = relationship(back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="check_persona_message_role"),
        Index("idx_persona_chat_messages_chat_id", "chat_id"),
        Index("idx_persona_chat_messages_created_at", "created_at"),
    )
