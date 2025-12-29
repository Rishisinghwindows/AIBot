"""
LangGraph State Definitions for WhatsApp AI Assistant

Uses TypedDict for type safety and clear state contracts.
"""

from typing import TypedDict, Literal, Optional, Annotated, Any
from operator import add


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
    # General
    "chat",
    "unknown",
]


class LocationData(TypedDict, total=False):
    """Location data from WhatsApp message."""
    latitude: float
    longitude: float
    name: Optional[str]
    address: Optional[str]


class WhatsAppMessage(TypedDict):
    """Incoming WhatsApp message structure."""

    message_id: str
    from_number: str
    phone_number_id: str
    timestamp: str
    message_type: str
    text: Optional[str]
    media_id: Optional[str]
    location: Optional[LocationData]


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

    # Input from WhatsApp
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

    # Language detection (multi-language support)
    detected_language: str  # Language code: en, hi, bn, ta, te, ml, kn, pa, mr, or

    # Conversation context (WhatsApp-specific)
    conversation_context: Optional[dict]  # use_context, reason, etc.

    # Tool execution results
    tool_result: Optional[ToolResult]

    # Word game state
    word_game: dict

    # Response generation
    response_text: str
    response_media_url: Optional[str]
    response_type: Literal["text", "image", "interactive"]

    # Error handling
    error: Optional[str]
    should_fallback: bool


def create_initial_state(whatsapp_message: WhatsAppMessage) -> BotState:
    """
    Create initial state for a new message.

    Args:
        whatsapp_message: Incoming WhatsApp message

    Returns:
        Initialized BotState
    """
    return BotState(
        whatsapp_message=whatsapp_message,
        domain=None,
        intent="unknown",
        intent_confidence=0.0,
        extracted_entities={},
        astro_intent=None,
        travel_intent=None,
        utility_intent=None,
        current_query=whatsapp_message.get("text", "") or "",
        detected_language="en",  # Default, will be detected in intent node
        conversation_context=None,
        tool_result=None,
        word_game={"is_active": False, "correct_word": None},
        response_text="",
        response_media_url=None,
        response_type="text",
        error=None,
        should_fallback=False,
    )
