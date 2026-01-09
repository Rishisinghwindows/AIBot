"""
Common Chat Processor

Unified chat processing service that can be used by both WhatsApp Bot and D23Web.
Uses smart AI-powered intent detection and routes to common tool handlers.
"""

import asyncio
import inspect
import logging
from typing import Any, Dict, List, Optional

from common.graph.state import BotState
from common.graph.nodes.intent import detect_intent
from common.graph.nodes.chat import handle_chat, handle_fallback
from common.graph.nodes.weather import handle_weather
from common.graph.nodes.news import handle_news
from common.config.settings import settings
from common.i18n.detector import detect_language

# AI Language Service (optional)
try:
    from common.services.ai_language_service import ai_understand_message, ai_translate_response
    AI_LANGUAGE_AVAILABLE = True
except ImportError:
    ai_understand_message = None
    ai_translate_response = None
    AI_LANGUAGE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Import optional handlers
try:
    from common.graph.nodes.food_node import handle_food
    FOOD_AVAILABLE = True
except ImportError:
    handle_food = None
    FOOD_AVAILABLE = False

try:
    from common.graph.nodes.event_node import handle_events as handle_event
    EVENT_AVAILABLE = True
except ImportError:
    handle_event = None
    EVENT_AVAILABLE = False

try:
    from common.graph.nodes.local_search import handle_local_search
    LOCAL_SEARCH_AVAILABLE = True
except ImportError:
    handle_local_search = None
    LOCAL_SEARCH_AVAILABLE = False

try:
    from common.graph.nodes.astro_node import handle_horoscope
    HOROSCOPE_AVAILABLE = True
except ImportError:
    handle_horoscope = None
    HOROSCOPE_AVAILABLE = False

try:
    from common.graph.nodes.pnr_status import handle_pnr_status
    PNR_AVAILABLE = True
except ImportError:
    handle_pnr_status = None
    PNR_AVAILABLE = False

try:
    from common.graph.nodes.train_status import handle_train_status
    TRAIN_AVAILABLE = True
except ImportError:
    handle_train_status = None
    TRAIN_AVAILABLE = False

try:
    from common.graph.nodes.image_gen import handle_image_generation
    IMAGE_GEN_AVAILABLE = True
except ImportError:
    handle_image_generation = None
    IMAGE_GEN_AVAILABLE = False

# Check if fal.ai is properly configured
try:
    from common.config.settings import settings as common_settings
    FAL_CONFIGURED = bool(common_settings.FAL_KEY)
except Exception:
    FAL_CONFIGURED = False


class CommonChatProcessor:
    """
    Unified chat processor that uses common AI-powered intent detection
    and routes to appropriate handlers.

    Can be used by both WhatsApp Bot and D23Web Chat APIs.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize chat processor.

        Args:
            openai_api_key: OpenAI API key (uses settings if not provided)
            model: Default model to use
        """
        self.api_key = openai_api_key
        self.model = model

        # Log available handlers
        handlers = []
        if FOOD_AVAILABLE:
            handlers.append("food")
        if EVENT_AVAILABLE:
            handlers.append("events")
        if LOCAL_SEARCH_AVAILABLE:
            handlers.append("local_search")
        if HOROSCOPE_AVAILABLE:
            handlers.append("horoscope")
        if PNR_AVAILABLE:
            handlers.append("pnr")
        if TRAIN_AVAILABLE:
            handlers.append("train")
        if IMAGE_GEN_AVAILABLE:
            handlers.append("image")

        logger.info(f"CommonChatProcessor initialized with handlers: {handlers}")

    async def _detect_language(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Detect user language with AI when available, fallback to rule-based.
        """
        if context and context.get("user_language"):
            return context["user_language"]

        if not message:
            return "en"

        if AI_LANGUAGE_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                ai_result = await ai_understand_message(
                    message,
                    openai_api_key=settings.OPENAI_API_KEY,
                )
                return ai_result.get("detected_language", "en")
            except Exception as e:
                logger.warning(f"AI language detection failed, falling back: {e}")

        return detect_language(message)

    async def _translate_response(self, text: str, target_lang: str) -> str:
        """
        Translate response text to target language using AI when available.
        """
        if not text or target_lang == "en":
            return text

        if AI_LANGUAGE_AVAILABLE and settings.OPENAI_API_KEY and ai_translate_response:
            try:
                return await ai_translate_response(
                    text=text,
                    target_language=target_lang,
                    openai_api_key=settings.OPENAI_API_KEY,
                )
            except Exception as e:
                logger.warning(f"AI translation failed, returning original: {e}")

        return text

    async def process_message(
        self,
        message: str,
        user_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
        location: Optional[Dict[str, float]] = None,
        platform: str = "web",  # "web" or "whatsapp"
    ) -> Dict[str, Any]:
        """
        Process a chat message with smart AI-powered intent detection.

        Args:
            message: User's message
            user_id: User ID (phone number for WhatsApp, session_id for web)
            conversation_history: Previous messages
            context: Additional context
            location: User's location {latitude, longitude} if provided
            platform: Platform identifier ("web" or "whatsapp")

        Returns:
            Response dictionary with:
                - response: str - The response text
                - intent: str - Detected intent
                - structured_data: Optional dict - Structured data for rich UI
                - needs_location: bool - True if location is needed
                - response_type: str - "text", "location_request", "image", etc.
                - route_log: list - Processing route log
        """
        # Create state for processing
        detected_language = await self._detect_language(message, context=context)
        state: BotState = {
            "current_query": message,
            "whatsapp_message": {
                "text": message,
                "from_number": user_id,
                "message_type": "location" if location else "text",
                "location": location,
            },
            "conversation_history": conversation_history or [],
            "metadata": {
                **(context or {}),
                "platform": platform,
            },
            "detected_language": detected_language,
        }

        # Detect intent using AI-powered detection
        try:
            intent_result = await detect_intent(state)
            state.update(intent_result)
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            state["intent"] = "chat"
            state["intent_confidence"] = 0.5
            state["extracted_entities"] = {}

        intent = state.get("intent", "chat")
        entities = state.get("extracted_entities", {})
        logger.info(f"Detected intent: {intent} for user {user_id}, entities: {entities}")

        # Route to appropriate handler
        try:
            result = await self._route_to_handler(intent, state)

            response_type = result.get("response_type", "text")
            response_text = result.get("response_text", "")
            if response_type in ["text", "location_request"] and response_text:
                response_text = await self._translate_response(response_text, detected_language)

            return {
                "response": response_text,
                "intent": result.get("intent", intent),
                "structured_data": result.get("tool_result") or result.get("structured_data"),
                "needs_location": response_type == "location_request",
                "response_type": response_type,
                "route_log": result.get("route_log", []),
                "media_url": result.get("response_media_url"),
            }

        except Exception as e:
            logger.error(f"Chat processing error: {e}", exc_info=True)
            return {
                "response": "I'm having trouble processing your request. Please try again.",
                "intent": "error",
                "error": str(e),
                "response_type": "text",
            }

    async def _route_to_handler(self, intent: str, state: BotState) -> Dict[str, Any]:
        """Route to the appropriate handler based on intent."""

        async def call_handler(handler, state):
            """Call handler, awaiting if it's async."""
            if asyncio.iscoroutinefunction(handler):
                return await handler(state)
            else:
                return handler(state)

        # Weather
        if intent == "weather":
            return await call_handler(handle_weather, state)

        # Food/Restaurant
        elif intent in ["food_order", "food"] and FOOD_AVAILABLE:
            return await call_handler(handle_food, state)

        # Events
        elif intent in ["events", "event"] and EVENT_AVAILABLE:
            return await call_handler(handle_event, state)

        # Local Search (hospitals, ATMs, plumbers, etc.)
        elif intent == "local_search" and LOCAL_SEARCH_AVAILABLE:
            return await call_handler(handle_local_search, state)

        # News
        elif intent in ["get_news", "news"]:
            return await call_handler(handle_news, state)

        # Horoscope
        elif intent in ["get_horoscope", "horoscope"] and HOROSCOPE_AVAILABLE:
            return await call_handler(handle_horoscope, state)

        # PNR Status
        elif intent == "pnr_status" and PNR_AVAILABLE:
            return await call_handler(handle_pnr_status, state)

        # Train Status
        elif intent == "train_status" and TRAIN_AVAILABLE:
            return await call_handler(handle_train_status, state)

        # Image Generation
        elif intent == "image":
            if IMAGE_GEN_AVAILABLE and FAL_CONFIGURED:
                return await call_handler(handle_image_generation, state)
            else:
                # Return helpful message when image generation isn't available
                return {
                    "response_text": (
                        "Image generation is currently being set up. "
                        "Please try again later or sign in to access full features."
                    ),
                    "response_type": "text",
                    "intent": "image",
                    "should_fallback": False,
                }

        # Default to chat
        else:
            return await call_handler(handle_chat, state)

    async def process_with_location(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        pending_query: Optional[str] = None,
        platform: str = "web",
    ) -> Dict[str, Any]:
        """
        Process a location response from user.

        Args:
            user_id: User ID
            latitude: User's latitude
            longitude: User's longitude
            pending_query: The original query that triggered location request
            platform: Platform identifier ("web" or "whatsapp")

        Returns:
            Response dictionary
        """
        location = {"latitude": latitude, "longitude": longitude}

        # Use the pending query or a default
        message = pending_query or "Show results for my location"

        return await self.process_message(
            message=message,
            user_id=user_id,
            location=location,
            platform=platform,
        )


# Module-level singleton
_chat_processor: Optional[CommonChatProcessor] = None


def get_chat_processor(api_key: Optional[str] = None) -> CommonChatProcessor:
    """Get or create chat processor singleton."""
    global _chat_processor
    if _chat_processor is None:
        from common.config.settings import settings
        _chat_processor = CommonChatProcessor(
            openai_api_key=api_key or settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )
    return _chat_processor
