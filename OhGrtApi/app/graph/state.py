"""
LangGraph State Definitions for WhatsApp AI Assistant

Uses TypedDict for type safety and clear state contracts.
"""

from typing import TypedDict, Literal, Optional
from enum import Enum


class ClientType(str, Enum):
    """Client platform types."""
    IOS = "ios"
    WEB = "web"
    WHATSAPP = "whatsapp"


# Intent types supported by the system
IntentType = Literal[
    "local_search",
    "image",
    "pnr_status",
    "train_status",
    "metro_ticket",
    "weather",
    "word_game",
    "db_query",
    "set_reminder",
    "get_news",
    # Astrology intents
    "get_horoscope",
    "birth_chart",
    "kundli_matching",
    "ask_astrologer",
    "numerology",
    "tarot_reading",
    # New Astrology intents (Phase 1)
    "life_prediction",   # Marriage, career, children predictions
    "dosha_check",       # Manglik, Kaal Sarp, Sade Sati
    "get_panchang",      # Daily panchang, tithi, nakshatra
    "get_remedy",        # Gemstones, mantras, pujas
    "find_muhurta",      # Auspicious dates/times
    # Subscription
    "subscription",
    # General
    "chat",
    "unknown",
]


class UserLocation(TypedDict):
    """User's geographic location."""
    latitude: float
    longitude: float
    accuracy: Optional[float]  # Accuracy in meters
    address: Optional[str]  # Reverse-geocoded address


class WhatsAppMessage(TypedDict):
    """Incoming WhatsApp message structure."""
    message_id: str
    from_number: str
    phone_number_id: str
    timestamp: str
    message_type: str
    text: Optional[str]
    media_id: Optional[str]
    user_name: Optional[str]
    location: Optional[UserLocation]  # User's location if shared


class ToolResult(TypedDict):
    """Result from tool execution."""
    success: bool
    data: Optional[dict]
    error: Optional[str]
    tool_name: str


class BotState(TypedDict):
    """
    Main state object for the LangGraph workflow.

    This state is passed between all nodes and represents
    the complete context of a single conversation turn.
    """
    # Client type (ios, web, whatsapp)
    client_type: ClientType

    # Input from WhatsApp (or converted from other clients)
    whatsapp_message: WhatsAppMessage

    # Domain classification (V2 architecture)
    domain: Optional[str]  # astrology, travel, utility, game, conversation

    # Intent classification
    intent: IntentType
    intent_confidence: float
    extracted_entities: dict

    # Astrology-specific intent (for sub-graph)
    astro_intent: Optional[str]

    # Travel-specific intent (for sub-routing)
    travel_intent: Optional[str]

    # Utility-specific intent (for sub-routing)
    utility_intent: Optional[str]

    # Processing state
    current_query: str

    # User context (from database)
    user_id: Optional[str]
    user_birth_details: Optional[dict]
    user_language: Optional[str]

    # Detected language from current message (for response localization)
    detected_language: Optional[str]

    # Conversation context
    conversation_context: Optional[dict]

    # Tool execution results
    tool_result: Optional[ToolResult]

    # Word game state
    word_game: dict

    # Response generation
    response_text: str
    response_media_url: Optional[str]
    response_type: Literal["text", "image", "interactive", "audio"]

    # Interactive buttons (for WhatsApp)
    buttons: Optional[list]

    # Error handling
    error: Optional[str]
    should_fallback: bool


def create_initial_state(
    message: WhatsAppMessage,
    client_type: ClientType = ClientType.WHATSAPP,
    user_id: Optional[str] = None,
    user_birth_details: Optional[dict] = None,
    user_language: Optional[str] = None,
) -> BotState:
    """
    Create initial state for a new message.

    Args:
        message: Incoming message (WhatsApp format)
        client_type: Client platform type
        user_id: User ID from database (for iOS/web users)
        user_birth_details: User's birth details for astrology
        user_language: User's preferred language

    Returns:
        Initialized BotState
    """
    return BotState(
        client_type=client_type,
        whatsapp_message=message,
        domain=None,
        intent="unknown",
        intent_confidence=0.0,
        extracted_entities={},
        astro_intent=None,
        travel_intent=None,
        utility_intent=None,
        current_query=message.get("text", "") or "",
        user_id=user_id,
        user_birth_details=user_birth_details,
        user_language=user_language or "en",
        detected_language="en",  # Will be updated by intent detection
        conversation_context=None,
        tool_result=None,
        word_game={"is_active": False, "correct_word": None},
        response_text="",
        response_media_url=None,
        response_type="text",
        buttons=None,
        error=None,
        should_fallback=False,
    )


def message_from_ios(
    user_id: str,
    text: str,
    conversation_id: Optional[str] = None,
    location: Optional[UserLocation] = None,
) -> WhatsAppMessage:
    """
    Convert iOS app message to WhatsApp format for unified processing.

    Args:
        user_id: iOS user ID
        text: Message text
        conversation_id: iOS conversation ID
        location: Optional user location

    Returns:
        WhatsAppMessage dict
    """
    return WhatsAppMessage(
        message_id=conversation_id or "",
        from_number=user_id,
        phone_number_id="ios_app",
        timestamp="",
        message_type="text",
        text=text,
        media_id=None,
        user_name=None,
        location=location,
    )


def message_from_web(
    session_id: str,
    text: str,
    user_name: Optional[str] = None,
    location: Optional[UserLocation] = None,
) -> WhatsAppMessage:
    """
    Convert web chat message to WhatsApp format for unified processing.

    Args:
        session_id: Web session ID
        text: Message text
        user_name: Optional user name
        location: Optional user location

    Returns:
        WhatsAppMessage dict
    """
    return WhatsAppMessage(
        message_id="",
        from_number=session_id,
        phone_number_id="web_chat",
        timestamp="",
        message_type="text",
        text=text,
        media_id=None,
        user_name=user_name,
        location=location,
    )
