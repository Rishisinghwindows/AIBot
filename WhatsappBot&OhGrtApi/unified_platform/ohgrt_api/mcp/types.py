"""
MCP Types - Pydantic models following MCP specification.

Based on: https://modelcontextprotocol.io/specification/2025-11-25
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# JSON-RPC 2.0 Base Types
# ============================================================================

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request format."""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 error object."""
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response format."""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Union[str, int, None]
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


# ============================================================================
# MCP Error Codes (JSON-RPC compatible)
# ============================================================================

class MCPErrorCode(int, Enum):
    """Standard MCP/JSON-RPC error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # MCP-specific error codes
    TOOL_NOT_FOUND = -32001
    RESOURCE_NOT_FOUND = -32002
    PERMISSION_DENIED = -32003
    RATE_LIMITED = -32004


# ============================================================================
# Content Types
# ============================================================================

class TextContent(BaseModel):
    """Text content in tool results."""
    type: Literal["text"] = "text"
    text: str


class ImageContent(BaseModel):
    """Image content in tool results."""
    type: Literal["image"] = "image"
    data: str  # Base64-encoded image data
    mimeType: str = "image/png"


class ResourceContent(BaseModel):
    """Embedded resource content."""
    type: Literal["resource"] = "resource"
    resource: "MCPResource"


ContentType = Union[TextContent, ImageContent, ResourceContent]


# ============================================================================
# Tool Definitions
# ============================================================================

class ToolInputSchema(BaseModel):
    """JSON Schema for tool input parameters."""
    type: Literal["object"] = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    additionalProperties: bool = False


class MCPTool(BaseModel):
    """MCP Tool definition."""
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Human-readable tool description")
    inputSchema: ToolInputSchema = Field(..., description="JSON Schema for inputs")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or coordinates"
                        }
                    },
                    "required": ["location"]
                }
            }
        }


class ToolCallResult(BaseModel):
    """Result of a tool execution."""
    content: List[ContentType] = Field(default_factory=list)
    isError: bool = False


# ============================================================================
# Resource Definitions
# ============================================================================

class MCPResource(BaseModel):
    """MCP Resource definition."""
    uri: str = Field(..., description="Unique resource URI")
    name: str = Field(..., description="Human-readable resource name")
    description: Optional[str] = Field(None, description="Resource description")
    mimeType: Optional[str] = Field(None, description="MIME type of content")


class ResourceTemplate(BaseModel):
    """Template for dynamic resource URIs."""
    uriTemplate: str = Field(..., description="URI template with {placeholders}")
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


# ============================================================================
# Prompt Definitions
# ============================================================================

class PromptArgument(BaseModel):
    """Argument for a prompt template."""
    name: str
    description: Optional[str] = None
    required: bool = False


class MCPPrompt(BaseModel):
    """MCP Prompt definition."""
    name: str = Field(..., description="Unique prompt identifier")
    description: Optional[str] = Field(None, description="Prompt description")
    arguments: List[PromptArgument] = Field(default_factory=list)


class PromptMessage(BaseModel):
    """Message in a prompt result."""
    role: Literal["user", "assistant"]
    content: ContentType


# ============================================================================
# Server Capabilities
# ============================================================================

class ToolsCapability(BaseModel):
    """Tools capability configuration."""
    listChanged: bool = False  # Whether server supports tools/list_changed


class ResourcesCapability(BaseModel):
    """Resources capability configuration."""
    subscribe: bool = False  # Whether server supports resource subscriptions
    listChanged: bool = False


class PromptsCapability(BaseModel):
    """Prompts capability configuration."""
    listChanged: bool = False


class LoggingCapability(BaseModel):
    """Logging capability configuration."""
    pass  # Presence indicates logging support


class MCPServerCapabilities(BaseModel):
    """Capabilities that an MCP server can support."""
    tools: Optional[ToolsCapability] = None
    resources: Optional[ResourcesCapability] = None
    prompts: Optional[PromptsCapability] = None
    logging: Optional[LoggingCapability] = None


class MCPServerInfo(BaseModel):
    """MCP Server information returned during initialization."""
    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")
    capabilities: MCPServerCapabilities = Field(default_factory=MCPServerCapabilities)
    instructions: Optional[str] = Field(None, description="Usage instructions")


# ============================================================================
# Client Capabilities
# ============================================================================

class SamplingCapability(BaseModel):
    """Sampling capability for LLM requests."""
    pass


class RootsCapability(BaseModel):
    """Roots capability for filesystem access."""
    listChanged: bool = False


class MCPClientCapabilities(BaseModel):
    """Capabilities that an MCP client can support."""
    sampling: Optional[SamplingCapability] = None
    roots: Optional[RootsCapability] = None


class MCPClientInfo(BaseModel):
    """MCP Client information sent during initialization."""
    name: str
    version: str
    capabilities: MCPClientCapabilities = Field(default_factory=MCPClientCapabilities)


# ============================================================================
# Initialization Messages
# ============================================================================

class InitializeParams(BaseModel):
    """Parameters for initialize request."""
    protocolVersion: str = "2025-11-25"
    clientInfo: MCPClientInfo


class InitializeResult(BaseModel):
    """Result of initialize request."""
    protocolVersion: str = "2025-11-25"
    serverInfo: MCPServerInfo


# ============================================================================
# Tool-related Messages
# ============================================================================

class ListToolsResult(BaseModel):
    """Result of tools/list request."""
    tools: List[MCPTool]
    nextCursor: Optional[str] = None  # For pagination


class CallToolParams(BaseModel):
    """Parameters for tools/call request."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Resource-related Messages
# ============================================================================

class ListResourcesResult(BaseModel):
    """Result of resources/list request."""
    resources: List[MCPResource]
    nextCursor: Optional[str] = None


class ReadResourceParams(BaseModel):
    """Parameters for resources/read request."""
    uri: str


class ReadResourceResult(BaseModel):
    """Result of resources/read request."""
    contents: List[ContentType]


# ============================================================================
# Prompt-related Messages
# ============================================================================

class ListPromptsResult(BaseModel):
    """Result of prompts/list request."""
    prompts: List[MCPPrompt]
    nextCursor: Optional[str] = None


class GetPromptParams(BaseModel):
    """Parameters for prompts/get request."""
    name: str
    arguments: Dict[str, str] = Field(default_factory=dict)


class GetPromptResult(BaseModel):
    """Result of prompts/get request."""
    description: Optional[str] = None
    messages: List[PromptMessage]


# ============================================================================
# Logging Messages
# ============================================================================

class LogLevel(str, Enum):
    """Log levels for MCP logging."""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class LogMessage(BaseModel):
    """Log message notification."""
    level: LogLevel
    logger: Optional[str] = None
    data: Any = None


# ============================================================================
# Progress Tracking
# ============================================================================

class ProgressToken(BaseModel):
    """Token for progress tracking."""
    token: Union[str, int]


class ProgressNotification(BaseModel):
    """Progress update notification."""
    progressToken: Union[str, int]
    progress: float  # 0.0 to 1.0
    total: Optional[float] = None


# Update forward references
ResourceContent.model_rebuild()
