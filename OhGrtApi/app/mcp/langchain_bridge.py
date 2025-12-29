"""
MCP to LangChain Bridge

Converts MCP tools to LangChain tools so they can be used by LangGraph agents.
This enables dynamic tool discovery from external MCP servers.

Usage:
    # New way (with caching via MCPManager):
    tools = await get_mcp_tools_for_user(db, user_id)

    # Use with LangGraph
    agent = create_react_agent(llm, tools)

Features:
    - Tool caching (5 min TTL by default)
    - Connection pooling
    - Automatic retry on failure
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Type
from uuid import UUID

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field, create_model

from app.logger import logger
from app.mcp.client import MCPClient
from app.mcp.types import MCPTool, ToolInputSchema


class MCPLangChainBridge:
    """
    Bridge between MCP servers and LangChain tools.

    Dynamically discovers tools from MCP servers and converts them
    to LangChain tools that can be used with LangGraph agents.
    """

    def __init__(
        self,
        db,
        user_id: Optional[UUID] = None,
    ):
        """
        Initialize the bridge.

        Args:
            db: Database session
            user_id: User ID to fetch MCP server configurations
        """
        self.db = db
        self.user_id = user_id
        self._mcp_clients: Dict[str, MCPClient] = {}
        self._discovered_tools: Dict[str, Dict[str, Any]] = {}

    async def discover_all_tools(self) -> Dict[str, List[MCPTool]]:
        """
        Discover tools from all configured MCP servers.

        Returns:
            Dict mapping server name to list of MCPTool definitions
        """
        if not self.user_id:
            return {}

        from app.db.models import IntegrationCredential

        # Get all MCP server configurations for user
        credentials = (
            self.db.query(IntegrationCredential)
            .filter(
                IntegrationCredential.user_id == self.user_id,
                IntegrationCredential.provider.like("mcp_server_%"),
            )
            .all()
        )

        all_tools = {}

        for cred in credentials:
            config = cred.config or {}
            server_name = config.get("name", cred.provider.replace("mcp_server_", ""))
            url = config.get("url")
            token = cred.access_token if cred.access_token else None

            if not url:
                continue

            try:
                client = MCPClient(base_url=url, token=token)
                async with client:
                    tools = await client.list_tools()
                    all_tools[server_name] = tools

                    # Store for later use
                    for tool in tools:
                        tool_key = f"{server_name}:{tool.name}"
                        self._discovered_tools[tool_key] = {
                            "server": server_name,
                            "url": url,
                            "token": token,
                            "tool": tool,
                        }

                    logger.info(
                        "mcp_bridge_discovered_tools",
                        server=server_name,
                        tool_count=len(tools),
                    )
            except Exception as e:
                logger.warning(
                    "mcp_bridge_discovery_failed",
                    server=server_name,
                    error=str(e),
                )
                all_tools[server_name] = []

        return all_tools

    def mcp_tool_to_langchain(
        self,
        server_name: str,
        mcp_tool: MCPTool,
        url: str,
        token: Optional[str] = None,
    ) -> StructuredTool:
        """
        Convert an MCP tool to a LangChain StructuredTool.

        Args:
            server_name: Name of the MCP server
            mcp_tool: MCP tool definition
            url: MCP server URL
            token: Optional auth token

        Returns:
            LangChain StructuredTool
        """
        # Create Pydantic model from MCP input schema
        input_schema = mcp_tool.inputSchema
        fields = {}

        for prop_name, prop_def in input_schema.properties.items():
            prop_type = prop_def.get("type", "string")
            description = prop_def.get("description", f"Parameter: {prop_name}")
            is_required = prop_name in input_schema.required

            # Map JSON Schema types to Python types
            type_map = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            python_type = type_map.get(prop_type, str)

            if is_required:
                fields[prop_name] = (python_type, Field(description=description))
            else:
                fields[prop_name] = (Optional[python_type], Field(default=None, description=description))

        # Create dynamic Pydantic model
        if fields:
            ArgsModel = create_model(f"{mcp_tool.name}Args", **fields)
        else:
            ArgsModel = None

        # Create the async function that calls the MCP server
        async def call_mcp_tool(**kwargs) -> str:
            """Call the MCP tool."""
            client = MCPClient(base_url=url, token=token)
            try:
                async with client:
                    result = await client.call_tool(mcp_tool.name, kwargs)

                    if result.isError:
                        return f"Error: {result.content}"

                    # Extract text from result
                    texts = []
                    for content in result.content:
                        if hasattr(content, "text"):
                            texts.append(content.text)
                        elif isinstance(content, dict) and "text" in content:
                            texts.append(content["text"])

                    return "\n".join(texts) if texts else str(result.content)
            except Exception as e:
                return f"MCP call failed: {str(e)}"

        # Create unique tool name with server prefix
        tool_name = f"{server_name}_{mcp_tool.name}"

        # Create LangChain tool
        if ArgsModel:
            return StructuredTool(
                name=tool_name,
                description=f"[{server_name}] {mcp_tool.description}",
                func=lambda **kw: asyncio.get_event_loop().run_until_complete(call_mcp_tool(**kw)),
                coroutine=call_mcp_tool,
                args_schema=ArgsModel,
                return_direct=True,
            )
        else:
            return StructuredTool(
                name=tool_name,
                description=f"[{server_name}] {mcp_tool.description}",
                func=lambda: asyncio.get_event_loop().run_until_complete(call_mcp_tool()),
                coroutine=call_mcp_tool,
                return_direct=True,
            )

    async def get_langchain_tools(self) -> List[StructuredTool]:
        """
        Get all MCP tools as LangChain tools.

        Discovers tools from all configured MCP servers and
        converts them to LangChain StructuredTools.

        Returns:
            List of LangChain tools
        """
        discovered = await self.discover_all_tools()

        langchain_tools = []

        for server_name, tools in discovered.items():
            for tool in tools:
                tool_key = f"{server_name}:{tool.name}"
                info = self._discovered_tools.get(tool_key, {})

                try:
                    lc_tool = self.mcp_tool_to_langchain(
                        server_name=server_name,
                        mcp_tool=tool,
                        url=info.get("url", ""),
                        token=info.get("token"),
                    )
                    langchain_tools.append(lc_tool)

                    logger.debug(
                        "mcp_bridge_converted_tool",
                        server=server_name,
                        tool=tool.name,
                    )
                except Exception as e:
                    logger.warning(
                        "mcp_bridge_conversion_failed",
                        server=server_name,
                        tool=tool.name,
                        error=str(e),
                    )

        logger.info(
            "mcp_bridge_total_tools",
            count=len(langchain_tools),
        )

        return langchain_tools


async def get_mcp_tools_for_user(
    db,
    user_id: Optional[UUID],
    force_refresh: bool = False,
) -> List[StructuredTool]:
    """
    Get all MCP tools for a user (with caching).

    Uses MCPManager for:
    - Tool caching (5 min TTL)
    - Connection management
    - Automatic retry

    Args:
        db: Database session
        user_id: User ID
        force_refresh: Force cache refresh

    Returns:
        List of LangChain tools from user's MCP servers
    """
    from app.mcp.manager import MCPManager

    manager = MCPManager.get_instance()

    # Get all tools from all servers (cached)
    all_tools = await manager.get_all_tools_for_user(db, user_id, force_refresh)

    # Convert to LangChain tools
    bridge = MCPLangChainBridge(db, user_id)
    langchain_tools = []

    for server_name, mcp_tools in all_tools.items():
        # Get server config for URL/token
        state = manager._get_server_state(user_id, server_name)
        if not state:
            continue

        url = state.connection.url
        token = state.connection.token

        for mcp_tool in mcp_tools:
            try:
                lc_tool = bridge.mcp_tool_to_langchain(
                    server_name=server_name,
                    mcp_tool=mcp_tool,
                    url=url,
                    token=token,
                )
                langchain_tools.append(lc_tool)
            except Exception as e:
                logger.warning(
                    "mcp_tool_conversion_failed",
                    server=server_name,
                    tool=mcp_tool.name,
                    error=str(e),
                )

    logger.info(
        "mcp_tools_loaded_cached",
        user_id=str(user_id) if user_id else "anonymous",
        tool_count=len(langchain_tools),
        server_count=len(all_tools),
    )

    return langchain_tools


async def invalidate_mcp_cache(
    user_id: Optional[UUID] = None,
    server_name: Optional[str] = None,
) -> int:
    """
    Invalidate MCP tool cache.

    Args:
        user_id: Specific user (None = all users)
        server_name: Specific server (None = all servers)

    Returns:
        Number of caches invalidated
    """
    from app.mcp.manager import MCPManager

    manager = MCPManager.get_instance()
    return manager.invalidate_cache(user_id, server_name)
