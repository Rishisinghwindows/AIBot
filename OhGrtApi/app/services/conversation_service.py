"""
Conversation Service - Manages user chat conversations and messages.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Conversation, ChatMessage
from app.logger import logger


class ConversationService:
    """Service for managing user conversations."""

    def __init__(self, db: Session):
        self.db = db

    def get_conversations_by_user(self, user_id: UUID, limit: int = 50) -> List[Conversation]:
        """Get all conversations for a user, ordered by most recent."""
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )

    def get_conversation(self, conversation_id: UUID, user_id: UUID) -> Optional[Conversation]:
        """Get a specific conversation by ID and user."""
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )

    def create_conversation(self, user_id: UUID, title: str) -> Conversation:
        """Create a new conversation for a user."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        logger.info("conversation_created", conversation_id=str(conversation.id), user_id=str(user_id))
        return conversation

    def update_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
    ) -> Optional[Conversation]:
        """Update an existing conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title

        self.db.commit()
        self.db.refresh(conversation)
        logger.info("conversation_updated", conversation_id=str(conversation.id), user_id=str(user_id))
        return conversation

    def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Delete a conversation and all its messages."""
        # Delete messages first (cascade should handle this, but being explicit)
        self.db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.user_id == user_id,
        ).delete()

        deleted = (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .delete()
        )
        self.db.commit()
        if deleted:
            logger.info("conversation_deleted", conversation_id=str(conversation_id), user_id=str(user_id))
        return deleted > 0

    def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        limit: int = 100,
    ) -> List[ChatMessage]:
        """Get messages for a conversation."""
        # Verify the conversation belongs to the user
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return []

        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

    def add_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> ChatMessage:
        """Add a message to a conversation."""
        message = ChatMessage(
            user_id=user_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
        )
        self.db.add(message)

        # Update conversation's updated_at
        conversation = self.get_conversation(conversation_id, user_id)
        if conversation:
            from datetime import datetime, timezone
            conversation.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(message)
        return message
