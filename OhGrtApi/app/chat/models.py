from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatSendRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[UUID] = Field(
        None, description="Continue existing conversation (optional)"
    )
    tools: Optional[List[str]] = Field(
        None,
        description="Optional list of tool names to enable for this message",
    )


class ChatMessageResponse(BaseModel):
    """A single chat message."""

    id: UUID
    role: str  # "user" or "assistant"
    content: str
    message_metadata: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSendResponse(BaseModel):
    """Response after sending a message."""

    conversation_id: UUID
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ToolInfo(BaseModel):
    """Available tool metadata."""

    name: str
    description: str


class ChatHistoryResponse(BaseModel):
    """Response containing chat history."""

    messages: List[ChatMessageResponse]
    has_more: bool


class ConversationSummary(BaseModel):
    """Summary of a conversation."""

    id: UUID
    title: Optional[str] = None
    message_count: int
    last_message_at: datetime
    created_at: datetime


# MCP Tool Models
class MCPToolCreate(BaseModel):
    """Request to create an MCP tool."""

    name: str = Field(..., min_length=1, max_length=100, description="Tool name")
    description: Optional[str] = Field(None, max_length=500, description="Tool description")
    tool_type: str = Field(..., description="Type of tool: oauth, api_key, mcp")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool configuration")
    enabled: bool = Field(default=True, description="Whether the tool is enabled")


class MCPToolUpdate(BaseModel):
    """Request to update an MCP tool."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tool_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class MCPToolResponse(BaseModel):
    """MCP tool response."""

    id: UUID
    name: str
    description: Optional[str] = None
    tool_type: str
    config: Dict[str, Any] = {}
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Streaming models
class StreamingAskRequest(BaseModel):
    """Request for streaming chat."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[UUID] = Field(None, description="Continue existing conversation")
    session_id: Optional[str] = Field(None, description="Session ID for anonymous users (used when not authenticated)")
    tools: Optional[List[str]] = Field(None, description="Optional list of tool names to enable")


class ConversationCreate(BaseModel):
    """Request to create a conversation."""

    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")


class ConversationUpdate(BaseModel):
    """Request to update a conversation."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
