"""
Stdio-based MCP Client Implementation

A client for connecting to MCP servers that use stdio transport (subprocess).
Used for official MCP servers like @modelcontextprotocol/server-github.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from app.logger import logger
from app.mcp.types import MCPTool, ToolCallResult, TextContent


@dataclass
class StdioMCPClient:
    """
    MCP Client for stdio-based servers.

    Spawns a subprocess and communicates via stdin/stdout using JSON-RPC 2.0.

    Usage:
        async with StdioMCPClient(
            command="mcp-server-github",
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": token}
        ) as client:
            tools = await client.list_tools()
            result = await client.call_tool("list_repos", {"owner": "user"})
    """

    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0

    _process: Optional[asyncio.subprocess.Process] = field(default=None, init=False)
    _request_id: int = field(default=0, init=False)
    _tools_cache: Optional[List[MCPTool]] = field(default=None, init=False)
    _initialized: bool = field(default=False, init=False)
    _read_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _write_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @property
    def available(self) -> bool:
        """Check if client has a valid command."""
        return bool(self.command)

    async def __aenter__(self) -> "StdioMCPClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Start the MCP server subprocess and initialize."""
        if not self.available:
            raise RuntimeError("StdioMCPClient not configured with command")

        # Merge environment variables
        process_env = os.environ.copy()
        process_env.update(self.env)

        try:
            self._process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env,
            )

            logger.info(
                "mcp_stdio_process_started",
                command=self.command,
                pid=self._process.pid,
            )

            # Send initialize request
            init_result = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "ohgrt-mcp-client",
                    "version": "1.0.0"
                }
            })

            if init_result.get("error"):
                raise RuntimeError(f"Initialize failed: {init_result['error']}")

            # Send initialized notification
            await self._send_notification("notifications/initialized", {})
            self._initialized = True

            server_info = init_result.get("result", {}).get("serverInfo", {})
            logger.info(
                "mcp_stdio_initialized",
                server=server_info.get("name", "unknown"),
                version=server_info.get("version", "unknown"),
            )

        except FileNotFoundError:
            raise RuntimeError(f"MCP server command not found: {self.command}")
        except Exception as e:
            logger.error("mcp_stdio_connect_failed", error=str(e))
            await self.close()
            raise

    async def close(self) -> None:
        """Stop the MCP server subprocess."""
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            except Exception:
                pass
            finally:
                self._process = None

        self._initialized = False
        self._tools_cache = None

    async def list_tools(self, force_refresh: bool = False) -> List[MCPTool]:
        """
        List available tools from the server.

        Returns:
            List of available MCPTool objects
        """
        if self._tools_cache and not force_refresh:
            return self._tools_cache

        try:
            result = await self._send_request("tools/list", {})

            if result.get("error"):
                logger.error("mcp_list_tools_error", error=result["error"])
                return []

            tools_data = result.get("result", {}).get("tools", [])
            self._tools_cache = [
                MCPTool(
                    name=t.get("name", ""),
                    description=t.get("description", ""),
                    inputSchema=t.get("inputSchema", {}),
                )
                for t in tools_data
            ]

            logger.info("mcp_tools_discovered", count=len(self._tools_cache))
            return self._tools_cache

        except Exception as e:
            logger.error("mcp_list_tools_failed", error=str(e))
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
            ToolCallResult with content and isError flag
        """
        try:
            result = await self._send_request("tools/call", {
                "name": name,
                "arguments": arguments or {},
            })

            if result.get("error"):
                error_msg = result["error"].get("message", str(result["error"]))
                return ToolCallResult(
                    content=[TextContent(text=f"Error: {error_msg}")],
                    isError=True,
                )

            tool_result = result.get("result", {})
            content_list = tool_result.get("content", [])

            # Convert content to TextContent objects
            contents = []
            for item in content_list:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        contents.append(TextContent(text=item.get("text", "")))
                    else:
                        contents.append(TextContent(text=json.dumps(item)))
                else:
                    contents.append(TextContent(text=str(item)))

            return ToolCallResult(
                content=contents if contents else [TextContent(text="")],
                isError=tool_result.get("isError", False),
            )

        except Exception as e:
            logger.error("mcp_tool_call_failed", tool=name, error=str(e))
            return ToolCallResult(
                content=[TextContent(text=f"Error calling tool: {str(e)}")],
                isError=True,
            )

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a JSON-RPC request and wait for response."""
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise RuntimeError("Process not running")

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }

        request_line = json.dumps(request) + "\n"

        try:
            async with self._write_lock:
                self._process.stdin.write(request_line.encode())
                await self._process.stdin.drain()

            async with self._read_lock:
                response_line = await asyncio.wait_for(
                    self._process.stdout.readline(),
                    timeout=self.timeout,
                )

            if not response_line:
                raise RuntimeError("Empty response from MCP server")

            response = json.loads(response_line.decode())
            return response

        except asyncio.TimeoutError:
            raise RuntimeError(f"Timeout waiting for response to {method}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")

    async def _send_notification(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if not self._process or not self._process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
        }

        notification_line = json.dumps(notification) + "\n"

        try:
            async with self._write_lock:
                self._process.stdin.write(notification_line.encode())
                await self._process.stdin.drain()
        except Exception:
            pass  # Notifications don't require acknowledgment
