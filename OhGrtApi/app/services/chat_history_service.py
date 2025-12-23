
from __future__ import annotations
from typing import List
from uuid import UUID

from app.services.postgres_service import PostgresService
from app.utils.models import ChatMessage


class ChatHistoryService:
    def __init__(self, settings):
        self.postgres_service = PostgresService(settings)

    def save_message(self, user_id: int, conversation_id: UUID, from_actor: str, text: str, category: str) -> ChatMessage:
        query = """
            INSERT INTO chat_history (user_id, conversation_id, from_actor, text, category)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, user_id, conversation_id, from_actor, text, category, created_at
        """
        params = (user_id, conversation_id, from_actor, text, category)
        result = self.postgres_service.execute_query(query, params)
        return ChatMessage(**result[0])

    def get_conversations(self, user_id: int) -> List[dict]:
        query = """
            SELECT DISTINCT conversation_id, MAX(created_at) as last_message_at
            FROM chat_history
            WHERE user_id = %s
            GROUP BY conversation_id
            ORDER BY last_message_at DESC
        """
        return self.postgres_service.execute_query(query, (user_id,))

    def get_conversation_history(self, user_id: int, conversation_id: UUID) -> List[ChatMessage]:
        query = "SELECT * FROM chat_history WHERE user_id = %s AND conversation_id = %s ORDER BY created_at ASC"
        params = (user_id, conversation_id)
        result = self.postgres_service.execute_query(query, params)
        return [ChatMessage(**row) for row in result]
