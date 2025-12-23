"""
Web Chat Router

Anonymous chat endpoints for D23Web.
Uses session tokens instead of user authentication.

Persistence Strategy:
- Redis: Fast session access, rate limiting (volatile)
- PostgreSQL: Long-term chat history and context (durable)
"""

from __future__ import annotations

import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Request, Response, File, UploadFile
from pydantic import BaseModel, Field

from app.config import get_settings
from app.logger import logger
from app.i18n import detect_language

router = APIRouter(prefix="/web", tags=["web-chat"])

# Lazy-loaded context service for PostgreSQL persistence
_context_service = None


async def get_context_service():
    """Get or create the PostgreSQL-backed context service."""
    global _context_service
    if _context_service is None:
        settings = get_settings()
        if not settings.lite_mode:
            try:
                from app.services.context_service import get_context_service as _get_ctx_svc
                _context_service = _get_ctx_svc()
                logger.info("web_context_service_initialized", persistence="postgresql")
            except Exception as e:
                logger.warning(f"PostgreSQL context service unavailable: {e}")
                _context_service = False  # Mark as unavailable
        else:
            _context_service = False  # Disabled in lite mode
    return _context_service if _context_service else None


# =============================================================================
# MODELS
# =============================================================================

class WebSessionResponse(BaseModel):
    """Response containing session info."""
    session_id: str
    expires_at: datetime
    language: str = "en"


class LocationData(BaseModel):
    """User's geographic location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None  # Accuracy in meters
    address: Optional[str] = None  # Reverse-geocoded address


class WebChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=32, max_length=64)
    language: Optional[str] = None
    location: Optional[LocationData] = None  # User's location if shared


class WebChatMessage(BaseModel):
    """A single chat message."""
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    language: str = "en"
    media_url: Optional[str] = None  # For image responses
    intent: Optional[str] = None  # Detected intent (pnr_status, weather, etc.)
    structured_data: Optional[Dict[str, Any]] = None  # Structured data for rich UI rendering


class WebChatResponse(BaseModel):
    """Response from chat endpoint."""
    user_message: WebChatMessage
    assistant_message: WebChatMessage
    detected_language: str
    requires_location: bool = False  # True if AI needs user's location to answer


class WebChatHistoryResponse(BaseModel):
    """Chat history response."""
    messages: List[WebChatMessage]
    session_id: str


# =============================================================================
# REDIS-BACKED SESSION STORE
# =============================================================================

# Lazy-loaded Redis session store
_redis_session_store: Optional["SessionStore"] = None


async def get_session_store() -> "SessionStore":
    """Get or create the Redis-backed session store."""
    global _redis_session_store
    if _redis_session_store is None:
        from app.services.redis_store import get_redis_store, SessionStore as RedisSessionStore
        redis_store = await get_redis_store()
        _redis_session_store = RedisSessionStore(redis_store)
    return _redis_session_store


class SessionStoreWrapper:
    """
    Wrapper to provide sync-like interface for Redis session store.
    Used for backward compatibility with existing code patterns.
    """

    def __init__(self, store: "SessionStore"):
        self._store = store

    async def create_session(self, language: str = "en") -> tuple[str, datetime]:
        """Create a new anonymous session."""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        await self._store.create_session(
            session_id=session_id,
            language=language,
            ttl_hours=24,
        )

        return session_id, expires_at

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session if valid and not expired."""
        return await self._store.get_session(session_id)

    async def update_session(self, session_id: str, **kwargs):
        """Update session data."""
        await self._store.update_session(session_id, **kwargs)

    async def delete_session(self, session_id: str):
        """Delete session and its messages."""
        await self._store.delete_session(session_id)

    async def add_message(self, session_id: str, message: WebChatMessage):
        """Add message to session history."""
        message_dict = {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "language": message.language,
            "media_url": message.media_url,
            "intent": message.intent,
            "structured_data": message.structured_data,
        }
        await self._store.add_message(session_id, message_dict)

    async def get_messages(self, session_id: str, limit: int = 50) -> List[WebChatMessage]:
        """Get messages for session."""
        messages_data = await self._store.get_messages(session_id, limit=limit)
        result = []
        for msg in messages_data:
            try:
                result.append(WebChatMessage(
                    id=msg["id"],
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]) if isinstance(msg["timestamp"], str) else msg["timestamp"],
                    language=msg.get("language", "en"),
                    media_url=msg.get("media_url"),
                    intent=msg.get("intent"),
                    structured_data=msg.get("structured_data"),
                ))
            except (KeyError, ValueError) as e:
                logger.warning("session_message_parse_error", error=str(e))
                continue
        return result

    async def increment_message_count(self, session_id: str):
        """Increment message count for rate limiting."""
        await self._store.increment_message_count(session_id)

    async def get_message_count(self, session_id: str) -> int:
        """Get message count for session."""
        return await self._store.get_message_count(session_id)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/session", response_model=WebSessionResponse)
async def create_session(
    request: Request,
    response: Response,
) -> WebSessionResponse:
    """
    Create a new anonymous chat session.

    Returns a session ID that must be included in subsequent chat requests.
    Sessions expire after 24 hours.

    Persistence:
    - Redis: For fast access and rate limiting
    - PostgreSQL: For long-term history (when available)
    """
    redis_store = await get_session_store()
    store = SessionStoreWrapper(redis_store)

    # Get preferred language from header or default to English
    accept_language = request.headers.get("Accept-Language", "en")
    language = accept_language.split(",")[0].split("-")[0].lower()

    session_id, expires_at = await store.create_session(language=language)

    # Also create PostgreSQL session for long-term persistence
    context_svc = await get_context_service()
    if context_svc:
        try:
            await context_svc.create_web_session(
                session_token=session_id,
                language=language,
                ttl_hours=24,
            )
            logger.info(
                "web_session_created",
                session_id=session_id[:8],
                persistence="redis+postgresql",
            )
        except Exception as e:
            logger.warning(f"PostgreSQL session creation failed: {e}")
            logger.info(
                "web_session_created",
                session_id=session_id[:8],
                persistence="redis_only",
            )
    else:
        logger.info(
            "web_session_created",
            session_id=session_id[:8],
            persistence="redis_only",
        )

    # Set session cookie for convenience
    response.set_cookie(
        key="web_session",
        value=session_id,
        expires=expires_at,
        httponly=True,
        samesite="lax",
        secure=True,
    )

    return WebSessionResponse(
        session_id=session_id,
        expires_at=expires_at,
        language=language,
    )


@router.get("/session/{session_id}", response_model=WebSessionResponse)
async def get_session(session_id: str) -> WebSessionResponse:
    """
    Get session info and validate it's still active.
    """
    redis_store = await get_session_store()
    store = SessionStoreWrapper(redis_store)
    session = await store.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Parse expires_at from ISO string if needed
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)

    return WebSessionResponse(
        session_id=session_id,
        expires_at=expires_at,
        language=session.get("language", "en"),
    )


@router.post("/chat", response_model=WebChatResponse)
async def send_chat_message(
    request: WebChatRequest,
) -> WebChatResponse:
    """
    Send a chat message and get AI response.

    Rate limited to 50 messages per session per hour.

    Persistence:
    - Redis: Real-time session state and rate limiting
    - PostgreSQL: Durable chat history for long-term context
    """
    redis_store = await get_session_store()
    store = SessionStoreWrapper(redis_store)
    session = await store.get_session(request.session_id)

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # Rate limiting check
    message_count = await store.get_message_count(request.session_id)
    if message_count >= 50:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later or create a new session."
        )

    # Detect language from message
    detected_lang = request.language or detect_language(request.message)
    await store.update_session(request.session_id, language=detected_lang)

    # Get context service for PostgreSQL persistence
    context_svc = await get_context_service()

    # Create user message
    user_msg = WebChatMessage(
        id=str(uuid.uuid4()),
        role="user",
        content=request.message,
        timestamp=datetime.now(timezone.utc),
        language=detected_lang,
    )
    await store.add_message(request.session_id, user_msg)

    # Persist user message to PostgreSQL
    detected_intent = None
    if context_svc:
        try:
            await context_svc.add_message(
                session_token=request.session_id,
                role="user",
                content=request.message,
                language=detected_lang,
            )
        except Exception as e:
            logger.warning(f"PostgreSQL message persist failed: {e}")

    # Process through LangGraph workflow
    assistant_media_url = None
    structured_data = None
    try:
        from app.graph.whatsapp_graph import process_whatsapp_message
        from app.graph.state import message_from_web, UserLocation

        # Convert location if provided
        user_location = None
        if request.location:
            user_location = UserLocation(
                latitude=request.location.latitude,
                longitude=request.location.longitude,
                accuracy=request.location.accuracy,
                address=request.location.address,
            )

        # Convert to internal message format
        internal_msg = message_from_web(
            text=request.message,
            session_id=request.session_id,
            location=user_location,
        )

        # Process through workflow (async)
        result = await process_whatsapp_message(internal_msg)

        assistant_content = result.get("response_text", "I apologize, but I couldn't process your request.")
        assistant_media_url = result.get("response_media_url")
        detected_intent = result.get("intent")
        # Extract structured data from tool_result for rich UI rendering
        tool_result = result.get("tool_result") or {}
        structured_data = tool_result.get("data") if tool_result.get("success") else None

    except ImportError as e:
        logger.error(f"web_chat_import_error: {e}, session_id={request.session_id[:8]}")
        assistant_content = "Service configuration error. Please contact support."
    except ConnectionError as e:
        logger.error(f"web_chat_connection_error: {e}, session_id={request.session_id[:8]}")
        assistant_content = "Connection error. Please try again in a moment."
    except TimeoutError as e:
        logger.error(f"web_chat_timeout: {e}, session_id={request.session_id[:8]}")
        assistant_content = "Request timed out. Please try again."
    except Exception as e:
        logger.error(f"web_chat_error: {type(e).__name__}: {e}, session_id={request.session_id[:8]}")
        assistant_content = "I apologize, but I encountered an error processing your request. Please try again."

    # Create assistant message
    assistant_msg = WebChatMessage(
        id=str(uuid.uuid4()),
        role="assistant",
        content=assistant_content,
        timestamp=datetime.now(timezone.utc),
        language=detected_lang,
        media_url=assistant_media_url,
        intent=detected_intent,
        structured_data=structured_data,
    )
    await store.add_message(request.session_id, assistant_msg)

    # Persist assistant message to PostgreSQL
    if context_svc:
        try:
            await context_svc.add_message(
                session_token=request.session_id,
                role="assistant",
                content=assistant_content,
                language=detected_lang,
                intent=detected_intent,
                media_url=assistant_media_url,
                metadata={"structured_data": structured_data} if structured_data else None,
            )
        except Exception as e:
            logger.warning(f"PostgreSQL assistant message persist failed: {e}")

    # Increment message count for rate limiting
    await store.increment_message_count(request.session_id)

    # Detect if location is required based on response content or intent
    location_keywords = [
        "location", "where are you", "your location", "current location",
        "share your location", "provide your location", "nearby", "near you",
        "closest", "nearest", "around you"
    ]
    requires_location = (
        not request.location and  # Only ask if location not already provided
        detected_intent == "local_search" or
        any(kw in assistant_content.lower() for kw in location_keywords)
    )

    logger.info(
        "web_chat_response",
        session_id=request.session_id[:8],
        language=detected_lang,
        message_count=message_count + 1,
        intent=detected_intent,
        requires_location=requires_location,
    )

    return WebChatResponse(
        user_message=user_msg,
        assistant_message=assistant_msg,
        detected_language=detected_lang,
        requires_location=requires_location,
    )


@router.get("/chat/history/{session_id}", response_model=WebChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    limit: int = 50,
) -> WebChatHistoryResponse:
    """
    Get chat history for a session.

    Retrieval priority:
    1. PostgreSQL (durable, long-term)
    2. Redis (fallback, volatile)
    """
    redis_store = await get_session_store()
    store = SessionStoreWrapper(redis_store)
    session = await store.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    messages = []
    source = "redis"

    # Try PostgreSQL first for durable history
    context_svc = await get_context_service()
    if context_svc:
        try:
            pg_messages = await context_svc.get_messages(session_id, limit=min(limit, 100))
            if pg_messages:
                messages = [
                    WebChatMessage(
                        id=str(msg.id),
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.created_at,
                        language=msg.language,
                        media_url=msg.media_url,
                        intent=msg.intent,
                        structured_data=msg.message_metadata.get("structured_data") if msg.message_metadata else None,
                    )
                    for msg in pg_messages
                ]
                source = "postgresql"
        except Exception as e:
            logger.warning(f"PostgreSQL history fetch failed: {e}")

    # Fallback to Redis
    if not messages:
        messages = await store.get_messages(session_id, limit=min(limit, 100))
        source = "redis"

    logger.debug(
        "web_chat_history_fetched",
        session_id=session_id[:8],
        message_count=len(messages),
        source=source,
    )

    return WebChatHistoryResponse(
        messages=messages,
        session_id=session_id,
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str) -> dict:
    """
    Delete a session and its chat history from both Redis and PostgreSQL.
    """
    redis_store = await get_session_store()
    store = SessionStoreWrapper(redis_store)
    session = await store.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete from Redis
    await store.delete_session(session_id)

    # Also delete from PostgreSQL
    context_svc = await get_context_service()
    if context_svc:
        try:
            await context_svc.delete_web_session(session_id)
            logger.info(
                "web_session_deleted",
                session_id=session_id[:8],
                persistence="redis+postgresql",
            )
        except Exception as e:
            logger.warning(f"PostgreSQL session deletion failed: {e}")
            logger.info(
                "web_session_deleted",
                session_id=session_id[:8],
                persistence="redis_only",
            )
    else:
        logger.info(
            "web_session_deleted",
            session_id=session_id[:8],
            persistence="redis_only",
        )

    return {"message": "Session deleted"}


# ============================================================================
# PUBLIC TOOLS AND PROVIDERS (No Authentication Required)
# ============================================================================


class PublicToolInfo(BaseModel):
    """Tool information for anonymous users."""
    name: str
    description: str
    category: Optional[str] = None


class PublicProviderInfo(BaseModel):
    """Provider information for anonymous users."""
    id: str
    name: str
    display_name: str
    auth_type: str = "oauth"  # oauth, api_key, none
    description: Optional[str] = None
    icon_name: Optional[str] = None
    is_connected: bool = False  # Always false for anonymous users


@router.get("/tools", response_model=List[PublicToolInfo])
async def list_public_tools() -> List[PublicToolInfo]:
    """
    List available tools for anonymous users.

    Returns the list of tools the AI assistant can use.
    No authentication required.
    """
    settings = get_settings()

    try:
        from app.graph.tool_agent import build_tool_agent

        # Build agent without user credentials (public tools only)
        agent = build_tool_agent(settings, credentials={})
        tools = agent.list_tools()

        return [
            PublicToolInfo(
                name=t.get("name", ""),
                description=t.get("description", ""),
                category=t.get("category"),
            )
            for t in tools
        ]
    except Exception as e:
        logger.error(f"Failed to list public tools: {e}")
        # Return a basic list of known tools as fallback
        return [
            PublicToolInfo(name="weather", description="Get current weather for a city", category="utility"),
            PublicToolInfo(name="horoscope", description="Get daily horoscope for zodiac signs", category="astrology"),
            PublicToolInfo(name="numerology", description="Get numerology analysis", category="astrology"),
            PublicToolInfo(name="panchang", description="Get Hindu calendar information", category="astrology"),
            PublicToolInfo(name="tarot", description="Get tarot card readings", category="astrology"),
            PublicToolInfo(name="news", description="Get latest news headlines", category="utility"),
            PublicToolInfo(name="image", description="Generate AI images from text", category="utility"),
        ]


@router.get("/providers", response_model=List[PublicProviderInfo])
async def list_public_providers() -> List[PublicProviderInfo]:
    """
    List available providers/integrations for anonymous users.

    Shows what integrations are available but all marked as not connected.
    Users need to sign in to connect providers.
    """
    # Return list of available providers (none connected for anonymous users)
    return [
        PublicProviderInfo(
            id="github",
            name="github",
            display_name="GitHub",
            auth_type="oauth",
            description="Access GitHub repositories and issues",
            icon_name="github",
            is_connected=False,
        ),
        PublicProviderInfo(
            id="jira",
            name="jira",
            display_name="Jira",
            auth_type="oauth",
            description="Access Jira projects and issues",
            icon_name="jira",
            is_connected=False,
        ),
        PublicProviderInfo(
            id="slack",
            name="slack",
            display_name="Slack",
            auth_type="oauth",
            description="Send messages to Slack channels",
            icon_name="slack",
            is_connected=False,
        ),
        PublicProviderInfo(
            id="notion",
            name="notion",
            display_name="Notion",
            auth_type="oauth",
            description="Access Notion pages and databases",
            icon_name="notion",
            is_connected=False,
        ),
        PublicProviderInfo(
            id="google_calendar",
            name="google_calendar",
            display_name="Google Calendar",
            auth_type="oauth",
            description="Manage calendar events",
            icon_name="calendar",
            is_connected=False,
        ),
    ]


# =============================================================================
# VOICE TRANSCRIPTION
# =============================================================================

class TranscriptionResponse(BaseModel):
    """Response from audio transcription."""
    text: str
    language: str = "en"
    confidence: Optional[float] = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
) -> TranscriptionResponse:
    """
    Transcribe audio to text.

    Accepts audio file (webm, wav, mp3) and returns transcribed text.
    Uses Whisper API or similar for transcription.
    """
    try:
        # Read audio content
        audio_content = await audio.read()

        # Check file size (max 25MB)
        if len(audio_content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio file too large (max 25MB)")

        settings = get_settings()

        # Try OpenAI Whisper API if available
        if settings.openai_api_key:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)

            # Create a temporary file-like object
            import io
            audio_file = io.BytesIO(audio_content)
            audio_file.name = audio.filename or "recording.webm"

            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",
            )

            return TranscriptionResponse(
                text=transcription.text,
                language="en",
            )

        # Fallback: Return empty if no transcription service available
        logger.warning("No transcription service available")
        raise HTTPException(
            status_code=503,
            detail="Transcription service not configured"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")
