"""
MCP Tool Service - Manages user-configured MCP tools.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import MCPTool
from app.logger import logger


class MCPToolService:
    """Service for managing user MCP tools."""

    def __init__(self, db: Session):
        self.db = db

    def get_tools_by_user(self, user_id: UUID) -> List[MCPTool]:
        """Get all MCP tools for a user."""
        return (
            self.db.query(MCPTool)
            .filter(MCPTool.user_id == user_id)
            .order_by(MCPTool.created_at.desc())
            .all()
        )

    def get_enabled_tools_by_user(self, user_id: UUID) -> List[MCPTool]:
        """Get only enabled MCP tools for a user."""
        return (
            self.db.query(MCPTool)
            .filter(MCPTool.user_id == user_id, MCPTool.enabled == True)
            .order_by(MCPTool.created_at.desc())
            .all()
        )

    def get_tool(self, tool_id: UUID, user_id: UUID) -> Optional[MCPTool]:
        """Get a specific tool by ID and user."""
        return (
            self.db.query(MCPTool)
            .filter(MCPTool.id == tool_id, MCPTool.user_id == user_id)
            .first()
        )

    def create_tool(
        self,
        user_id: UUID,
        name: str,
        tool_type: str,
        description: Optional[str] = None,
        config: Optional[dict] = None,
        enabled: bool = True,
    ) -> MCPTool:
        """Create a new MCP tool for a user."""
        tool = MCPTool(
            user_id=user_id,
            name=name,
            description=description,
            tool_type=tool_type,
            config=config or {},
            enabled=enabled,
        )
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        logger.info("mcp_tool_created", tool_id=str(tool.id), user_id=str(user_id))
        return tool

    def update_tool(
        self,
        tool_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tool_type: Optional[str] = None,
        config: Optional[dict] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[MCPTool]:
        """Update an existing MCP tool."""
        tool = self.get_tool(tool_id, user_id)
        if not tool:
            return None

        if name is not None:
            tool.name = name
        if description is not None:
            tool.description = description
        if tool_type is not None:
            tool.tool_type = tool_type
        if config is not None:
            tool.config = config
        if enabled is not None:
            tool.enabled = enabled

        self.db.commit()
        self.db.refresh(tool)
        logger.info("mcp_tool_updated", tool_id=str(tool.id), user_id=str(user_id))
        return tool

    def delete_tool(self, tool_id: UUID, user_id: UUID) -> bool:
        """Delete an MCP tool."""
        deleted = (
            self.db.query(MCPTool)
            .filter(MCPTool.id == tool_id, MCPTool.user_id == user_id)
            .delete()
        )
        self.db.commit()
        if deleted:
            logger.info("mcp_tool_deleted", tool_id=str(tool_id), user_id=str(user_id))
        return deleted > 0

    def toggle_tool(self, tool_id: UUID, user_id: UUID) -> Optional[MCPTool]:
        """Toggle the enabled state of a tool."""
        tool = self.get_tool(tool_id, user_id)
        if not tool:
            return None

        tool.enabled = not tool.enabled
        self.db.commit()
        self.db.refresh(tool)
        logger.info(
            "mcp_tool_toggled",
            tool_id=str(tool.id),
            enabled=tool.enabled,
            user_id=str(user_id),
        )
        return tool
