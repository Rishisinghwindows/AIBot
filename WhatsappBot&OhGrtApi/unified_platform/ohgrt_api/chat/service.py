"""
Chat Service.

Provides chat functionality using smart AI-powered intent detection.
Routes to appropriate handlers for weather, food, events, local search, etc.
"""

import logging
from typing import Any, Dict, List, Optional

from common.graph.state import BotState, create_initial_state
from common.graph.nodes.intent import detect_intent
from common.graph.nodes.chat import handle_chat
from common.graph.nodes.weather import handle_weather
from ohgrt_api.graph.nodes.news_node import handle_news
from common.llm.openai_client import get_chat_completion

logger = logging.getLogger(__name__)

# Import optional handlers
try:
    from whatsapp_bot.graph.nodes.food_node import handle_food
    FOOD_AVAILABLE = True
except ImportError:
    handle_food = None
    FOOD_AVAILABLE = False

try:
    from whatsapp_bot.graph.nodes.event_node import handle_event
    EVENT_AVAILABLE = True
except ImportError:
    handle_event = None
    EVENT_AVAILABLE = False

try:
    from whatsapp_bot.graph.nodes.local_search import handle_local_search
    LOCAL_SEARCH_AVAILABLE = True
except ImportError:
    handle_local_search = None
    LOCAL_SEARCH_AVAILABLE = False

try:
    from common.graph.nodes.horoscope import handle_horoscope
    HOROSCOPE_AVAILABLE = True
except ImportError:
    handle_horoscope = None
    HOROSCOPE_AVAILABLE = False

try:
    from whatsapp_bot.graph.nodes.pnr import handle_pnr
    PNR_AVAILABLE = True
except ImportError:
    handle_pnr = None
    PNR_AVAILABLE = False

try:
    from whatsapp_bot.graph.nodes.train import handle_train_status
    TRAIN_AVAILABLE = True
except ImportError:
    handle_train_status = None
    TRAIN_AVAILABLE = False


class ChatService:
    """Service for handling chat requests with smart intent detection."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """
        Initialize chat service.

        Args:
            openai_api_key: OpenAI API key
            model: Default model to use
        """
        self.api_key = openai_api_key
        self.model = model

    async def process_message(
        self,
        message: str,
        user_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
        location: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Process a chat message with smart AI-powered intent detection.

        Args:
            message: User's message
            user_id: User ID
            conversation_history: Previous messages
            context: Additional context
            location: User's location {latitude, longitude} if provided

        Returns:
            Response dictionary with intent, response, and structured_data
        """
        # Create state for web/API context
        state: BotState = {
            "current_query": message,
            "whatsapp_message": {
                "text": message,
                "from_number": user_id,
                "message_type": "location" if location else "text",
                "location": location,
            },
            "conversation_history": conversation_history or [],
            "metadata": context or {},
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

            return {
                "response": result.get("response_text", ""),
                "intent": result.get("intent", intent),
                "structured_data": result.get("tool_result") or result.get("structured_data"),
                "needs_location": result.get("response_type") == "location_request",
                "route_log": result.get("route_log", []),
            }

        except Exception as e:
            logger.error(f"Chat processing error: {e}", exc_info=True)
            return {
                "response": "I'm having trouble processing your request. Please try again.",
                "intent": "error",
                "error": str(e),
            }

    async def _route_to_handler(self, intent: str, state: BotState) -> Dict[str, Any]:
        """Route to the appropriate handler based on intent."""
        from ohgrt_api.config import settings

        # Weather
        if intent == "weather":
            return await handle_weather(state)

        # Food/Restaurant
        elif intent in ["food_order", "food"] and FOOD_AVAILABLE:
            return await handle_food(state)

        # Events
        elif intent in ["events", "event"] and EVENT_AVAILABLE:
            return await handle_event(state)

        # Local Search (hospitals, ATMs, plumbers, etc.)
        elif intent == "local_search" and LOCAL_SEARCH_AVAILABLE:
            return await handle_local_search(state)

        # News
        elif intent == "get_news":
            return await handle_news(state)

        # Horoscope
        elif intent in ["get_horoscope", "horoscope"] and HOROSCOPE_AVAILABLE:
            return await handle_horoscope(state)

        # PNR Status
        elif intent == "pnr_status" and PNR_AVAILABLE:
            return await handle_pnr(state)

        # Train Status
        elif intent == "train_status" and TRAIN_AVAILABLE:
            return await handle_train_status(state)

        # Default to chat
        else:
            return await handle_chat(
                state,
                model=self.model,
                api_key=self.api_key,
            )

    async def process_with_location(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        pending_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a location response from user.

        Args:
            user_id: User ID
            latitude: User's latitude
            longitude: User's longitude
            pending_query: The original query that triggered location request

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
        )

    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get a direct completion from the LLM.

        Args:
            messages: Message history
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            Generated response
        """
        return await get_chat_completion(
            messages=messages,
            model=model or self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
        )


# Module-level service
_chat_service: Optional[ChatService] = None


def get_chat_service(api_key: Optional[str] = None) -> ChatService:
    """Get or create chat service instance."""
    global _chat_service
    if _chat_service is None:
        from ohgrt_api.config import settings
        _chat_service = ChatService(
            openai_api_key=api_key or settings.openai_api_key,
            model=settings.openai_model,
        )
    return _chat_service
