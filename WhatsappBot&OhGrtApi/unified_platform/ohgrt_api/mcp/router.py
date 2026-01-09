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

from ohgrt_api.auth.dependencies import get_current_user, get_optional_user
from ohgrt_api.db.models import User
from ohgrt_api.logger import logger
from ohgrt_api.mcp.server import MCPServer
from ohgrt_api.mcp.client import MCPClient
from ohgrt_api.mcp.types import (
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

    # GitHub tools (require OAuth connection + set-repo)
    server.register_tool(
        name="github_search_issues",
        handler=_tool_github_search_issues,
        description="Search GitHub issues in your configured repository",
        input_schema=ToolInputSchema(
            properties={
                "query": {
                    "type": "string",
                    "description": "Search query for issues (e.g., 'bug', 'feature request', 'is:open')",
                },
            },
            required=["query"],
        ),
    )

    server.register_tool(
        name="github_create_issue",
        handler=_tool_github_create_issue,
        description="Create a new GitHub issue in your configured repository",
        input_schema=ToolInputSchema(
            properties={
                "title": {
                    "type": "string",
                    "description": "Issue title",
                },
                "body": {
                    "type": "string",
                    "description": "Issue description/body",
                },
            },
            required=["title", "body"],
        ),
    )

    logger.info("mcp_builtin_tools_registered", count=10)


# Tool implementations (these delegate to actual services)
async def _tool_get_weather(location: str, units: str = "metric") -> str:
    """Get weather - delegates to weather service."""
    from ohgrt_api.config import get_settings
    from ohgrt_api.services.weather_service import WeatherService

    settings = get_settings()
    service = WeatherService(settings)
    return await service.get_weather(location)


async def _tool_get_news(
    category: str = "general",
    country: str = "in",
    query: Optional[str] = None,
) -> str:
    """Get news - delegates to news service."""
    from ohgrt_api.config import get_settings
    from ohgrt_api.services.news_service import NewsService

    settings = get_settings()
    service = NewsService(settings)
    return await service.get_news(category=category, country=country, query=query)


async def _tool_check_pnr(pnr_number: str) -> str:
    """Check PNR - delegates to travel service."""
    from ohgrt_api.config import get_settings
    from ohgrt_api.services.travel_service import TravelService

    settings = get_settings()
    service = TravelService(settings)
    result = await service.get_pnr_status(pnr_number)
    return str(result)


async def _tool_get_horoscope(sign: str, day: str = "today") -> str:
    """Get horoscope - delegates to astrology service."""
    from ohgrt_api.services.astrology_service import AstrologyService

    service = AstrologyService()
    result = await service.get_horoscope(sign, day)
    return str(result)


async def _tool_translate(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
) -> str:
    """Translate text - uses LLM for translation."""
    # This would use the LLM for translation
    return f"Translation to {target_language}: [Requires LLM integration]"


async def _tool_generate_image(prompt: str, style: str = "realistic") -> str:
    """Generate image - uses fal.ai FLUX model."""
    from ohgrt_api.graph.nodes.image_node import generate_image_fal, _clean_prompt

    clean_prompt = _clean_prompt(prompt)
    if style and style != "realistic":
        clean_prompt = f"{clean_prompt}, {style} style"

    result = await generate_image_fal(clean_prompt)
    if result.get("success"):
        image_url = result.get("data", {}).get("image_url")
        if image_url:
            return f"Generated image: {image_url}"
    return f"Failed to generate image: {result.get('error', 'Unknown error')}"


async def _tool_web_search(query: str, num_results: int = 5) -> str:
    """Web search - uses Tavily search API."""
    from ohgrt_api.config import get_settings
    from langchain_community.tools.tavily_search import TavilySearchResults

    settings = get_settings()
    if not settings.tavily_api_key:
        return "Web search not configured. Set TAVILY_API_KEY in environment."

    import os
    os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

    search = TavilySearchResults(max_results=num_results)
    results = await search.ainvoke(query)

    if not results:
        return f"No results found for: {query}"

    # Format results
    output = []
    for r in results:
        output.append(f"• {r.get('title', 'No title')}\n  {r.get('url', '')}\n  {r.get('content', '')[:200]}...")

    return f"Search results for '{query}':\n\n" + "\n\n".join(output)


async def _tool_search_documents(query: str, document_type: str = "all") -> str:
    """Search documents - uses RAG service for PDF search."""
    from ohgrt_api.config import get_settings
    from ohgrt_api.services.rag_service import RAGService

    settings = get_settings()
    service = RAGService(settings)

    try:
        results = await service.similarity_search(query, k=5)
        if not results:
            return f"No documents found matching: {query}"

        output = []
        for i, (doc, score) in enumerate(results, 1):
            content = doc.page_content[:300] if doc.page_content else ""
            source = doc.metadata.get("source", "Unknown")
            output.append(f"{i}. [{source}] (score: {score:.2f})\n   {content}...")

        return f"Document search results for '{query}':\n\n" + "\n\n".join(output)
    except Exception as e:
        return f"Document search error: {str(e)}"


async def _tool_github_search_issues(query: str, user_id: Optional[str] = None, db: Optional[Any] = None) -> str:
    """Search GitHub issues - requires OAuth connection and set-repo."""
    from ohgrt_api.services.github_service import GitHubService
    from ohgrt_api.oauth.base import get_credential
    from ohgrt_api.db.session import SessionLocal

    # Get database session if not provided
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        # For now, we'll return a message that GitHub needs to be configured
        # In a real scenario, we'd get user_id from the request context
        return (
            "GitHub search requires authentication. "
            "Please connect GitHub via Settings > Integrations > GitHub, "
            "then set your repository using POST /github/set-repo with {\"repo\": \"repo-name\"}."
        )
    finally:
        if should_close:
            db.close()


async def _tool_github_create_issue(title: str, body: str, user_id: Optional[str] = None, db: Optional[Any] = None) -> str:
    """Create GitHub issue - requires OAuth connection and set-repo."""
    from ohgrt_api.services.github_service import GitHubService
    from ohgrt_api.oauth.base import get_credential
    from ohgrt_api.db.session import SessionLocal

    # Get database session if not provided
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        # For now, we'll return a message that GitHub needs to be configured
        return (
            "GitHub issue creation requires authentication. "
            "Please connect GitHub via Settings > Integrations > GitHub, "
            "then set your repository using POST /github/set-repo with {\"repo\": \"repo-name\"}."
        )
    finally:
        if should_close:
            db.close()


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


# ============================================================================
# Persistent MCP Server Management (Like Claude Desktop)
# ============================================================================

from ohgrt_api.auth.dependencies import get_db
from ohgrt_api.oauth.base import get_or_create_credential, get_credential, delete_credential
from sqlalchemy.orm import Session


class AddMCPServerRequest(BaseModel):
    """Request to add an MCP server."""
    name: str
    url: str
    token: Optional[str] = None
    description: Optional[str] = None


class MCPServerConfig(BaseModel):
    """Stored MCP server configuration."""
    name: str
    url: str
    description: Optional[str] = None
    connected: bool = False
    tool_count: int = 0


class MCPServersResponse(BaseModel):
    """Response with all user's MCP servers."""
    servers: List[MCPServerConfig]


@router.post("/servers", response_model=MCPServerConfig)
async def add_mcp_server(
    request: AddMCPServerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MCPServerConfig:
    """
    Add a persistent MCP server connection (like Claude Desktop).

    The server will be stored and its tools will be available
    in all future chat sessions.
    """
    # Test connection first
    client = MCPClient(base_url=request.url, token=request.token)
    tool_count = 0
    connected = False

    try:
        async with client:
            tools = await client.list_tools()
            tool_count = len(tools)
            connected = True
    except Exception as e:
        logger.warning("mcp_server_connection_test_failed", url=request.url, error=str(e))

    # Store using provider pattern: mcp_server_{name}
    provider_name = f"mcp_server_{request.name}"
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider=provider_name,
        access_token=request.token or "",
        extra_config={
            "name": request.name,
            "url": request.url,
            "description": request.description,
        },
    )

    logger.info(
        "mcp_server_added",
        user_id=str(current_user.id),
        name=request.name,
        url=request.url,
        tool_count=tool_count,
    )

    return MCPServerConfig(
        name=request.name,
        url=request.url,
        description=request.description,
        connected=connected,
        tool_count=tool_count,
    )


@router.get("/servers", response_model=MCPServersResponse)
async def list_mcp_servers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MCPServersResponse:
    """
    List all configured MCP servers for the current user.
    """
    from ohgrt_api.db.models import IntegrationCredential

    credentials = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == current_user.id,
            IntegrationCredential.provider.like("mcp_server_%"),
        )
        .all()
    )

    servers = []
    for cred in credentials:
        config = cred.config or {}
        servers.append(MCPServerConfig(
            name=config.get("name", cred.provider.replace("mcp_server_", "")),
            url=config.get("url", ""),
            description=config.get("description"),
            connected=False,  # We'd need to test each one
            tool_count=0,
        ))

    return MCPServersResponse(servers=servers)


@router.delete("/servers/{name}")
async def remove_mcp_server(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove an MCP server configuration.
    """
    provider_name = f"mcp_server_{name}"
    deleted = delete_credential(db, current_user.id, provider_name)

    if deleted:
        logger.info("mcp_server_removed", user_id=str(current_user.id), name=name)
        return {"success": True, "message": f"MCP server '{name}' removed"}

    raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")


@router.get("/servers/{name}/tools")
async def get_mcp_server_tools(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get tools from a specific MCP server.
    """
    provider_name = f"mcp_server_{name}"
    credential = get_credential(db, current_user.id, provider_name)

    if not credential:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")

    config = credential.config or {}
    url = config.get("url")
    token = credential.access_token if credential.access_token else None

    client = MCPClient(base_url=url, token=token)

    try:
        async with client:
            tools = await client.list_tools()
            return {
                "name": name,
                "url": url,
                "connected": True,
                "tools": [t.model_dump() for t in tools],
            }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "connected": False,
            "tools": [],
            "error": str(e),
        }


@router.post("/servers/{name}/call")
async def call_mcp_server_tool(
    name: str,
    request: ToolCallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ToolCallResponse:
    """
    Call a tool on a specific MCP server.
    """
    provider_name = f"mcp_server_{name}"
    credential = get_credential(db, current_user.id, provider_name)

    if not credential:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found")

    config = credential.config or {}
    url = config.get("url")
    token = credential.access_token if credential.access_token else None

    client = MCPClient(base_url=url, token=token)

    try:
        async with client:
            result = await client.call_tool(request.name, request.arguments)

            if result.isError:
                return ToolCallResponse(
                    success=False,
                    error=str(result.content),
                )

            # Extract text from result
            result_text = ""
            for content in result.content:
                if hasattr(content, "text"):
                    result_text += content.text
                elif isinstance(content, dict) and "text" in content:
                    result_text += content["text"]

            return ToolCallResponse(
                success=True,
                result=result_text,
            )
    except Exception as e:
        return ToolCallResponse(
            success=False,
            error=str(e),
        )


# ============================================================================
# MCP Manager Status & Control (Caching, Health Checks)
# ============================================================================

from ohgrt_api.mcp.manager import MCPManager, ServerStatus


class MCPManagerStats(BaseModel):
    """MCP manager statistics."""
    total_users: int
    total_servers: int
    connected_servers: int
    errored_servers: int
    total_tools: int
    cache_ttl_seconds: int
    health_check_running: bool


class ServerStatusResponse(BaseModel):
    """Status of an MCP server."""
    name: str
    url: str
    status: str
    tool_count: int
    latency_ms: Optional[float] = None
    last_check: Optional[str] = None
    last_error: Optional[str] = None


class AllServersStatusResponse(BaseModel):
    """Status of all user's MCP servers."""
    servers: List[ServerStatusResponse]
    cache_ttl_seconds: int


@router.get("/manager/stats", response_model=MCPManagerStats)
async def get_mcp_manager_stats() -> MCPManagerStats:
    """
    Get MCP manager statistics.

    Returns overall stats about cached servers, tools, and health checks.
    """
    manager = MCPManager.get_instance()
    stats = manager.get_stats()
    return MCPManagerStats(**stats)


@router.get("/manager/status", response_model=AllServersStatusResponse)
async def get_mcp_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AllServersStatusResponse:
    """
    Get status of all user's MCP servers.

    Shows connection status, latency, tool count, and any errors.
    """
    manager = MCPManager.get_instance()

    # Load servers from DB to ensure they're registered
    await manager.get_all_tools_for_user(db, current_user.id)

    # Get status of all servers
    connections = manager.get_all_server_status(current_user.id)

    servers = []
    for conn in connections:
        servers.append(ServerStatusResponse(
            name=conn.name,
            url=conn.url,
            status=conn.status.value,
            tool_count=conn.tool_count,
            latency_ms=conn.latency_ms,
            last_check=conn.last_check.isoformat() if conn.last_check else None,
            last_error=conn.last_error,
        ))

    return AllServersStatusResponse(
        servers=servers,
        cache_ttl_seconds=manager._cache_ttl,
    )


@router.post("/manager/refresh")
async def refresh_mcp_cache(
    server_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Force refresh MCP tool cache.

    Args:
        server_name: Optional specific server to refresh (None = all)
    """
    manager = MCPManager.get_instance()

    if server_name:
        # Refresh specific server
        tools = await manager.get_tools(current_user.id, server_name, force_refresh=True)
        return {
            "success": True,
            "server": server_name,
            "tool_count": len(tools),
            "message": f"Refreshed cache for {server_name}",
        }
    else:
        # Refresh all
        all_tools = await manager.get_all_tools_for_user(db, current_user.id, force_refresh=True)
        total_tools = sum(len(tools) for tools in all_tools.values())
        return {
            "success": True,
            "servers_refreshed": len(all_tools),
            "total_tools": total_tools,
            "message": f"Refreshed cache for {len(all_tools)} servers",
        }


@router.post("/manager/health-check/start")
async def start_mcp_health_checks() -> Dict[str, str]:
    """
    Start background MCP health checks.

    Health checks run every 60 seconds and update server status.
    """
    manager = MCPManager.get_instance()
    await manager.start_health_checks()
    return {"status": "started", "message": "MCP health checks started"}


@router.post("/manager/health-check/stop")
async def stop_mcp_health_checks() -> Dict[str, str]:
    """
    Stop background MCP health checks.
    """
    manager = MCPManager.get_instance()
    await manager.stop_health_checks()
    return {"status": "stopped", "message": "MCP health checks stopped"}


class CacheTTLRequest(BaseModel):
    """Request to set cache TTL."""
    ttl_seconds: int


@router.post("/manager/cache-ttl")
async def set_mcp_cache_ttl(request: CacheTTLRequest) -> Dict[str, Any]:
    """
    Set MCP tool cache TTL.

    Args:
        ttl_seconds: Cache TTL in seconds (60-3600)
    """
    if request.ttl_seconds < 60 or request.ttl_seconds > 3600:
        raise HTTPException(
            status_code=400,
            detail="TTL must be between 60 and 3600 seconds",
        )

    manager = MCPManager.get_instance()
    manager.set_cache_ttl(request.ttl_seconds)

    return {
        "success": True,
        "cache_ttl_seconds": request.ttl_seconds,
        "message": f"Cache TTL set to {request.ttl_seconds} seconds",
    }
