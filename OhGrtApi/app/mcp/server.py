"""
MCP Server Implementation

A proper MCP server that exposes tools via JSON-RPC 2.0 protocol.
Follows the specification at https://modelcontextprotocol.io/specification/2025-11-25
"""

import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from uuid import uuid4

from app.logger import logger
from app.mcp.types import (
    CallToolParams,
    InitializeParams,
    InitializeResult,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    MCPErrorCode,
    MCPPrompt,
    MCPResource,
    MCPServerCapabilities,
    MCPServerInfo,
    MCPTool,
    PromptsCapability,
    ResourcesCapability,
    TextContent,
    ToolCallResult,
    ToolInputSchema,
    ToolsCapability,
)

F = TypeVar("F", bound=Callable[..., Any])


class MCPServer:
    """
    MCP Server that exposes tools, resources, and prompts via JSON-RPC 2.0.

    Usage:
        server = MCPServer(name="my-server", version="1.0.0")

        @server.tool()
        async def get_weather(location: str) -> str:
            '''Get weather for a location.'''
            return f"Weather for {location}: Sunny, 25°C"

        # Handle incoming JSON-RPC requests
        response = await server.handle_request(request)
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        instructions: Optional[str] = None,
    ):
        self.name = name
        self.version = version
        self.instructions = instructions

        self._tools: Dict[str, Dict[str, Any]] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, MCPPrompt] = {}

        self._initialized = False
        self._protocol_version = "2025-11-25"

        # Method handlers for JSON-RPC
        self._handlers: Dict[str, Callable] = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
        }

    @property
    def capabilities(self) -> MCPServerCapabilities:
        """Return server capabilities based on registered handlers."""
        return MCPServerCapabilities(
            tools=ToolsCapability() if self._tools else None,
            resources=ResourcesCapability() if self._resources else None,
            prompts=PromptsCapability() if self._prompts else None,
        )

    @property
    def server_info(self) -> MCPServerInfo:
        """Return server information."""
        return MCPServerInfo(
            name=self.name,
            version=self.version,
            capabilities=self.capabilities,
            instructions=self.instructions,
        )

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Callable[[F], F]:
        """
        Decorator to register a tool.

        Args:
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)

        Example:
            @server.tool()
            async def search(query: str) -> str:
                '''Search for information.'''
                return "results..."
        """
        def decorator(func: F) -> F:
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or f"Execute {tool_name}"

            # Build input schema from function signature
            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name in ("self", "cls"):
                    continue

                # Determine type
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_type = "array"
                    elif param.annotation == dict or param.annotation == Dict:
                        param_type = "object"

                properties[param_name] = {
                    "type": param_type,
                    "description": f"Parameter: {param_name}",
                }

                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            input_schema = ToolInputSchema(
                properties=properties,
                required=required,
            )

            mcp_tool = MCPTool(
                name=tool_name,
                description=tool_description.strip(),
                inputSchema=input_schema,
            )

            self._tools[tool_name] = {
                "definition": mcp_tool,
                "handler": func,
            }

            logger.info("mcp_tool_registered", tool_name=tool_name)
            return func

        return decorator

    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str,
        input_schema: Optional[ToolInputSchema] = None,
    ) -> None:
        """
        Programmatically register a tool.

        Args:
            name: Tool name
            handler: Async function to execute
            description: Tool description
            input_schema: JSON Schema for inputs
        """
        if input_schema is None:
            input_schema = ToolInputSchema()

        mcp_tool = MCPTool(
            name=name,
            description=description,
            inputSchema=input_schema,
        )

        self._tools[name] = {
            "definition": mcp_tool,
            "handler": handler,
        }

        logger.info("mcp_tool_registered", tool_name=name)

    def register_resource(self, resource: MCPResource) -> None:
        """Register a resource."""
        self._resources[resource.uri] = resource
        logger.info("mcp_resource_registered", uri=resource.uri)

    def register_prompt(self, prompt: MCPPrompt) -> None:
        """Register a prompt template."""
        self._prompts[prompt.name] = prompt
        logger.info("mcp_prompt_registered", name=prompt.name)

    async def handle_request(
        self,
        request: Union[JSONRPCRequest, Dict[str, Any]],
    ) -> JSONRPCResponse:
        """
        Handle an incoming JSON-RPC request.

        Args:
            request: JSON-RPC request object or dict

        Returns:
            JSON-RPC response
        """
        try:
            # Parse request if dict
            if isinstance(request, dict):
                request = JSONRPCRequest(**request)

            logger.debug("mcp_request", method=request.method, id=request.id)

            # Find handler
            handler = self._handlers.get(request.method)
            if not handler:
                return JSONRPCResponse(
                    id=request.id,
                    error=JSONRPCError(
                        code=MCPErrorCode.METHOD_NOT_FOUND,
                        message=f"Method not found: {request.method}",
                    ),
                )

            # Execute handler
            result = await handler(request.params or {})

            return JSONRPCResponse(
                id=request.id,
                result=result,
            )

        except Exception as e:
            logger.error("mcp_request_error", error=str(e))
            return JSONRPCResponse(
                id=getattr(request, "id", None),
                error=JSONRPCError(
                    code=MCPErrorCode.INTERNAL_ERROR,
                    message=str(e),
                ),
            )

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        init_params = InitializeParams(**params)

        logger.info(
            "mcp_initialize",
            client_name=init_params.clientInfo.name,
            client_version=init_params.clientInfo.version,
            protocol_version=init_params.protocolVersion,
        )

        result = InitializeResult(
            protocolVersion=self._protocol_version,
            serverInfo=self.server_info,
        )

        return result.model_dump()

    async def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialized notification."""
        self._initialized = True
        logger.info("mcp_initialized")
        return None

    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request."""
        return {}

    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = [t["definition"] for t in self._tools.values()]
        result = ListToolsResult(tools=tools)
        return result.model_dump()

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        call_params = CallToolParams(**params)

        tool = self._tools.get(call_params.name)
        if not tool:
            raise ValueError(f"Tool not found: {call_params.name}")

        handler = tool["handler"]

        logger.info(
            "mcp_tool_call",
            tool=call_params.name,
            arguments=call_params.arguments,
        )

        try:
            # Execute tool
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**call_params.arguments)
            else:
                result = handler(**call_params.arguments)

            # Wrap result in content
            if isinstance(result, str):
                content = [TextContent(text=result)]
            elif isinstance(result, dict):
                import json
                content = [TextContent(text=json.dumps(result, indent=2))]
            elif isinstance(result, list):
                content = result
            else:
                content = [TextContent(text=str(result))]

            tool_result = ToolCallResult(content=content)
            return tool_result.model_dump()

        except Exception as e:
            logger.error("mcp_tool_error", tool=call_params.name, error=str(e))
            tool_result = ToolCallResult(
                content=[TextContent(text=f"Error: {str(e)}")],
                isError=True,
            )
            return tool_result.model_dump()

    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources = list(self._resources.values())
        result = ListResourcesResult(resources=resources)
        return result.model_dump()

    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        if not uri or uri not in self._resources:
            raise ValueError(f"Resource not found: {uri}")

        # For now, return empty content (implement actual reading as needed)
        return {"contents": []}

    async def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        prompts = list(self._prompts.values())
        result = ListPromptsResult(prompts=prompts)
        return result.model_dump()

    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        name = params.get("name")
        if not name or name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")

        # For now, return empty messages (implement actual prompt as needed)
        return {"description": self._prompts[name].description, "messages": []}

    def get_tools(self) -> List[MCPTool]:
        """Get all registered tools."""
        return [t["definition"] for t in self._tools.values()]

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())
