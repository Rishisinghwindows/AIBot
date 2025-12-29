"""
MCP (Model Context Protocol) Implementation

This module provides a complete MCP implementation following the official
specification at https://modelcontextprotocol.io/specification/2025-11-25

Components:
- MCPServer: Exposes tools via JSON-RPC 2.0
- MCPClient: Connects to external MCP servers
- MCPManager: Connection pooling, caching, health checks
- MCPLangChainBridge: Converts MCP tools to LangChain tools
- Types: Pydantic models for MCP protocol

Generic MCP Flow (like Claude Desktop):
1. User adds MCP server via POST /mcp/servers
2. On chat, tools are discovered via tools/list (cached)
3. MCP tools converted to LangChain tools via bridge
4. Agent uses all tools (built-in + MCP)
5. Tool calls routed to correct MCP server

Features:
- Tool caching (5 min TTL by default)
- Connection management with health checks
- Background monitoring of server status
- Per-user server isolation
"""

from app.mcp.types import (
    MCPTool,
    MCPResource,
    MCPPrompt,
    MCPServerCapabilities,
    MCPServerInfo,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    ToolCallResult,
    TextContent,
    ImageContent,
)
from app.mcp.server import MCPServer
from app.mcp.client import MCPClient
from app.mcp.manager import MCPManager, ServerStatus, ServerConnection
from app.mcp.langchain_bridge import (
    MCPLangChainBridge,
    get_mcp_tools_for_user,
    invalidate_mcp_cache,
)

__all__ = [
    # Core components
    "MCPServer",
    "MCPClient",
    "MCPManager",
    "MCPLangChainBridge",
    # Convenience functions
    "get_mcp_tools_for_user",
    "invalidate_mcp_cache",
    # Manager types
    "ServerStatus",
    "ServerConnection",
    # Protocol types
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "MCPServerCapabilities",
    "MCPServerInfo",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "ToolCallResult",
    "TextContent",
    "ImageContent",
]
