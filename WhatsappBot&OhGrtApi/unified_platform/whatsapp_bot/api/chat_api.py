"""
WhatsApp Bot Chat API Wrapper

Provides WhatsApp-specific chat processing using the common chat processor.
Handles WhatsApp message formats, location buttons, and response formatting.
"""

import logging
from typing import Any, Dict, List, Optional

from common.services.chat_processor import get_chat_processor, CommonChatProcessor
from common.graph.state import BotState
from whatsapp_bot.stores.pending_location_store import get_pending_location_store

logger = logging.getLogger(__name__)


class WhatsAppChatAPI:
    """
    WhatsApp-specific chat API wrapper.

    Uses the common chat processor for intent detection and routing,
    but adds WhatsApp-specific features like:
    - Location request buttons
    - Interactive message formatting
    - Pending location store integration
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize WhatsApp chat API.

        Args:
            openai_api_key: OpenAI API key (uses settings if not provided)
            model: Default model to use
        """
        self._processor = get_chat_processor(openai_api_key)
        self._pending_store = get_pending_location_store()

    async def process_message(
        self,
        message: str,
        phone_number: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
        location: Optional[Dict[str, float]] = None,
        message_type: str = "text",
    ) -> Dict[str, Any]:
        """
        Process a WhatsApp message.

        Args:
            message: User's message text
            phone_number: User's WhatsApp phone number
            conversation_history: Previous messages
            context: Additional context (user_name, etc.)
            location: User's location if shared {latitude, longitude}
            message_type: Type of message ("text", "location", "image", etc.)

        Returns:
            Response dictionary with WhatsApp-specific formatting:
                - response_text: str - The response text
                - response_type: str - "text", "location_request", "interactive", etc.
                - intent: str - Detected intent
                - buttons: list - Interactive buttons if any
                - structured_data: dict - Structured data for UI
                - needs_location: bool - True if location button should be shown
        """
        # Check if this is a location message responding to a pending request
        if message_type == "location" and location:
            pending = await self._pending_store.get_pending_search(phone_number)
            if pending:
                # Process with location
                result = await self._processor.process_with_location(
                    user_id=phone_number,
                    latitude=location["latitude"],
                    longitude=location["longitude"],
                    pending_query=pending.get("original_message") or pending.get("search_query"),
                    platform="whatsapp",
                )
                return self._format_whatsapp_response(result, phone_number)

        # Regular message processing
        result = await self._processor.process_message(
            message=message,
            user_id=phone_number,
            conversation_history=conversation_history,
            context=context,
            location=location,
            platform="whatsapp",
        )

        return self._format_whatsapp_response(result, phone_number)

    def _format_whatsapp_response(
        self,
        result: Dict[str, Any],
        phone_number: str,
    ) -> Dict[str, Any]:
        """
        Format the common processor result for WhatsApp.

        Args:
            result: Result from common chat processor
            phone_number: User's phone number

        Returns:
            WhatsApp-formatted response
        """
        response_type = result.get("response_type", "text")
        needs_location = result.get("needs_location", False)

        # Build buttons if needed
        buttons = None
        if response_type == "location_request" or needs_location:
            buttons = [
                {
                    "type": "location_request_message",
                    "body": {"text": "📍 Share your location to continue"},
                }
            ]

        return {
            "response_text": result.get("response", ""),
            "response_type": response_type,
            "intent": result.get("intent", "unknown"),
            "structured_data": result.get("structured_data"),
            "buttons": buttons,
            "needs_location": needs_location or response_type == "location_request",
            "response_media_url": result.get("media_url"),
            "tool_result": result.get("structured_data"),
            "error": result.get("error"),
        }

    async def process_with_location(
        self,
        phone_number: str,
        latitude: float,
        longitude: float,
        pending_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a location share from user.

        Args:
            phone_number: User's phone number
            latitude: User's latitude
            longitude: User's longitude
            pending_query: Original query that triggered location request

        Returns:
            WhatsApp-formatted response
        """
        result = await self._processor.process_with_location(
            user_id=phone_number,
            latitude=latitude,
            longitude=longitude,
            pending_query=pending_query,
            platform="whatsapp",
        )

        return self._format_whatsapp_response(result, phone_number)


# Module-level singleton
_whatsapp_chat_api: Optional[WhatsAppChatAPI] = None


def get_whatsapp_chat_api(api_key: Optional[str] = None) -> WhatsAppChatAPI:
    """Get or create WhatsApp chat API singleton."""
    global _whatsapp_chat_api
    if _whatsapp_chat_api is None:
        _whatsapp_chat_api = WhatsAppChatAPI(openai_api_key=api_key)
    return _whatsapp_chat_api


async def process_whatsapp_message(
    whatsapp_message: Dict[str, Any],
    user_id: Optional[str] = None,
    user_birth_details: Optional[Dict] = None,
    user_language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point for processing WhatsApp messages.

    Compatible with the existing ohgrt_api/graph/whatsapp_graph.py interface.

    Args:
        whatsapp_message: WhatsApp message dictionary with keys:
            - message_id: str
            - from_number: str
            - phone_number_id: str
            - timestamp: str
            - message_type: str
            - text: Optional[str]
            - location: Optional[dict] with latitude, longitude
            - media_id: Optional[str]
            - user_name: Optional[str]
        user_id: Optional user ID from database
        user_birth_details: Optional birth details for astrology
        user_language: Optional preferred language

    Returns:
        Response dictionary with:
            - response_text: str
            - response_type: str
            - response_media_url: Optional[str]
            - buttons: Optional[list]
            - intent: str
            - error: Optional[str]
            - tool_result: Optional[dict]
    """
    api = get_whatsapp_chat_api()

    phone_number = whatsapp_message.get("from_number", "")
    message = whatsapp_message.get("text", "")
    message_type = whatsapp_message.get("message_type", "text")
    location = whatsapp_message.get("location")

    context = {
        "user_id": user_id,
        "user_name": whatsapp_message.get("user_name"),
        "user_birth_details": user_birth_details,
        "user_language": user_language,
        "message_id": whatsapp_message.get("message_id"),
        "phone_number_id": whatsapp_message.get("phone_number_id"),
    }

    try:
        result = await api.process_message(
            message=message,
            phone_number=phone_number,
            context=context,
            location=location,
            message_type=message_type,
        )

        return {
            "response_text": result.get("response_text", ""),
            "response_type": result.get("response_type", "text"),
            "response_media_url": result.get("response_media_url"),
            "buttons": result.get("buttons"),
            "intent": result.get("intent", "unknown"),
            "error": result.get("error"),
            "tool_result": result.get("tool_result"),
        }

    except Exception as e:
        logger.error(f"WhatsApp message processing error: {e}", exc_info=True)
        return {
            "response_text": (
                "I'm having trouble processing your message right now.\n\n"
                "Please try again in a moment, or try one of these:\n"
                "- Weather: 'Weather in Delhi'\n"
                "- Horoscope: 'Aries horoscope'\n"
                "- Search: 'Restaurants near me'"
            ),
            "response_type": "text",
            "response_media_url": None,
            "buttons": None,
            "intent": "error",
            "error": str(e),
            "tool_result": None,
        }
