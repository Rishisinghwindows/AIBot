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
        intent = None
        structured_data = None
        media_url = None
        requires_location = False
        try:
            agent = build_tool_agent(self.settings, credentials=credentials, db=self.db, user_id=user.id)
            result = await agent.invoke(message, allowed_tools=allowed_tools)
            ai_content = result.get("response", "I apologize, but I couldn't process your request.")
            route_log = result.get("route_log", [])
            intent = result.get("intent") or result.get("category", "chat")
            structured_data = result.get("structured_data")
            media_url = result.get("media_url")
            requires_location = result.get("requires_location", False)
            ai_message_metadata = {
                "category": result.get("category", "chat"),
                "route_log": ", ".join(route_log) if isinstance(route_log, list) else str(route_log),
                "intent": intent,
            }
        except Exception as e:
            logger.error("chat_agent_error", error=str(e))
            ai_content = "I apologize, but an error occurred while processing your request."
            ai_message_metadata = {"error": str(e)}

        # Store assistant message with structured data in metadata
        ai_message_metadata["structured_data"] = structured_data
        ai_message_metadata["media_url"] = media_url
        ai_message_metadata["requires_location"] = requires_location
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
        from sqlalchemy import text, literal_column
        from sqlalchemy.orm import aliased

        # PERFORMANCE FIX: Use a subquery to get first messages in one query
        # instead of N+1 queries (one per conversation)

        # Subquery to get the first user message per conversation using DISTINCT ON
        first_messages_subquery = (
            self.db.query(
                ChatMessage.conversation_id,
                ChatMessage.content,
            )
            .filter(
                ChatMessage.user_id == user.id,
                ChatMessage.role == "user",
            )
            .distinct(ChatMessage.conversation_id)
            .order_by(ChatMessage.conversation_id, ChatMessage.created_at)
            .subquery()
        )

        # Get distinct conversations with aggregated info and first message
        conversations = (
            self.db.query(
                ChatMessage.conversation_id,
                func.count(ChatMessage.id).label("message_count"),
                func.max(ChatMessage.created_at).label("last_message_at"),
                func.min(ChatMessage.created_at).label("created_at"),
                first_messages_subquery.c.content.label("first_message"),
            )
            .filter(ChatMessage.user_id == user.id)
            .outerjoin(
                first_messages_subquery,
                ChatMessage.conversation_id == first_messages_subquery.c.conversation_id,
            )
            .group_by(
                ChatMessage.conversation_id,
                first_messages_subquery.c.content,
            )
            .order_by(func.max(ChatMessage.created_at).desc())
            .limit(limit)
            .all()
        )

        result = []
        for conv in conversations:
            first_msg_content = conv.first_message
            title = (
                first_msg_content[:50] + "..."
                if first_msg_content and len(first_msg_content) > 50
                else first_msg_content
            )

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
        """Load and decrypt user's integration credentials."""
        from app.utils.crypto import decrypt_if_needed

        creds = (
            self.db.query(IntegrationCredential)
            .filter(IntegrationCredential.user_id == user.id)
            .all()
        )
        cred_map = {}
        for cred in creds:
            try:
                # Decrypt the access token before returning
                decrypted_token = decrypt_if_needed(cred.access_token) if cred.access_token else None

                # Decrypt sensitive config values (like refresh_token)
                config = dict(cred.config) if cred.config else {}
                if config.get("refresh_token"):
                    try:
                        config["refresh_token"] = decrypt_if_needed(config["refresh_token"])
                    except ValueError:
                        # If decryption fails, keep original (may not be encrypted)
                        pass

                cred_map[cred.provider] = {
                    "access_token": decrypted_token,
                    "config": config,
                    "display_name": cred.display_name,
                }
            except ValueError as e:
                logger.error(
                    "credential_decryption_failed",
                    provider=cred.provider,
                    user_id=str(user.id),
                    error=str(e),
                )
                # Skip this credential if decryption fails
                continue
        return cred_map
