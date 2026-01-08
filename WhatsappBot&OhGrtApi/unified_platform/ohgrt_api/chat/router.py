"""
Chat API Router.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ohgrt_api.auth.dependencies import User, get_current_user, get_optional_user
from ohgrt_api.chat.service import get_chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    history: Optional[List[ChatMessage]] = Field(
        None, description="Conversation history"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="Assistant response")
    conversation_id: Optional[str] = Field(None)
    intent: Optional[str] = Field(None, description="Detected intent")
    metadata: Optional[Dict[str, Any]] = Field(None)


@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    user: User = Depends(get_current_user),
):
    """
    Send a message to the AI assistant.

    Args:
        request: ChatRequest with message and optional context
        user: Authenticated user

    Returns:
        ChatResponse with AI response
    """
    try:
        service = get_chat_service()

        # Convert history to list of dicts
        history = None
        if request.history:
            history = [{"role": m.role, "content": m.content} for m in request.history]

        result = await service.process_message(
            message=request.message,
            user_id=user.user_id,
            conversation_history=history,
            context=request.context,
        )

        return ChatResponse(
            response=result.get("response", ""),
            conversation_id=request.conversation_id,
            intent=result.get("intent"),
            metadata=result.get("metadata"),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed")


@router.post("/completion")
async def get_completion(
    request: ChatRequest,
    user: User = Depends(get_current_user),
):
    """
    Get a direct LLM completion.

    Args:
        request: ChatRequest with message
        user: Authenticated user

    Returns:
        Completion response
    """
    try:
        service = get_chat_service()

        # Build messages
        messages = []
        if request.history:
            messages.extend(
                [{"role": m.role, "content": m.content} for m in request.history]
            )
        messages.append({"role": "user", "content": request.message})

        response = await service.get_completion(messages)

        return {"response": response}

    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(status_code=500, detail="Completion failed")


@router.get("/health")
async def chat_health():
    """Chat service health check."""
    return {"status": "healthy", "service": "chat"}
