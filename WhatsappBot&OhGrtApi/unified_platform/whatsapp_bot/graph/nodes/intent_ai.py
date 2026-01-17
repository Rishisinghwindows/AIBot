"""
AI-First Intent Detection Node

Uses AI to:
1. Detect language
2. Understand intent
3. Extract entities (with normalization to English)

This replaces regex-based pattern matching with AI-first approach.
"""

import logging
from typing import Dict, Any

from whatsapp_bot.state import BotState
from whatsapp_bot.config import settings
from whatsapp_bot.stores.pending_location_store import get_pending_location_store
from common.services.ai_language_service import (
    init_ai_language_service,
    ai_understand_message,
    get_ai_language_service,
)

logger = logging.getLogger(__name__)


# Valid intents
VALID_INTENTS = [
    "local_search",
    "image",
    "pnr_status",
    "train_status",
    "train_journey",
    "metro_ticket",
    "weather",
    "word_game",
    "db_query",
    "set_reminder",
    "get_news",
    "stock_price",
    "fact_check",
    "get_horoscope",
    "birth_chart",
    "kundli_matching",
    "ask_astrologer",
    "numerology",
    "tarot_reading",
    "life_prediction",
    "dosha_check",
    "get_panchang",
    "get_remedy",
    "find_muhurta",
    "events",
    "food_order",
    "help",
    "chat",
]


async def detect_intent_ai(state: BotState) -> dict:
    """
    AI-First Intent Detection.

    Uses GPT-4o-mini to:
    1. Detect language from user message
    2. Understand the intent
    3. Extract entities (normalized to English)

    Args:
        state: Current bot state with WhatsApp message

    Returns:
        Updated state dict with intent, confidence, entities, and detected_language
    """
    whatsapp_message = state.get("whatsapp_message", {})
    user_message = whatsapp_message.get("text", "")
    message_type = whatsapp_message.get("message_type", "text")
    phone = whatsapp_message.get("from_number", "")

    # Initialize AI service if not already done
    if get_ai_language_service() is None:
        init_ai_language_service(
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model
        )

    # Handle location messages (check for pending search)
    if message_type == "location" and whatsapp_message.get("location"):
        pending_store = get_pending_location_store()
        pending = await pending_store.peek_pending_search(phone)
        logger.info(f"Location message from {phone}, pending_search: {pending}")

        if pending:
            search_query = pending.get("search_query", "")

            # Weather location request
            if search_query == "__weather__":
                logger.info("Routing location message to weather")
                return {
                    "intent": "weather",
                    "intent_confidence": 1.0,
                    "extracted_entities": {},
                    "current_query": "",
                    "detected_language": "en",
                    "error": None,
                }

            # Food location request
            if search_query == "__food__":
                logger.info("Routing location message to food_order")
                return {
                    "intent": "food_order",
                    "intent_confidence": 1.0,
                    "extracted_entities": {},
                    "current_query": "restaurants near me",
                    "detected_language": "en",
                    "error": None,
                }

            # Events location request
            if search_query.startswith("__events"):
                logger.info(f"Routing location to events: {search_query}")
                return {
                    "intent": "events",
                    "intent_confidence": 1.0,
                    "extracted_entities": {},
                    "current_query": pending.get("original_message", "events near me"),
                    "detected_language": "en",
                    "error": None,
                }

            # Local search location request
            logger.info("Routing location to local_search")
            return {
                "intent": "local_search",
                "intent_confidence": 1.0,
                "extracted_entities": {},
                "current_query": "",
                "detected_language": "en",
                "error": None,
            }

    # Empty message handling
    if not user_message:
        return {
            "intent": "chat",
            "intent_confidence": 1.0,
            "extracted_entities": {},
            "current_query": "",
            "detected_language": "en",
            "error": None,
        }

    # Use AI to understand the message
    try:
        logger.info(f"AI understanding message: {user_message[:100]}...")

        result = await ai_understand_message(
            message=user_message,
            openai_api_key=settings.openai_api_key
        )

        detected_lang = result.get("detected_language", "en")
        intent = result.get("intent", "chat")
        confidence = result.get("confidence", 0.8)
        entities = result.get("entities", {})
        normalized_query = result.get("normalized_query", user_message)

        # Validate intent
        if intent not in VALID_INTENTS:
            logger.warning(f"AI returned unknown intent: {intent}, defaulting to chat")
            intent = "chat"

        logger.info(f"AI detected: lang={detected_lang}, intent={intent}, conf={confidence}, entities={entities}")

        return {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_entities": entities,
            "current_query": normalized_query or user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    except Exception as e:
        logger.error(f"AI intent detection failed: {e}")
        # Fallback to chat on error
        return {
            "intent": "chat",
            "intent_confidence": 0.5,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": "en",
            "error": f"AI detection error: {str(e)}",
        }
