from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID
import psycopg2
import psycopg2.extras

# Register UUID adapter for psycopg2
psycopg2.extras.register_uuid()

from app.config import Settings
from app.logger import logger
from app.utils.errors import ServiceError
from app.utils.models import ChatMessage


class MessageService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _conn_kwargs(self) -> dict:
        return {
            "host": self.settings.postgres_host,
            "port": self.settings.postgres_port,
            "user": self.settings.postgres_user,
            "password": self.settings.postgres_password,
            "dbname": self.settings.postgres_db,
        }

    def _execute_query(self, query: str, params: Optional[tuple] = None, fetch: str = "none") -> Any:
        logger.debug("message_service_execute_query", query=query, params=params)
        try:
            with psycopg2.connect(**self._conn_kwargs()) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if fetch == "one":
                        res = cur.fetchone()
                        if res is None:
                            return None
                        col_names = [desc[0] for desc in cur.description]
                        return dict(zip(col_names, res))
                    elif fetch == "all":
                        col_names = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        return [dict(zip(col_names, row)) for row in rows]
                    return None
        except Exception as exc:
            logger.error("message_service_sql_error", error=str(exc))
            raise ServiceError("SQL execution failed in MessageService") from exc

    def get_messages_by_conversation(self, conversation_id: UUID, user_id: UUID) -> List[ChatMessage]:
        # We must join with conversations to ensure the user owns the conversation
        query = """
            SELECT m.*
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE m.conversation_id = %s AND c.user_id = %s
            ORDER BY m.created_at ASC;
        """
        params = (str(conversation_id), str(user_id))
        results = self._execute_query(query, params, fetch="all")
        if not results:
            return []
        return [ChatMessage(**result) for result in results]

    def create_message(self, conversation_id: UUID, from_actor: str, text: str) -> ChatMessage:
        # Insert message
        query_insert = "INSERT INTO messages (conversation_id, from_actor, text) VALUES (%s, %s, %s) RETURNING *;"
        params_insert = (str(conversation_id), from_actor, text)
        result = self._execute_query(query_insert, params_insert, fetch="one")

        # Update conversation timestamp
        query_update = "UPDATE conversations SET updated_at = NOW() WHERE id = %s;"
        params_update = (str(conversation_id),)
        self._execute_query(query_update, params_update, fetch="none")

        if not result:
            raise ServiceError("Failed to create message.")
        return ChatMessage(**result)
