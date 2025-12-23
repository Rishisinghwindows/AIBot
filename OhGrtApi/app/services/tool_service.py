
from __future__ import annotations
from typing import List, Dict, Any

from app.services.postgres_service import PostgresService
from app.utils.models import Tool, ToolCreate, ToolUpdate


class ToolService:
    def __init__(self, settings):
        self.postgres_service = PostgresService(settings)

    def get_tools_by_user(self, user_id: int) -> List[Tool]:
        query = "SELECT * FROM tools WHERE user_id = %s"
        result = self.postgres_service.execute_query(query, (user_id,))
        return [Tool(**row) for row in result]

    def get_tool(self, tool_id: int) -> Tool | None:
        query = "SELECT * FROM tools WHERE id = %s"
        result = self.postgres_service.execute_query(query, (tool_id,))
        if result:
            return Tool(**result[0])
        return None

    def create_tool(self, user_id: int, tool: ToolCreate) -> Tool:
        query = """
            INSERT INTO tools (user_id, name, description, type, config)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, user_id, name, description, type, config, created_at
        """
        params = (
            user_id,
            tool.name,
            tool.description,
            tool.type,
            tool.config,
        )
        result = self.postgres_service.execute_query(query, params)
        return Tool(**result[0])

    def update_tool(self, tool_id: int, tool: ToolUpdate) -> Tool | None:
        query = """
            UPDATE tools
            SET name = %s, description = %s, type = %s, config = %s
            WHERE id = %s
            RETURNING id, user_id, name, description, type, config, created_at
        """
        params = (
            tool.name,
            tool.description,
            tool.type,
            tool.config,
            tool_id,
        )
        result = self.postgres_service.execute_query(query, params)
        if result:
            return Tool(**result[0])
        return None

    def delete_tool(self, tool_id: int) -> bool:
        query = "DELETE FROM tools WHERE id = %s"
        # The execute_query method returns a list of dicts, so we can't directly check for success.
        # A better approach would be to have execute_query return the number of affected rows for non-SELECT queries.
        # For now, we will assume success if no exception is raised.
        try:
            self.postgres_service.execute_query(query, (tool_id,))
            return True
        except Exception:
            return False
