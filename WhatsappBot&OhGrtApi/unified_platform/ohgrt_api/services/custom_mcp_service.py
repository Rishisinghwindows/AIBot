"""
Custom MCP Service - Enhanced client for user-specified MCP endpoints.

This service now uses the proper MCP protocol (JSON-RPC 2.0) with fallback
to legacy HTTP POST for non-MCP-compliant servers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from ohgrt_api.logger import logger
from ohgrt_api.mcp.client import MCPClient, MCPClientError
from ohgrt_api.mcp.types import MCPTool, ToolCallResult


class CustomMCPService:
    """
    Enhanced client for user-specified MCP endpoints.

    Supports:
    1. Full MCP protocol (JSON-RPC 2.0) with tool discovery
    2. Legacy HTTP POST fallback for non-MCP servers

    Usage:
        service = CustomMCPService(
            base_url="http://my-mcp-server:8080",
            token="optional-bearer-token"
        )

        # Discover tools
        tools = await service.discover_tools()

        # Call a specific tool
        result = await service.call_tool("search", {"query": "hello"})

        # Legacy query (auto-detects protocol)
        response = await service.query("What is the weather?")
    """

    def __init__(
        self,
        base_url: Optional[str],
        token: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize the Custom MCP Service.

        Args:
            base_url: Root URL of the MCP endpoint
            token: Optional Bearer token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or "").rstrip("/")
        self.token = token or ""
        self.timeout = timeout
        self.available = bool(self.base_url)

        self._mcp_client: Optional[MCPClient] = None
        self._tools_cache: Optional[List[MCPTool]] = None
        self._is_mcp_server: Optional[bool] = None

    async def connect(self) -> bool:
        """
        Connect to the MCP server and detect protocol support.

        Returns:
            True if connected successfully (MCP or legacy mode)
        """
        if not self.available:
            return False

        self._mcp_client = MCPClient(
            base_url=self.base_url,
            token=self.token if self.token else None,
            timeout=self.timeout,
        )

        try:
            await self._mcp_client.connect()
            self._is_mcp_server = True
            logger.info("custom_mcp_connected", mode="mcp", url=self.base_url)
            return True
        except MCPClientError:
            self._is_mcp_server = False
            logger.info("custom_mcp_connected", mode="legacy", url=self.base_url)
            return True
        except Exception as e:
            logger.warning("custom_mcp_connect_failed", error=str(e))
            self._is_mcp_server = False
            return False

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._mcp_client:
            await self._mcp_client.close()
            self._mcp_client = None
        self._tools_cache = None

    async def discover_tools(self, force_refresh: bool = False) -> List[MCPTool]:
        """
        Discover available tools from the MCP server.

        Args:
            force_refresh: Force refresh of cached tools

        Returns:
            List of available MCP tools
        """
        if self._tools_cache and not force_refresh:
            return self._tools_cache

        if not self.available:
            return []

        # Ensure connected
        if self._mcp_client is None:
            await self.connect()

        if self._mcp_client and self._is_mcp_server:
            try:
                self._tools_cache = await self._mcp_client.list_tools()
                logger.info(
                    "custom_mcp_tools_discovered",
                    count=len(self._tools_cache),
                    url=self.base_url,
                )
                return self._tools_cache
            except Exception as e:
                logger.warning("custom_mcp_discover_failed", error=str(e))

        return []

    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> ToolCallResult:
        """
        Call a specific tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self.available:
            from ohgrt_api.mcp.types import TextContent
            return ToolCallResult(
                content=[TextContent(text="Custom MCP not configured")],
                isError=True,
            )

        # Ensure connected
        if self._mcp_client is None:
            await self.connect()

        if self._mcp_client:
            return await self._mcp_client.call_tool(name, arguments or {})

        from ohgrt_api.mcp.types import TextContent
        return ToolCallResult(
            content=[TextContent(text="Failed to connect to MCP server")],
            isError=True,
        )

    async def query(self, prompt: str) -> str:
        """
        Send a query to the MCP server.

        Uses MCP protocol if available, falls back to legacy HTTP POST.

        Args:
            prompt: User prompt/query

        Returns:
            Response text
        """
        if not self.available:
            return "Custom MCP not configured. Provide a base URL (and optional token)."

        # Ensure connected
        if self._mcp_client is None:
            await self.connect()

        # Try MCP protocol first
        if self._mcp_client and self._is_mcp_server:
            try:
                result = await self._mcp_client.query(prompt)
                return result
            except Exception as e:
                logger.warning("custom_mcp_query_failed", error=str(e))
                # Fall through to legacy mode

        # Legacy HTTP POST
        return await self._legacy_query(prompt)

    async def _legacy_query(self, prompt: str) -> str:
        """
        Legacy query for non-MCP servers.

        Sends a simple POST request with the prompt.
        """
        url = f"{self.base_url}/query"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json={"prompt": prompt}, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                # Accept common response shapes
                if isinstance(data, dict):
                    if "reply" in data:
                        return str(data["reply"])
                    if "response" in data:
                        return str(data["response"])
                    if "result" in data:
                        return str(data["result"])
                    if "text" in data:
                        return str(data["text"])

                # Fallback to text
                return resp.text

        except Exception as exc:
            logger.error("custom_mcp_legacy_error", error=_format_error(exc))
            return f"Custom MCP unavailable: {_format_error(exc)}"

    @property
    def is_mcp_compliant(self) -> bool:
        """Check if the connected server is MCP-compliant."""
        return self._is_mcp_server is True

    @property
    def tools(self) -> List[MCPTool]:
        """Get cached tools (call discover_tools first)."""
        return self._tools_cache or []

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions in a format suitable for LangChain/LangGraph.

        Returns:
            List of tool definitions with name, description, and schema
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema.model_dump(),
            }
            for tool in self.tools
        ]


def _format_error(exc: Exception) -> str:
    """Format an exception for user-friendly display."""
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        body = exc.response.text[:500]
        return f"HTTP {status}: {body}"
    if isinstance(exc, httpx.ConnectError):
        return f"Connection failed: {str(exc)}"
    if isinstance(exc, httpx.TimeoutException):
        return "Request timed out"
    return str(exc)
