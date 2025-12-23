from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import ChatMessage, User
from app.graph.tool_agent import build_tool_agent
from app.logger import logger
from app.db.models import IntegrationCredential


class ChatService:
    """Service for handling chat operations."""

    def __init__(self, settings: Settings, db: Session) -> None:
        self.settings = settings
        self.db = db
        self._agent = None

    async def send_message(
        self,
        user: User,
        message: str,
        conversation_id: Optional[UUID] = None,
        allowed_tools: Optional[list[str]] = None,
    ) -> Tuple[ChatMessage, ChatMessage, UUID]:
        """
        Process a user message and get AI response.

        Args:
            user: The authenticated user
            message: The user's message text
            conversation_id: Optional ID to continue existing conversation

        Returns:
            Tuple of (user_message, assistant_message, conversation_id)
        """
        # Generate conversation ID if not provided
        if conversation_id is None:
            conversation_id = uuid4()
            logger.info("chat_new_conversation", conversation_id=str(conversation_id))

        # Store user message
        user_msg = ChatMessage(
            user_id=user.id,
            conversation_id=conversation_id,
            role="user",
            content=message,
            message_metadata={},
        )
        self.db.add(user_msg)
        self.db.commit()
        self.db.refresh(user_msg)

        logger.info(
            "chat_user_message",
            user_id=str(user.id),
            conversation_id=str(conversation_id),
            message_id=str(user_msg.id),
        )

        # Build user-specific credentials map
        credentials = self._load_credentials(user)

        # Get AI response using the tool agent (user-specific)
        try:
            agent = build_tool_agent(self.settings, credentials=credentials)
            result = await agent.invoke(message, allowed_tools=allowed_tools)
            ai_content = result.get("response", "I apologize, but I couldn't process your request.")
            route_log = result.get("route_log", [])
            ai_message_metadata = {
                "category": result.get("category", "chat"),
                "route_log": ", ".join(route_log) if isinstance(route_log, list) else str(route_log),
            }
        except Exception as e:
            logger.error("chat_agent_error", error=str(e))
            ai_content = "I apologize, but an error occurred while processing your request."
            ai_message_metadata = {"error": str(e)}

        # Store assistant message
        assistant_msg = ChatMessage(
            user_id=user.id,
            conversation_id=conversation_id,
            role="assistant",
            content=ai_content,
            message_metadata=ai_message_metadata,
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)

        logger.info(
            "chat_assistant_message",
            user_id=str(user.id),
            conversation_id=str(conversation_id),
            message_id=str(assistant_msg.id),
            category=ai_message_metadata.get("category"),
        )

        return user_msg, assistant_msg, conversation_id

    def get_history(
        self,
        user: User,
        conversation_id: Optional[UUID] = None,
        limit: int = 50,
        before: Optional[datetime] = None,
    ) -> Tuple[List[ChatMessage], bool]:
        """
        Get chat history for a user.

        Args:
            user: The authenticated user
            conversation_id: Optional filter by conversation
            limit: Maximum messages to return
            before: Optional cursor for pagination (messages before this time)

        Returns:
            Tuple of (messages, has_more)
        """
        query = self.db.query(ChatMessage).filter(ChatMessage.user_id == user.id)

        if conversation_id:
            query = query.filter(ChatMessage.conversation_id == conversation_id)

        if before:
            query = query.filter(ChatMessage.created_at < before)

        # Get one extra to check if there are more
        query = query.order_by(ChatMessage.created_at.desc()).limit(limit + 1)
        messages = query.all()

        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        # Return in chronological order
        return list(reversed(messages)), has_more

    def get_conversations(
        self,
        user: User,
        limit: int = 20,
    ) -> List[dict]:
        """
        Get list of user's conversations with summaries.

        Args:
            user: The authenticated user
            limit: Maximum conversations to return

        Returns:
            List of conversation summaries
        """
        # Get distinct conversations with aggregated info
        conversations = (
            self.db.query(
                ChatMessage.conversation_id,
                func.count(ChatMessage.id).label("message_count"),
                func.max(ChatMessage.created_at).label("last_message_at"),
                func.min(ChatMessage.created_at).label("created_at"),
            )
            .filter(ChatMessage.user_id == user.id)
            .group_by(ChatMessage.conversation_id)
            .order_by(func.max(ChatMessage.created_at).desc())
            .limit(limit)
            .all()
        )

        result = []
        for conv in conversations:
            # Get first user message as title
            first_msg = (
                self.db.query(ChatMessage)
                .filter(
                    ChatMessage.conversation_id == conv.conversation_id,
                    ChatMessage.role == "user",
                )
                .order_by(ChatMessage.created_at)
                .first()
            )
            title = first_msg.content[:50] + "..." if first_msg and len(first_msg.content) > 50 else (first_msg.content if first_msg else None)

            result.append({
                "id": conv.conversation_id,
                "title": title,
                "message_count": conv.message_count,
                "last_message_at": conv.last_message_at,
                "created_at": conv.created_at,
            })

        return result

    def delete_conversation(self, user: User, conversation_id: UUID) -> int:
        """
        Delete a conversation and all its messages.

        Args:
            user: The authenticated user
            conversation_id: The conversation to delete

        Returns:
            Number of messages deleted
        """
        deleted = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == user.id,
                ChatMessage.conversation_id == conversation_id,
            )
            .delete()
        )
        self.db.commit()

        logger.info(
            "chat_conversation_deleted",
            user_id=str(user.id),
            conversation_id=str(conversation_id),
            messages_deleted=deleted,
        )

        return deleted

    def _load_credentials(self, user: User) -> dict:
        creds = (
            self.db.query(IntegrationCredential)
            .filter(IntegrationCredential.user_id == user.id)
            .all()
        )
        cred_map = {}
        for cred in creds:
            cred_map[cred.provider] = {
                "access_token": cred.access_token,
                "config": cred.config or {},
                "display_name": cred.display_name,
            }
        return cred_map
