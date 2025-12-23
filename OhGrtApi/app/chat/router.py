from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_optional_user
from app.chat.models import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatSendRequest,
    ChatSendResponse,
    ConversationCreate,
    ConversationSummary,
    ConversationUpdate,
    MCPToolCreate,
    MCPToolResponse,
    MCPToolUpdate,
    StreamingAskRequest,
    ToolInfo,
)
from app.chat.service import ChatService
from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import User
from app.graph.tool_agent import build_tool_agent
from app.logger import logger
from app.services.mcp_tool_service import MCPToolService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/send",
    response_model=ChatSendResponse,
    summary="Send a chat message",
    description="""
Send a message to the AI assistant and receive a response.

## Tools
Optionally specify which tools the assistant can use:
- `weather`: Get weather information for cities
- `pdf`: Search uploaded PDF documents
- `sql`: Query connected databases
- `github`: Access GitHub repositories (requires connected provider)
- `jira`: Access Jira issues (requires connected provider)
- `slack`: Access Slack channels (requires connected provider)

## Conversation
- If `conversation_id` is provided, continues existing conversation
- If omitted, starts a new conversation (ID returned in response)
    """,
    responses={
        200: {
            "description": "Message sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_message": {
                            "id": "550e8400-e29b-41d4-a716-446655440001",
                            "role": "user",
                            "content": "What's the weather in Tokyo?",
                            "message_metadata": {},
                            "created_at": "2025-01-15T10:30:00Z"
                        },
                        "assistant_message": {
                            "id": "550e8400-e29b-41d4-a716-446655440002",
                            "role": "assistant",
                            "content": "The current weather in Tokyo is 15°C with clear skies.",
                            "message_metadata": {"category": "weather", "tool_used": "weather"},
                            "created_at": "2025-01-15T10:30:01Z"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            }
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {"detail": "Missing required security headers: X-Request-ID, X-Nonce"}
                }
            }
        }
    }
)
async def send_message(
    request: ChatSendRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ChatSendResponse:
    """
    Send a message and receive an AI response.

    The message is processed by the AI agent which may use various tools
    (weather, PDF search, SQL queries, etc.) to generate a response.
    """
    service = ChatService(settings, db)
    user_msg, assistant_msg, conv_id = await service.send_message(
        user=user,
        message=request.message,
        conversation_id=request.conversation_id,
        allowed_tools=request.tools,
    )

    return ChatSendResponse(
        conversation_id=conv_id,
        user_message=ChatMessageResponse(
            id=user_msg.id,
            role=user_msg.role,
            content=user_msg.content,
            message_metadata=user_msg.message_metadata or {},
            created_at=user_msg.created_at,
        ),
        assistant_message=ChatMessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            message_metadata=assistant_msg.message_metadata or {},
            created_at=assistant_msg.created_at,
        ),
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    limit: int = Query(50, ge=1, le=100, description="Max messages to return"),
    before: Optional[datetime] = Query(None, description="Pagination cursor"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ChatHistoryResponse:
    """
    Get chat history for the authenticated user.

    Can filter by conversation_id or get all messages.
    Supports cursor-based pagination via the 'before' parameter.
    """
    conv_uuid = UUID(conversation_id) if conversation_id else None

    service = ChatService(settings, db)
    messages, has_more = service.get_history(
        user=user,
        conversation_id=conv_uuid,
        limit=limit,
        before=before,
    )

    return ChatHistoryResponse(
        messages=[
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                message_metadata=m.message_metadata or {},
                created_at=m.created_at,
            )
            for m in messages
        ],
        has_more=has_more,
    )


@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    limit: int = Query(20, ge=1, le=50, description="Max conversations to return"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> List[ConversationSummary]:
    """
    Get list of user's conversations with summaries.

    Returns conversations sorted by most recent activity.
    """
    service = ChatService(settings, db)
    conversations = service.get_conversations(user=user, limit=limit)

    return [
        ConversationSummary(
            id=conv["id"],
            title=conv["title"],
            message_count=conv["message_count"],
            last_message_at=conv["last_message_at"],
            created_at=conv["created_at"],
        )
        for conv in conversations
    ]


@router.get(
    "/tools",
    response_model=List[ToolInfo],
    summary="List available tools",
    description="""
Get the list of tools the AI assistant can use.

## Tool Availability
Tools are available based on:
- Built-in tools (weather, pdf, sql) - always available
- Provider tools (github, jira, slack) - available when provider is connected

## Response
Each tool includes:
- `name`: Tool identifier to pass in chat request
- `description`: What the tool does
    """,
    responses={
        200: {
            "description": "Tools retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {"name": "weather", "description": "Get current weather for a city"},
                        {"name": "pdf", "description": "Search uploaded PDF documents"},
                        {"name": "github", "description": "Access GitHub repositories"}
                    ]
                }
            }
        }
    }
)
async def list_tools(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> List[ToolInfo]:
    """
    List available tools the assistant can use.
    """
    # Build user-scoped agent so availability can reflect connected providers
    from app.chat.service import ChatService  # local import to avoid circular

    service = ChatService(settings, db)
    credentials = service._load_credentials(user)  # internal helper for availability
    agent = build_tool_agent(settings, credentials=credentials)
    tools = agent.list_tools()
    return [ToolInfo(name=t["name"], description=t["description"]) for t in tools]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Delete a conversation and all its messages.
    """
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    service = ChatService(settings, db)
    deleted = service.delete_conversation(user=user, conversation_id=conv_uuid)

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted", "messages_deleted": deleted}


# =============================================================================
# STREAMING /ask ENDPOINT (SSE)
# =============================================================================


async def generate_sse_response(
    message: str,
    settings: Settings,
    db: Session,
    user: Optional[User] = None,
    session_id: Optional[str] = None,
    conversation_id: Optional[UUID] = None,
    allowed_tools: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for streaming chat response.

    Supports both authenticated users and anonymous sessions.
    """
    from uuid import uuid4
    from app.db.models import ChatMessage

    # Generate or use conversation ID
    conv_id = conversation_id or uuid4()

    # Send conversation_id/session_id event
    if user:
        yield f"event: conversation_id\ndata: {json.dumps({'conversation_id': str(conv_id)})}\n\n"
    else:
        yield f"event: session_id\ndata: {json.dumps({'session_id': session_id or str(conv_id)})}\n\n"

    # Store user message (only for authenticated users with DB storage)
    if user:
        user_msg = ChatMessage(
            user_id=user.id,
            conversation_id=conv_id,
            role="user",
            content=message,
            message_metadata={},
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

    # Load user credentials (only for authenticated users)
    credentials = {}
    if user:
        service = ChatService(settings, db)
        credentials = service._load_credentials(user)

    try:
        # Build agent and invoke
        agent = build_tool_agent(settings, credentials=credentials)
        result = await agent.invoke(message, allowed_tools=allowed_tools)

        ai_content = result.get("response", "I apologize, but I couldn't process your request.")
        route_log = result.get("route_log", [])
        category = result.get("category", "chat")
        media_url = result.get("media_url")
        intent = result.get("intent")
        structured_data = result.get("structured_data")

        # Send content in chunks for streaming effect
        chunk_size = 50
        for i in range(0, len(ai_content), chunk_size):
            chunk = ai_content[i:i + chunk_size]
            yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"
            await asyncio.sleep(0.02)  # Small delay for streaming effect

        # Send metadata
        metadata = {
            "category": category,
            "route_log": route_log if isinstance(route_log, list) else [route_log],
        }
        if media_url:
            metadata["media_url"] = media_url
        if intent:
            metadata["intent"] = intent
        if structured_data:
            metadata["structured_data"] = structured_data

        yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

        # Store assistant message (only for authenticated users)
        if user:
            msg_metadata = {
                "category": category,
                "route_log": ", ".join(route_log) if isinstance(route_log, list) else str(route_log),
            }
            if media_url:
                msg_metadata["media_url"] = media_url
            if intent:
                msg_metadata["intent"] = intent
            if structured_data:
                msg_metadata["structured_data"] = structured_data

            assistant_msg = ChatMessage(
                user_id=user.id,
                conversation_id=conv_id,
                role="assistant",
                content=ai_content,
                message_metadata=msg_metadata,
            )
            db.add(assistant_msg)
            db.commit()

        logger.info(
            "streaming_chat_complete",
            user_id=str(user.id) if user else "anonymous",
            conversation_id=str(conv_id),
            category=category,
        )

    except Exception as e:
        logger.error("streaming_chat_error", error=str(e), user_id=str(user.id) if user else "anonymous")
        error_msg = "I apologize, but an error occurred while processing your request."
        yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"

    # Send done event
    yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"


@router.post(
    "/ask",
    summary="Streaming chat endpoint",
    description="""
Send a message and receive a streaming AI response via Server-Sent Events (SSE).

Supports both authenticated users (with Bearer token) and anonymous users (with session_id).

## Events
- `conversation_id`: Contains the conversation ID (for authenticated users)
- `session_id`: Contains the session ID (for anonymous users)
- `chunk`: Contains a chunk of the response content
- `metadata`: Contains response metadata (category, tools used, media_url, intent, structured_data)
- `error`: Contains error information if something went wrong
- `done`: Signals the end of the stream

## Usage
```javascript
// For authenticated users - include Bearer token in headers
// For anonymous users - include session_id in request body
fetch('/chat/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: "Hello", session_id: "optional-for-anonymous" })
});
```
    """,
)
async def streaming_ask(
    request: StreamingAskRequest,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Send a message and receive a streaming AI response via SSE.

    Works for both authenticated and anonymous users.
    """
    return StreamingResponse(
        generate_sse_response(
            message=request.message,
            settings=settings,
            db=db,
            user=user,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            allowed_tools=request.tools,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# MCP TOOLS CRUD ENDPOINTS
# =============================================================================


@router.get("/mcp-tools", response_model=List[MCPToolResponse])
async def list_mcp_tools(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[MCPToolResponse]:
    """
    List all MCP tools for the authenticated user.
    """
    service = MCPToolService(db)
    tools = service.get_tools_by_user(user.id)

    return [
        MCPToolResponse(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            tool_type=tool.tool_type,
            config=tool.config or {},
            enabled=tool.enabled,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
        )
        for tool in tools
    ]


@router.post("/mcp-tools", response_model=MCPToolResponse, status_code=201)
async def create_mcp_tool(
    request: MCPToolCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MCPToolResponse:
    """
    Create a new MCP tool for the authenticated user.
    """
    service = MCPToolService(db)
    tool = service.create_tool(
        user_id=user.id,
        name=request.name,
        tool_type=request.tool_type,
        description=request.description,
        config=request.config,
        enabled=request.enabled,
    )

    return MCPToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        tool_type=tool.tool_type,
        config=tool.config or {},
        enabled=tool.enabled,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )


@router.get("/mcp-tools/{tool_id}", response_model=MCPToolResponse)
async def get_mcp_tool(
    tool_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MCPToolResponse:
    """
    Get a specific MCP tool by ID.
    """
    try:
        tool_uuid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tool ID")

    service = MCPToolService(db)
    tool = service.get_tool(tool_uuid, user.id)

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return MCPToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        tool_type=tool.tool_type,
        config=tool.config or {},
        enabled=tool.enabled,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )


@router.put("/mcp-tools/{tool_id}", response_model=MCPToolResponse)
async def update_mcp_tool(
    tool_id: str,
    request: MCPToolUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MCPToolResponse:
    """
    Update an MCP tool.
    """
    try:
        tool_uuid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tool ID")

    service = MCPToolService(db)
    tool = service.update_tool(
        tool_id=tool_uuid,
        user_id=user.id,
        name=request.name,
        description=request.description,
        tool_type=request.tool_type,
        config=request.config,
        enabled=request.enabled,
    )

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return MCPToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        tool_type=tool.tool_type,
        config=tool.config or {},
        enabled=tool.enabled,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )


@router.delete("/mcp-tools/{tool_id}")
async def delete_mcp_tool(
    tool_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Delete an MCP tool.
    """
    try:
        tool_uuid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tool ID")

    service = MCPToolService(db)
    deleted = service.delete_tool(tool_uuid, user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Tool not found")

    return {"message": "Tool deleted successfully"}


@router.post("/mcp-tools/{tool_id}/toggle", response_model=MCPToolResponse)
async def toggle_mcp_tool(
    tool_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MCPToolResponse:
    """
    Toggle the enabled state of an MCP tool.
    """
    try:
        tool_uuid = UUID(tool_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tool ID")

    service = MCPToolService(db)
    tool = service.toggle_tool(tool_uuid, user.id)

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return MCPToolResponse(
        id=tool.id,
        name=tool.name,
        description=tool.description,
        tool_type=tool.tool_type,
        config=tool.config or {},
        enabled=tool.enabled,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )


# =============================================================================
# CONVERSATION MANAGEMENT ENDPOINTS
# =============================================================================


@router.post("/conversations", response_model=ConversationSummary, status_code=201)
async def create_conversation(
    request: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationSummary:
    """
    Create a new conversation.
    """
    service = ConversationService(db)
    conversation = service.create_conversation(user.id, request.title)

    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        message_count=0,
        last_message_at=conversation.created_at,
        created_at=conversation.created_at,
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationSummary)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ConversationSummary:
    """
    Update a conversation's title.
    """
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    service = ConversationService(db)
    conversation = service.update_conversation(conv_uuid, user.id, title=request.title)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get message count
    chat_service = ChatService(settings, db)
    convs = chat_service.get_conversations(user=user, limit=100)
    conv_data = next((c for c in convs if c["id"] == conv_uuid), None)
    message_count = conv_data["message_count"] if conv_data else 0

    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        message_count=message_count,
        last_message_at=conversation.updated_at,
        created_at=conversation.created_at,
    )
