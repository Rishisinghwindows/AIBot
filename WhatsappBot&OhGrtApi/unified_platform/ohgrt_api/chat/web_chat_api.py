"""
D23Web Chat API Wrapper

Provides web-specific chat processing using the common chat processor.
Handles web session management, location processing, and response formatting.
"""

import logging
from typing import Any, Dict, List, Optional

from common.services.chat_processor import get_chat_processor, CommonChatProcessor

logger = logging.getLogger(__name__)


class WebChatAPI:
    """
    Web-specific chat API wrapper for D23Web.

    Uses the common chat processor for intent detection and routing,
    but adds web-specific features like:
    - Session-based user identification
    - Location processing from browser geolocation
    - Rich structured data for frontend UI rendering
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize Web chat API.

        Args:
            openai_api_key: OpenAI API key (uses settings if not provided)
            model: Default model to use
        """
        self._processor = get_chat_processor(openai_api_key)

    async def process_message(
        self,
        message: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
        location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Process a web chat message.

        Args:
            message: User's message text
            session_id: Web session ID
            conversation_history: Previous messages
            context: Additional context (user info, etc.)
            location: User's location from browser {latitude, longitude, accuracy, address}

        Returns:
            Response dictionary for web frontend:
                - response: str - The response text
                - intent: str - Detected intent
                - structured_data: dict - Structured data for rich UI rendering
                - needs_location: bool - True if location is needed
                - response_type: str - "text", "location_request", "image", etc.
                - media_url: Optional[str] - URL for media content (images, etc.)
        """
        # Process location if provided (convert from web format)
        location_dict = None
        if location:
            location_dict = {
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
            }

        result = await self._processor.process_message(
            message=message,
            user_id=session_id,
            conversation_history=conversation_history,
            context=context,
            location=location_dict,
            platform="web",
        )

        return self._format_web_response(result)

    def _format_web_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the common processor result for web frontend.

        Args:
            result: Result from common chat processor

        Returns:
            Web-formatted response
        """
        return {
            "response": result.get("response", ""),
            "intent": result.get("intent", "unknown"),
            "structured_data": result.get("structured_data"),
            "needs_location": result.get("needs_location", False),
            "response_type": result.get("response_type", "text"),
            "media_url": result.get("media_url"),
            "route_log": result.get("route_log", []),
            "error": result.get("error"),
        }

    async def process_with_location(
        self,
        session_id: str,
        latitude: float,
        longitude: float,
        pending_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a location share from user (browser geolocation).

        Args:
            session_id: Web session ID
            latitude: User's latitude
            longitude: User's longitude
            pending_query: Original query that triggered location request

        Returns:
            Web-formatted response
        """
        result = await self._processor.process_with_location(
            user_id=session_id,
            latitude=latitude,
            longitude=longitude,
            pending_query=pending_query,
            platform="web",
        )

        return self._format_web_response(result)


# Module-level singleton
_web_chat_api: Optional[WebChatAPI] = None


def get_web_chat_api(api_key: Optional[str] = None) -> WebChatAPI:
    """Get or create Web chat API singleton."""
    global _web_chat_api
    if _web_chat_api is None:
        _web_chat_api = WebChatAPI(openai_api_key=api_key)
    return _web_chat_api


async def process_web_message(
    message: str,
    session_id: str,
    language: Optional[str] = None,
    location: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Main entry point for processing D23Web chat messages.

    This is the simplified interface for the web chat router.

    Args:
        message: User's message text
        session_id: Web session ID
        language: Detected/preferred language
        location: User's location from browser geolocation
        conversation_history: Previous messages in the conversation

    Returns:
        Response dictionary with:
            - response_text: str - The response text
            - response_type: str - "text", "location_request", etc.
            - intent: str - Detected intent
            - structured_data: dict - For rich UI rendering
            - needs_location: bool - True if location is needed
            - media_url: Optional[str] - For image/media responses
    """
    api = get_web_chat_api()

    context = {
        "language": language,
    }

    try:
        result = await api.process_message(
            message=message,
            session_id=session_id,
            conversation_history=conversation_history,
            context=context,
            location=location,
        )

        return {
            "response_text": result.get("response", ""),
            "response_type": result.get("response_type", "text"),
            "intent": result.get("intent", "unknown"),
            "structured_data": result.get("structured_data"),
            "needs_location": result.get("needs_location", False),
            "media_url": result.get("media_url"),
            "error": result.get("error"),
        }

    except Exception as e:
        logger.error(f"Web message processing error: {e}", exc_info=True)
        return {
            "response_text": (
                "I'm having trouble processing your request right now. "
                "Please try again in a moment."
            ),
            "response_type": "text",
            "intent": "error",
            "structured_data": None,
            "needs_location": False,
            "media_url": None,
            "error": str(e),
        }
