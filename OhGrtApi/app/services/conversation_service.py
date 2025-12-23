from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import Conversation
from app.logger import logger


class ConversationService:
    """Service for managing conversations using SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def get_conversations_by_user(self, user_id: UUID) -> list[Conversation]:
        """Get all conversations for a user."""
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
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
        """Update a conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title

        self.db.commit()
        self.db.refresh(conversation)
        logger.info("conversation_updated", conversation_id=str(conversation_id), user_id=str(user_id))
        return conversation

    def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Delete a conversation."""
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False

        self.db.delete(conversation)
        self.db.commit()
        logger.info("conversation_deleted", conversation_id=str(conversation_id), user_id=str(user_id))
        return True
