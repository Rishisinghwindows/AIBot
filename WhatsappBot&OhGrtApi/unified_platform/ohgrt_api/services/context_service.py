"""
Context Persistence Service

Provides long-term conversation context storage and retrieval.
Uses PostgreSQL for durable storage and LLM for context summarization.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from ohgrt_api.config import get_settings
from ohgrt_api.db.base import SessionLocal
from ohgrt_api.db.models import WebSession, WebChatHistory, ConversationContext, WhatsAppChatMessage
from ohgrt_api.logger import logger


class ContextService:
    """
    Service for managing long-term conversation context.

    Features:
    - Stores chat history in PostgreSQL
    - Generates context summaries using LLM
    - Provides context retrieval for LangGraph
    - Manages session lifecycle
    """

    def __init__(self):
        self.settings = get_settings()
        self._llm = None

    @property
    def llm(self):
        """Lazy-load LLM for context summarization."""
        if self._llm is None:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model=self.settings.openai_model,
                temperature=0.3,
                api_key=self.settings.openai_api_key,
            )
        return self._llm

    def _get_db(self) -> Session:
        """Get database session."""
        return SessionLocal()

    def generate_thread_id(self, client_type: str, client_id: str) -> str:
        """
        Generate a unique thread ID for LangGraph checkpointing.

        Args:
            client_type: Type of client (web, ios, whatsapp)
            client_id: Client identifier (session_id, user_id, phone)

        Returns:
            Unique thread ID for this conversation
        """
        # Create a stable hash for the thread
        raw = f"{client_type}:{client_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    # =========================================================================
    # WEB SESSION MANAGEMENT
    # =========================================================================

    async def create_web_session(
        self,
        session_token: str,
        language: str = "en",
        ttl_hours: int = 24,
    ) -> WebSession:
        """
        Create a new web session in the database.

        Args:
            session_token: Unique session token
            language: User's preferred language
            ttl_hours: Session lifetime in hours

        Returns:
            Created WebSession object
        """
        db = self._get_db()
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

            session = WebSession(
                session_token=session_token,
                language=language,
                expires_at=expires_at,
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            logger.info("context_session_created", session_token=session_token[:8])
            return session
        except Exception as e:
            db.rollback()
            logger.error("context_session_create_error", error=str(e))
            raise
        finally:
            db.close()

    async def get_web_session(self, session_token: str) -> Optional[WebSession]:
        """
        Get a web session by token.

        Args:
            session_token: Session token to look up

        Returns:
            WebSession if found and not expired, None otherwise
        """
        db = self._get_db()
        try:
            stmt = select(WebSession).where(
                WebSession.session_token == session_token,
                WebSession.expires_at > datetime.now(timezone.utc),
            )
            result = db.execute(stmt).scalar_one_or_none()
            return result
        finally:
            db.close()

    async def update_web_session(
        self,
        session_token: str,
        **kwargs,
    ) -> Optional[WebSession]:
        """Update a web session."""
        db = self._get_db()
        try:
            stmt = select(WebSession).where(WebSession.session_token == session_token)
            session = db.execute(stmt).scalar_one_or_none()

            if session:
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                session.last_message_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(session)

            return session
        except Exception as e:
            db.rollback()
            logger.error("context_session_update_error", error=str(e))
            raise
        finally:
            db.close()

    async def delete_web_session(self, session_token: str) -> bool:
        """Delete a web session and all its messages."""
        db = self._get_db()
        try:
            stmt = select(WebSession).where(WebSession.session_token == session_token)
            session = db.execute(stmt).scalar_one_or_none()

            if session:
                db.delete(session)
                db.commit()
                logger.info("context_session_deleted", session_token=session_token[:8])
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error("context_session_delete_error", error=str(e))
            raise
        finally:
            db.close()

    # =========================================================================
    # CHAT HISTORY MANAGEMENT
    # =========================================================================

    async def add_message(
        self,
        session_token: str,
        role: str,
        content: str,
        language: str = "en",
        intent: Optional[str] = None,
        media_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[WebChatHistory]:
        """
        Add a message to session history.

        Args:
            session_token: Session token
            role: Message role (user, assistant, system)
            content: Message content
            language: Message language
            intent: Detected intent (optional)
            media_url: Media URL if any
            metadata: Additional metadata

        Returns:
            Created WebChatHistory object
        """
        db = self._get_db()
        try:
            # Get session
            stmt = select(WebSession).where(WebSession.session_token == session_token)
            session = db.execute(stmt).scalar_one_or_none()

            if not session:
                logger.warning("context_add_message_no_session", session_token=session_token[:8])
                return None

            # Create message
            message = WebChatHistory(
                session_id=session.id,
                role=role,
                content=content,
                language=language,
                intent=intent,
                media_url=media_url,
                message_metadata=metadata or {},
            )
            db.add(message)

            # Update session
            session.message_count += 1
            session.last_message_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(message)

            return message
        except Exception as e:
            db.rollback()
            logger.error("context_add_message_error", error=str(e))
            raise
        finally:
            db.close()

    async def get_messages(
        self,
        session_token: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WebChatHistory]:
        """
        Get messages for a session.

        Args:
            session_token: Session token
            limit: Maximum messages to return
            offset: Offset for pagination

        Returns:
            List of WebChatHistory objects
        """
        db = self._get_db()
        try:
            # Get session
            stmt = select(WebSession).where(WebSession.session_token == session_token)
            session = db.execute(stmt).scalar_one_or_none()

            if not session:
                return []

            # Get messages
            stmt = (
                select(WebChatHistory)
                .where(WebChatHistory.session_id == session.id)
                .order_by(WebChatHistory.created_at.asc())
                .offset(offset)
                .limit(limit)
            )
            result = db.execute(stmt).scalars().all()
            return list(result)
        finally:
            db.close()

    async def get_recent_context(
        self,
        session_token: str,
        max_messages: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Get recent conversation context for LLM.

        Args:
            session_token: Session token
            max_messages: Maximum messages to include

        Returns:
            List of message dicts with role and content
        """
        messages = await self.get_messages(session_token, limit=max_messages)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    # =========================================================================
    # CONTEXT SUMMARIZATION
    # =========================================================================

    async def get_or_create_context(
        self,
        thread_id: str,
        client_type: str,
        client_id: str,
    ) -> Optional[ConversationContext]:
        """
        Get or create a conversation context record.

        Args:
            thread_id: LangGraph thread ID
            client_type: Client type (web, ios, whatsapp)
            client_id: Client identifier

        Returns:
            ConversationContext object
        """
        db = self._get_db()
        try:
            stmt = select(ConversationContext).where(
                ConversationContext.thread_id == thread_id
            )
            context = db.execute(stmt).scalar_one_or_none()

            if not context:
                context = ConversationContext(
                    thread_id=thread_id,
                    client_type=client_type,
                    client_id=client_id,
                    summary="New conversation started.",
                )
                db.add(context)
                db.commit()
                db.refresh(context)

            return context
        except Exception as e:
            db.rollback()
            logger.error("context_get_or_create_error", error=str(e))
            return None
        finally:
            db.close()

    async def record_whatsapp_activity(self, phone: str) -> bool:
        """
        Record WhatsApp activity for admin analytics.

        Creates or updates a ConversationContext row keyed by phone number.
        """
        if not phone:
            return False

        db = self._get_db()
        try:
            stmt = select(ConversationContext).where(
                ConversationContext.client_type == "whatsapp",
                ConversationContext.client_id == phone,
            )
            context = db.execute(stmt).scalar_one_or_none()

            if not context:
                thread_id = self.generate_thread_id("whatsapp", phone)
                context = ConversationContext(
                    thread_id=thread_id,
                    client_type="whatsapp",
                    client_id=phone,
                    summary="New WhatsApp conversation started.",
                )
                db.add(context)

            context.message_count = (context.message_count or 0) + 1
            context.updated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error("whatsapp_activity_record_error", error=str(e))
            return False
        finally:
            db.close()

    async def record_whatsapp_message(
        self,
        phone: str,
        direction: str,
        text: str | None = None,
        message_id: str | None = None,
        response_type: str | None = None,
        media_url: str | None = None,
        raw_payload: dict | None = None,
    ) -> bool:
        """
        Persist a WhatsApp chat message for admin visibility.
        """
        if not phone or direction not in {"incoming", "outgoing"}:
            return False

        db = self._get_db()
        try:
            msg = WhatsAppChatMessage(
                phone_number=phone,
                direction=direction,
                message_id=message_id,
                text=text,
                response_type=response_type,
                media_url=media_url,
                raw_payload=raw_payload or {},
            )
            db.add(msg)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error("whatsapp_message_record_error", error=str(e))
            return False
        finally:
            db.close()
    async def update_context_summary(
        self,
        thread_id: str,
        messages: List[Dict[str, str]],
        current_summary: Optional[str] = None,
    ) -> Optional[str]:
        """
        Update conversation context summary using LLM.

        Args:
            thread_id: LangGraph thread ID
            messages: Recent messages to summarize
            current_summary: Existing summary to build upon

        Returns:
            Updated summary string
        """
        if not messages:
            return current_summary

        # Build summarization prompt
        messages_text = "\n".join([
            f"{m['role'].upper()}: {m['content']}"
            for m in messages[-10:]  # Last 10 messages
        ])

        prompt = f"""Summarize this conversation context concisely (max 200 words).
Focus on: user preferences, key topics discussed, any pending requests.

Previous context:
{current_summary or 'None'}

Recent messages:
{messages_text}

Updated summary:"""

        try:
            from langchain_core.messages import HumanMessage
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            new_summary = response.content.strip()

            # Update in database
            db = self._get_db()
            try:
                stmt = select(ConversationContext).where(
                    ConversationContext.thread_id == thread_id
                )
                context = db.execute(stmt).scalar_one_or_none()

                if context:
                    context.summary = new_summary
                    context.message_count += len(messages)
                    context.updated_at = datetime.now(timezone.utc)
                    db.commit()

                return new_summary
            finally:
                db.close()

        except Exception as e:
            logger.error("context_summarization_error", error=str(e))
            return current_summary

    async def get_context_for_prompt(
        self,
        session_token: str,
        max_recent: int = 5,
    ) -> str:
        """
        Get formatted context for including in LLM prompts.

        Args:
            session_token: Session token
            max_recent: Maximum recent messages to include

        Returns:
            Formatted context string for LLM
        """
        # Get session
        session = await self.get_web_session(session_token)
        if not session:
            return ""

        # Build context
        parts = []

        # Add summary if available
        if session.context_summary:
            parts.append(f"Conversation summary: {session.context_summary}")

        # Add recent messages
        messages = await self.get_messages(session_token, limit=max_recent)
        if messages:
            parts.append("Recent conversation:")
            for msg in messages:
                parts.append(f"  {msg.role.upper()}: {msg.content[:100]}...")

        return "\n".join(parts)

    # =========================================================================
    # CLEANUP
    # =========================================================================

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired web sessions and their messages.

        Returns:
            Number of sessions deleted
        """
        db = self._get_db()
        try:
            stmt = delete(WebSession).where(
                WebSession.expires_at < datetime.now(timezone.utc)
            )
            result = db.execute(stmt)
            db.commit()

            count = result.rowcount
            if count > 0:
                logger.info("context_expired_sessions_cleaned", count=count)
            return count
        except Exception as e:
            db.rollback()
            logger.error("context_cleanup_error", error=str(e))
            return 0
        finally:
            db.close()


# Singleton instance
_context_service: Optional[ContextService] = None


def get_context_service() -> ContextService:
    """Get the singleton context service instance."""
    global _context_service
    if _context_service is None:
        _context_service = ContextService()
    return _context_service
