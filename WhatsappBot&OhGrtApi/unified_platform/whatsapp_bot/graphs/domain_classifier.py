"""
Domain Classifier

First-level routing that classifies user queries into domains:
- astrology: All astrology-related features
- travel: PNR, train status, metro
- utility: Weather, news, search, image, reminders
- game: Word games, quizzes
- conversation: General chat, fallback

This reduces the complexity of intent detection by first
identifying the domain, then routing to domain-specific handlers.

UPDATED: Now uses AI-first approach for multilingual support.
"""

import logging
from typing import Literal
import re

from whatsapp_bot.state import BotState
from whatsapp_bot.config import settings
from bot.stores.pending_location_store import get_pending_location_store

# AI Language Service for multilingual understanding
try:
    from common.services.ai_language_service import (
        ai_understand_message,
        init_ai_language_service,
        get_ai_language_service,
    )
    AI_SERVICE_AVAILABLE = True
except ImportError:
    AI_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)


# Domain type definition
DomainType = Literal[
    "astrology",
    "travel",
    "utility",
    "game",
    "conversation",
]


# Domain keywords for classification
DOMAIN_KEYWORDS = {
    "astrology": [
        # English
        "horoscope", "kundli", "kundali", "birth chart", "janam patri",
        "zodiac", "astrology", "astrologer", "astrological",
        "manglik", "mangal dosha", "kaal sarp", "kaalsarp", "sade sati",
        "dosha", "dosh", "pitra", "pitru",
        "prediction", "predict", "future", "destiny", "fate",
        "marriage prediction", "career prediction", "job prediction",
        "when will i", "will i get",
        "numerology", "lucky number", "name number",
        "tarot", "card reading", "pick a card",
        "panchang", "panchangam", "tithi", "nakshatra",
        "muhurat", "muhurta", "auspicious", "shubh",
        "gemstone", "stone", "ratna", "neelam", "ruby", "emerald",
        "mantra", "remedy", "upay",
        "rahu", "ketu", "saturn", "shani", "jupiter", "guru",
        "dasha", "mahadasha", "antardasha",
        "compatibility", "gun milan", "matching",
        # Hindi
        "rashifal", "rashi", "graha", "grahas",
        "mesh", "vrishabh", "mithun", "kark", "singh", "kanya",
        "tula", "vrishchik", "dhanu", "makar", "kumbh", "meen",
        # Zodiac signs
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ],
    "travel": [
        "pnr", "pnr status", "check pnr",
        "train", "train status", "running status", "live train",
        "train number", "train no",
        "metro", "metro route", "metro fare", "metro ticket",
        "railway", "railways", "irctc",
        "station", "platform",
    ],
    "utility": [
        "weather", "temperature", "forecast", "rain", "sunny",
        "news", "headlines", "latest news", "breaking news",
        # Local search keywords
        "search", "find", "near me", "nearby", "nearest",
        "restaurant", "hospital", "hotel", "atm", "bank", "pharmacy",
        "petrol pump", "gas station", "mall", "shop", "store", "clinic",
        "school", "college", "gym", "park", "temple", "mosque", "church",
        "police station", "airport", "bus stand",
        # Image generation
        "generate image", "create image", "draw", "picture",
        # Reminders
        "remind", "reminder", "alarm", "set reminder",
        # Database queries
        "document", "pdf", "query", "database",
    ],
    "game": [
        "game", "play", "play game", "word game",
        "quiz", "puzzle", "riddle",
        "jumbled", "unscramble",
    ],
}


async def classify_domain(state: BotState) -> dict:
    """
    Classify the user query into a domain using AI-first approach.

    This uses GPT-4o-mini to:
    1. Detect the user's language
    2. Understand the intent
    3. Extract entities (normalized to English)

    Falls back to keyword matching if AI fails.

    Args:
        state: Current bot state with whatsapp_message

    Returns:
        Updated state with domain, intent, entities, and detected_language
    """
    message = state.get("whatsapp_message", {})
    text = message.get("text", "").strip()
    text_lower = text.lower()
    message_type = message.get("message_type", "text")
    phone = message.get("from_number", "")

    # Check if this is a location message with a pending search
    if message_type == "location" and message.get("location"):
        pending_store = get_pending_location_store()
        has_pending = await pending_store.has_pending_search(phone)
        logger.info(f"Location message from {phone}, has_pending_search: {has_pending}")
        if has_pending:
            # Route to utility domain for local_search to handle
            return {
                "domain": "utility",
                "utility_intent": "local_search",
                "current_query": "",
                "detected_language": "en",
            }

    if not text:
        return {
            "domain": "conversation",
            "current_query": "",
            "detected_language": "en",
        }

    # ==========================================================================
    # AI-FIRST APPROACH: Use AI to understand the message
    # ==========================================================================
    if AI_SERVICE_AVAILABLE:
        try:
            # Initialize AI service if not already done
            if get_ai_language_service() is None:
                init_ai_language_service(
                    openai_api_key=settings.openai_api_key,
                    model=settings.openai_model
                )

            # Use AI to understand the message
            logger.info(f"Using AI to understand: {text[:100]}...")
            ai_result = await ai_understand_message(
                message=text,
                openai_api_key=settings.openai_api_key
            )

            detected_lang = ai_result.get("detected_language", "en")
            intent = ai_result.get("intent", "chat")
            entities = ai_result.get("entities", {})
            normalized_query = ai_result.get("normalized_query", text)

            logger.info(f"AI result: lang={detected_lang}, intent={intent}, entities={entities}")

            # Map intent to domain
            domain = get_domain_from_intent(intent)

            # Set utility_intent for weather specifically
            utility_intent = None
            if domain == "utility":
                if intent == "weather":
                    utility_intent = "weather"
                elif intent == "get_news":
                    utility_intent = "news"
                elif intent == "image":
                    utility_intent = "image"
                elif intent == "set_reminder":
                    utility_intent = "reminder"
                elif intent in ["local_search", "food_order"]:
                    utility_intent = "local_search"

            return {
                "domain": domain,
                "intent": intent,
                "extracted_entities": entities,
                "current_query": normalized_query or text,
                "detected_language": detected_lang,
                "utility_intent": utility_intent,
            }

        except Exception as e:
            logger.warning(f"AI classification failed, falling back to keywords: {e}")
            # Fall through to keyword-based classification

    # ==========================================================================
    # FALLBACK: Keyword-based classification (for when AI fails)
    # ==========================================================================
    logger.info("Using keyword-based classification (fallback)")

    # Check each domain's keywords
    domain_scores = {domain: 0 for domain in DOMAIN_KEYWORDS}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Longer keywords get higher scores
                domain_scores[domain] += len(keyword.split())

    # Get domain with highest score
    best_domain = max(domain_scores, key=domain_scores.get)
    best_score = domain_scores[best_domain]

    # If no keywords matched, default to conversation
    if best_score == 0:
        # Check for question patterns that might be astrology
        astro_question_patterns = [
            r"when will i",
            r"will i get",
            r"will i have",
            r"will my",
            r"should i",
            r"is it good",
            r"what is my",
        ]
        for pattern in astro_question_patterns:
            if re.search(pattern, text_lower):
                best_domain = "astrology"
                break
        else:
            best_domain = "conversation"

    return {
        "domain": best_domain,
        "current_query": text,
        "detected_language": "en",  # Fallback assumes English
    }


def get_domain_from_intent(intent: str) -> DomainType:
    """
    Map an intent to its domain.

    Useful for backward compatibility with existing intent system.

    Args:
        intent: Detected intent string

    Returns:
        Domain type
    """
    intent_to_domain = {
        # Astrology
        "get_horoscope": "astrology",
        "birth_chart": "astrology",
        "kundli_matching": "astrology",
        "ask_astrologer": "astrology",
        "numerology": "astrology",
        "tarot_reading": "astrology",
        "dosha_check": "astrology",
        "life_prediction": "astrology",
        "get_panchang": "astrology",
        "get_remedy": "astrology",
        "find_muhurta": "astrology",
        # Travel
        "pnr_status": "travel",
        "train_status": "travel",
        "metro_ticket": "travel",
        # Utility
        "weather": "utility",
        "get_news": "utility",
        "local_search": "utility",
        "image": "utility",
        "set_reminder": "utility",
        "db_query": "utility",
        # Game
        "word_game": "game",
        # Conversation
        "chat": "conversation",
        "unknown": "conversation",
    }

    return intent_to_domain.get(intent, "conversation")


# Astrology-specific intent keywords (for sub-routing within astrology domain)
ASTRO_INTENT_KEYWORDS = {
    "get_horoscope": ["horoscope", "rashifal", "prediction for", "zodiac"],
    "birth_chart": ["kundli", "kundali", "birth chart", "janam patri", "planetary position"],
    "kundli_matching": ["match kundli", "compatibility", "gun milan", "matching"],
    "dosha_check": ["manglik", "kaal sarp", "sade sati", "dosha", "pitra"],
    "life_prediction": ["when will i", "will i get", "marriage prediction", "career prediction", "children", "abroad", "foreign"],
    "get_panchang": ["panchang", "tithi", "nakshatra today", "rahu kaal"],
    "numerology": ["numerology", "lucky number", "name number"],
    "tarot_reading": ["tarot", "card reading", "pick a card"],
    "get_remedy": ["gemstone", "stone", "mantra", "remedy", "puja for"],
    "find_muhurta": ["muhurat", "muhurta", "auspicious date", "best date for", "shubh"],
    "ask_astrologer": [],  # Fallback for astrology questions
}


def classify_astro_intent(query: str) -> str:
    """
    Classify query within astrology domain.

    Args:
        query: User query text

    Returns:
        Specific astrology intent
    """
    query_lower = query.lower()

    for intent, keywords in ASTRO_INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return intent

    # Default to ask_astrologer for unmatched astrology queries
    return "ask_astrologer"
