"""
MCP (Model Context Protocol) Implementation

This module provides a complete MCP implementation following the official
specification at https://modelcontextprotocol.io/specification/2025-11-25

Components:
- MCPServer: Exposes tools via JSON-RPC 2.0
- MCPClient: Connects to external MCP servers
- Types: Pydantic models for MCP protocol
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

__all__ = [
    "MCPServer",
    "MCPClient",
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
