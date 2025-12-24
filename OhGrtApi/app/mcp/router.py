"""
MCP Router - FastAPI endpoints for MCP protocol.

Exposes the MCP server via HTTP with JSON-RPC 2.0.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_optional_user
from app.db.models import User
from app.logger import logger
from app.mcp.server import MCPServer
from app.mcp.client import MCPClient
from app.mcp.types import (
    JSONRPCRequest,
    JSONRPCResponse,
    MCPTool,
    ToolInputSchema,
    ListToolsResult,
    MCPServerInfo,
)

router = APIRouter(prefix="/mcp", tags=["MCP"])

# Global MCP server instance (initialized with app tools)
_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get or create the global MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = create_mcp_server()
    return _mcp_server


def create_mcp_server() -> MCPServer:
    """
    Create and configure the MCP server with all available tools.
    """
    server = MCPServer(
        name="ohgrt-mcp-server",
        version="2.1.0",
        instructions="OhGrt AI Assistant MCP Server. Provides tools for weather, news, travel, and more.",
    )

    # Register built-in tools
    _register_builtin_tools(server)

    return server


def _register_builtin_tools(server: MCPServer) -> None:
    """Register all built-in tools with the MCP server."""

    # Weather tool
    server.register_tool(
        name="get_weather",
        handler=_tool_get_weather,
        description="Get current weather for a location",
        input_schema=ToolInputSchema(
            properties={
                "location": {
                    "type": "string",
                    "description": "City name or coordinates (e.g., 'Delhi' or '28.6139,77.2090')",
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": "Temperature units",
                },
            },
            required=["location"],
        ),
    )

    # News tool
    server.register_tool(
        name="get_news",
        handler=_tool_get_news,
        description="Get latest news headlines",
        input_schema=ToolInputSchema(
            properties={
                "category": {
                    "type": "string",
                    "enum": ["general", "business", "technology", "sports", "entertainment", "health", "science"],
                    "description": "News category",
                },
                "country": {
                    "type": "string",
                    "description": "Country code (e.g., 'in', 'us')",
                },
                "query": {
                    "type": "string",
                    "description": "Search query for news",
                },
            },
            required=[],
        ),
    )

    # PNR Status tool
    server.register_tool(
        name="check_pnr",
        handler=_tool_check_pnr,
        description="Check Indian Railways PNR status",
        input_schema=ToolInputSchema(
            properties={
                "pnr_number": {
                    "type": "string",
                    "description": "10-digit PNR number",
                },
            },
            required=["pnr_number"],
        ),
    )

    # Horoscope tool
    server.register_tool(
        name="get_horoscope",
        handler=_tool_get_horoscope,
        description="Get daily horoscope for a zodiac sign",
        input_schema=ToolInputSchema(
            properties={
                "sign": {
                    "type": "string",
                    "enum": ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                             "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"],
                    "description": "Zodiac sign",
                },
                "day": {
                    "type": "string",
                    "enum": ["today", "tomorrow", "yesterday"],
                    "description": "Which day's horoscope",
                },
            },
            required=["sign"],
        ),
    )

    # Translation tool
    server.register_tool(
        name="translate",
        handler=_tool_translate,
        description="Translate text between languages",
        input_schema=ToolInputSchema(
            properties={
                "text": {
                    "type": "string",
                    "description": "Text to translate",
                },
                "target_language": {
                    "type": "string",
                    "description": "Target language (e.g., 'Hindi', 'Spanish', 'French')",
                },
                "source_language": {
                    "type": "string",
                    "description": "Source language (optional, auto-detected if not provided)",
                },
            },
            required=["text", "target_language"],
        ),
    )

    # Image generation tool
    server.register_tool(
        name="generate_image",
        handler=_tool_generate_image,
        description="Generate an image from a text description",
        input_schema=ToolInputSchema(
            properties={
                "prompt": {
                    "type": "string",
                    "description": "Description of the image to generate",
                },
                "style": {
                    "type": "string",
                    "enum": ["realistic", "artistic", "cartoon", "abstract"],
                    "description": "Image style",
                },
            },
            required=["prompt"],
        ),
    )

    # Web search tool
    server.register_tool(
        name="web_search",
        handler=_tool_web_search,
        description="Search the web for information",
        input_schema=ToolInputSchema(
            properties={
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10)",
                },
            },
            required=["query"],
        ),
    )

    # PDF/Document search tool
    server.register_tool(
        name="search_documents",
        handler=_tool_search_documents,
        description="Search through uploaded documents and PDFs",
        input_schema=ToolInputSchema(
            properties={
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "document_type": {
                    "type": "string",
                    "enum": ["pdf", "all"],
                    "description": "Type of documents to search",
                },
            },
            required=["query"],
        ),
    )

    logger.info("mcp_builtin_tools_registered", count=8)


# Tool implementations (these delegate to actual services)
async def _tool_get_weather(location: str, units: str = "metric") -> str:
    """Get weather - delegates to weather service."""
    from app.config import get_settings
    from app.services.weather_service import WeatherService

    settings = get_settings()
    service = WeatherService(settings)
    return await service.get_weather(location)


async def _tool_get_news(
    category: str = "general",
    country: str = "in",
    query: Optional[str] = None,
) -> str:
    """Get news - delegates to news service."""
    from app.config import get_settings
    from app.services.news_service import NewsService

    settings = get_settings()
    service = NewsService(settings)
    return await service.get_news(category=category, country=country, query=query)


async def _tool_check_pnr(pnr_number: str) -> str:
    """Check PNR - delegates to travel service."""
    from app.config import get_settings
    from app.services.travel_service import TravelService

    settings = get_settings()
    service = TravelService(settings)
    return await service.check_pnr_status(pnr_number)


async def _tool_get_horoscope(sign: str, day: str = "today") -> str:
    """Get horoscope - delegates to astrology service."""
    from app.config import get_settings
    from app.services.astrology_service import AstrologyService

    settings = get_settings()
    service = AstrologyService(settings)
    return await service.get_horoscope(sign, day)


async def _tool_translate(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
) -> str:
    """Translate text - uses LLM for translation."""
    # This would use the LLM for translation
    return f"Translation to {target_language}: [Requires LLM integration]"


async def _tool_generate_image(prompt: str, style: str = "realistic") -> str:
    """Generate image - delegates to image service."""
    from app.config import get_settings
    from app.services.image_service import ImageService

    settings = get_settings()
    service = ImageService(settings)
    result = await service.generate_image(prompt)
    return result


async def _tool_web_search(query: str, num_results: int = 5) -> str:
    """Web search - delegates to search service."""
    from app.config import get_settings
    from app.services.search_service import SearchService

    settings = get_settings()
    service = SearchService(settings)
    return await service.search(query, max_results=num_results)


async def _tool_search_documents(query: str, document_type: str = "all") -> str:
    """Search documents - delegates to PDF service."""
    from app.config import get_settings
    from app.services.pdf_service import PDFService

    settings = get_settings()
    service = PDFService(settings)
    return await service.search(query)


# ============================================================================
# API Endpoints
# ============================================================================

class MCPRequest(BaseModel):
    """Request body for MCP JSON-RPC endpoint."""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class ToolDiscoveryResponse(BaseModel):
    """Response for tool discovery endpoint."""
    tools: List[MCPTool]
    server: MCPServerInfo


class ToolCallRequest(BaseModel):
    """Request for calling a tool directly."""
    name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    """Response from tool call."""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


@router.post("", response_model=None)
@router.post("/", response_model=None)
async def mcp_jsonrpc_endpoint(
    request: MCPRequest,
    current_user: Optional[User] = Depends(get_optional_user),
) -> JSONRPCResponse:
    """
    MCP JSON-RPC 2.0 endpoint.

    Handles all MCP protocol methods:
    - initialize
    - tools/list
    - tools/call
    - resources/list
    - prompts/list
    """
    server = get_mcp_server()

    json_rpc_request = JSONRPCRequest(
        id=request.id or 1,
        method=request.method,
        params=request.params,
    )

    logger.info(
        "mcp_jsonrpc_request",
        method=request.method,
        user_id=str(current_user.id) if current_user else "anonymous",
    )

    response = await server.handle_request(json_rpc_request)
    return response


@router.get("/tools", response_model=ToolDiscoveryResponse)
async def discover_tools(
    current_user: Optional[User] = Depends(get_optional_user),
) -> ToolDiscoveryResponse:
    """
    Discover available MCP tools.

    Returns all tools registered with the MCP server along with
    their input schemas for client integration.
    """
    server = get_mcp_server()

    return ToolDiscoveryResponse(
        tools=server.get_tools(),
        server=server.server_info,
    )


@router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    current_user: User = Depends(get_current_user),
) -> ToolCallResponse:
    """
    Call a specific MCP tool.

    This is a convenience endpoint that wraps the JSON-RPC tools/call method.
    Requires authentication.
    """
    server = get_mcp_server()

    json_rpc_request = JSONRPCRequest(
        id=1,
        method="tools/call",
        params={
            "name": request.name,
            "arguments": request.arguments,
        },
    )

    logger.info(
        "mcp_tool_call",
        tool=request.name,
        user_id=str(current_user.id),
    )

    response = await server.handle_request(json_rpc_request)

    if response.error:
        return ToolCallResponse(
            success=False,
            error=response.error.message,
        )

    # Extract text from result
    result_text = ""
    if response.result and "content" in response.result:
        for content in response.result["content"]:
            if content.get("type") == "text":
                result_text += content.get("text", "")

    return ToolCallResponse(
        success=True,
        result=result_text or str(response.result),
    )


@router.get("/server-info", response_model=MCPServerInfo)
async def get_server_info() -> MCPServerInfo:
    """
    Get MCP server information.

    Returns server name, version, and capabilities.
    """
    server = get_mcp_server()
    return server.server_info


# ============================================================================
# External MCP Server Connection
# ============================================================================

class ConnectExternalRequest(BaseModel):
    """Request to connect to an external MCP server."""
    url: str
    token: Optional[str] = None
    name: Optional[str] = None


class ExternalServerInfo(BaseModel):
    """Information about connected external MCP server."""
    name: str
    url: str
    tools: List[MCPTool]
    connected: bool


@router.post("/connect", response_model=ExternalServerInfo)
async def connect_external_server(
    request: ConnectExternalRequest,
    current_user: User = Depends(get_current_user),
) -> ExternalServerInfo:
    """
    Connect to an external MCP server and discover its tools.

    This allows users to connect their own MCP-compatible servers
    and use them through the OhGrt platform.
    """
    client = MCPClient(
        base_url=request.url,
        token=request.token,
    )

    try:
        async with client:
            tools = await client.list_tools()

            return ExternalServerInfo(
                name=request.name or client._server_info.name if client._server_info else "unknown",
                url=request.url,
                tools=tools,
                connected=True,
            )
    except Exception as e:
        logger.error("mcp_connect_failed", url=request.url, error=str(e))
        return ExternalServerInfo(
            name=request.name or "unknown",
            url=request.url,
            tools=[],
            connected=False,
        )
