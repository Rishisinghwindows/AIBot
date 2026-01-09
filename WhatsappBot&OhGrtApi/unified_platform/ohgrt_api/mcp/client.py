"""
MCP Client Implementation

A client for connecting to external MCP servers via HTTP/SSE or stdio.
Follows the specification at https://modelcontextprotocol.io/specification/2025-11-25
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import httpx

from ohgrt_api.logger import logger
from ohgrt_api.mcp.types import (
    CallToolParams,
    InitializeParams,
    InitializeResult,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    ListToolsResult,
    MCPClientCapabilities,
    MCPClientInfo,
    MCPServerInfo,
    MCPTool,
    TextContent,
    ToolCallResult,
)

class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass


class MCPConnectionError(MCPClientError):
    """Connection-related errors."""
    pass


class MCPToolError(MCPClientError):
    """Tool execution errors."""
    pass


class MCPClient:
    """
    MCP Client for connecting to external MCP servers.

    Supports HTTP transport with JSON-RPC 2.0.

    Usage:
        async with MCPClient(base_url="http://mcp-server:8080") as client:
            # Discover available tools
            tools = await client.list_tools()

            # Call a tool
            result = await client.call_tool("search", {"query": "hello"})
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: float = 30.0,
        client_name: str = "ohgrt-mcp-client",
        client_version: str = "1.0.0",
    ):
        """
        Initialize MCP client.

        Args:
            base_url: Base URL of the MCP server
            token: Optional Bearer token for authentication
            timeout: Request timeout in seconds
            client_name: Client identifier
            client_version: Client version
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.client_name = client_name
        self.client_version = client_version

        self._http_client: Optional[httpx.AsyncClient] = None
        self._server_info: Optional[MCPServerInfo] = None
        self._tools_cache: Optional[List[MCPTool]] = None
        self._request_id = 0
        self._initialized = False

    @property
    def available(self) -> bool:
        """Check if client is configured with a valid URL."""
        return bool(self.base_url and self.base_url.startswith(("http://", "https://")))

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> MCPServerInfo:
        """
        Connect to the MCP server and initialize the session.

        Returns:
            Server information including capabilities
        """
        if not self.available:
            raise MCPConnectionError("MCP client not configured with valid URL")

        # Create HTTP client
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self._http_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
        )

        # Send initialize request
        try:
            init_params = InitializeParams(
                protocolVersion="2025-11-25",
                clientInfo=MCPClientInfo(
                    name=self.client_name,
                    version=self.client_version,
                    capabilities=MCPClientCapabilities(),
                ),
            )

            response = await self._send_request("initialize", init_params.model_dump())

            if response.error:
                raise MCPConnectionError(f"Initialize failed: {response.error.message}")

            init_result = InitializeResult(**response.result)
            self._server_info = init_result.serverInfo

            # Send initialized notification
            await self._send_notification("initialized", {})
            self._initialized = True

            logger.info(
                "mcp_client_connected",
                server=self._server_info.name,
                version=self._server_info.version,
            )

            return self._server_info

        except httpx.HTTPError as e:
            # Fall back to legacy mode for non-MCP servers
            logger.warning("mcp_init_failed_fallback", error=str(e))
            self._initialized = True
            return MCPServerInfo(name="legacy", version="1.0.0")

    async def close(self) -> None:
        """Close the client connection."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        self._initialized = False
        self._tools_cache = None

    async def list_tools(self, force_refresh: bool = False) -> List[MCPTool]:
        """
        List available tools from the server.

        Args:
            force_refresh: Force refresh of cached tools

        Returns:
            List of available tools
        """
        if self._tools_cache and not force_refresh:
            return self._tools_cache

        try:
            response = await self._send_request("tools/list", {})

            if response.error:
                raise MCPToolError(f"Failed to list tools: {response.error.message}")

            result = ListToolsResult(**response.result)
            self._tools_cache = result.tools

            logger.info("mcp_tools_discovered", count=len(result.tools))
            return result.tools

        except httpx.HTTPError as e:
            logger.warning("mcp_list_tools_failed", error=str(e))
            return []

    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> ToolCallResult:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            params = CallToolParams(
                name=name,
                arguments=arguments or {},
            )

            response = await self._send_request("tools/call", params.model_dump())

            if response.error:
                return ToolCallResult(
                    content=[TextContent(text=f"Error: {response.error.message}")],
                    isError=True,
                )

            return ToolCallResult(**response.result)

        except httpx.HTTPError as e:
            logger.error("mcp_tool_call_failed", tool=name, error=str(e))
            return ToolCallResult(
                content=[TextContent(text=f"Connection error: {str(e)}")],
                isError=True,
            )

    async def query(self, prompt: str) -> str:
        """
        Legacy query method for backwards compatibility.

        Attempts to use MCP protocol first, falls back to simple POST.

        Args:
            prompt: User prompt

        Returns:
            Response text
        """
        # Try MCP protocol first
        if self._initialized and self._tools_cache:
            # Find a suitable tool (e.g., "query", "chat", "ask")
            for tool_name in ["query", "chat", "ask", "process"]:
                if any(t.name == tool_name for t in self._tools_cache):
                    result = await self.call_tool(tool_name, {"prompt": prompt})
                    if not result.isError and result.content:
                        return self._extract_text(result)

        # Fall back to legacy POST
        return await self._legacy_query(prompt)

    async def _legacy_query(self, prompt: str) -> str:
        """
        Legacy query for non-MCP servers.

        Sends a simple POST request with the prompt.
        """
        if not self._http_client:
            headers = {"Content-Type": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )

        try:
            response = await self._http_client.post(
                "/query",
                json={"prompt": prompt},
            )
            response.raise_for_status()

            data = response.json()

            # Handle various response formats
            if isinstance(data, dict):
                return data.get("reply") or data.get("response") or data.get("result") or str(data)
            return str(data)

        except httpx.HTTPError as e:
            logger.error("mcp_legacy_query_failed", error=str(e))
            return f"Error: {str(e)}"

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> JSONRPCResponse:
        """Send a JSON-RPC request."""
        if not self._http_client:
            raise MCPConnectionError("Client not connected")

        self._request_id += 1
        request = JSONRPCRequest(
            id=self._request_id,
            method=method,
            params=params,
        )

        logger.debug("mcp_request", method=method, id=self._request_id)

        try:
            # Try /mcp endpoint first, then root
            for endpoint in ["/mcp", "/", ""]:
                try:
                    response = await self._http_client.post(
                        endpoint,
                        json=request.model_dump(),
                    )
                    if response.status_code == 404:
                        continue
                    response.raise_for_status()
                    data = response.json()
                    return JSONRPCResponse(**data)
                except httpx.HTTPStatusError:
                    continue

            # If no endpoint worked, return error
            return JSONRPCResponse(
                id=self._request_id,
                error=JSONRPCError(code=-32600, message="No MCP endpoint found"),
            )

        except httpx.HTTPError as e:
            return JSONRPCResponse(
                id=self._request_id,
                error=JSONRPCError(code=-32603, message=str(e)),
            )

    async def _send_notification(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self._http_client:
            return

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }

        try:
            for endpoint in ["/mcp", "/", ""]:
                try:
                    await self._http_client.post(endpoint, json=request)
                    return
                except httpx.HTTPStatusError:
                    continue
        except httpx.HTTPError:
            pass  # Notifications don't require acknowledgment

    def _extract_text(self, result: ToolCallResult) -> str:
        """Extract text from tool result."""
        texts = []
        for content in result.content:
            if hasattr(content, "text"):
                texts.append(content.text)
            elif isinstance(content, dict) and "text" in content:
                texts.append(content["text"])
        return "\n".join(texts) if texts else str(result.content)


class MCPClientPool:
    """
    Pool of MCP clients for managing multiple server connections.

    Usage:
        pool = MCPClientPool()
        pool.add("weather", "http://weather-mcp:8080")
        pool.add("search", "http://search-mcp:8080")

        async with pool:
            weather = await pool.call("weather", "get_forecast", {"city": "NYC"})
    """

    def __init__(self):
        self._clients: Dict[str, MCPClient] = {}

    def add(
        self,
        name: str,
        base_url: str,
        token: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Add a client to the pool."""
        self._clients[name] = MCPClient(base_url=base_url, token=token, **kwargs)

    def remove(self, name: str) -> None:
        """Remove a client from the pool."""
        self._clients.pop(name, None)

    async def __aenter__(self) -> "MCPClientPool":
        """Connect all clients."""
        for client in self._clients.values():
            try:
                await client.connect()
            except MCPConnectionError:
                pass  # Continue with other clients
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close all clients."""
        for client in self._clients.values():
            await client.close()

    async def call(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> ToolCallResult:
        """Call a tool on a specific server."""
        client = self._clients.get(server_name)
        if not client:
            return ToolCallResult(
                content=[TextContent(text=f"Server not found: {server_name}")],
                isError=True,
            )
        return await client.call_tool(tool_name, arguments)

    async def discover_all_tools(self) -> Dict[str, List[MCPTool]]:
        """Discover tools from all connected servers."""
        result = {}
        for name, client in self._clients.items():
            try:
                tools = await client.list_tools()
                result[name] = tools
            except Exception as e:
                logger.warning("mcp_discover_failed", server=name, error=str(e))
                result[name] = []
        return result
