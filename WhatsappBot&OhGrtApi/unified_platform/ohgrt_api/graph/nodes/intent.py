"""
Intent Detection Node

Uses pattern matching and GPT-4o-mini for intent classification.
Extracts relevant entities based on detected intent.
"""

import re
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ohgrt_api.graph.state import BotState
from ohgrt_api.config import get_settings
from ohgrt_api.logger import logger


class IntentClassification(BaseModel):
    """Structured output for intent classification."""
    intent: str = Field(
        description="The classified intent"
    )
    confidence: float = Field(description="Confidence score between 0 and 1")
    entities: dict = Field(
        description="Extracted entities relevant to the intent",
        default_factory=dict,
    )


INTENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an intent classifier for an Indian AI assistant.

Classify the user message into one of these intents:
- local_search: Find places, restaurants, hospitals, businesses
- image: Generate/create an AI image
- pnr_status: Check Indian Railways PNR status (10-digit number)
- train_status: Live running status of a train
- metro_ticket: Metro information, fare, route help
- weather: Current weather conditions
- word_game: Play word games
- set_reminder: Set a reminder
- get_news: Get news headlines
- get_horoscope: Daily/weekly/monthly horoscope
- birth_chart: Birth chart/kundli analysis
- kundli_matching: Compatibility/matching for marriage
- ask_astrologer: General astrology questions
- numerology: Numerology analysis
- tarot_reading: Tarot card reading
- life_prediction: Marriage, career, children predictions
- dosha_check: Manglik, Kaal Sarp, Sade Sati check
- get_panchang: Daily panchang/tithi
- get_remedy: Gemstone, mantra recommendations
- find_muhurta: Auspicious dates/times
- subscription: Subscription management
- chat: General conversation

Extract relevant entities based on intent.
Respond in JSON with: intent, confidence (0.0-1.0), entities (dict)"""),
    ("human", "{message}"),
])


def extract_pnr(text: str) -> Optional[str]:
    """Extract 10-digit PNR number from text."""
    match = re.search(r'\b(\d{10})\b', text)
    return match.group(1) if match else None


def extract_train_number(text: str) -> Optional[str]:
    """Extract train number from text."""
    match = re.search(r'\b(\d{4,5})\b', text)
    return match.group(1) if match else None


def detect_intent(state: BotState) -> dict:
    """
    Node function: Detect intent from user message.

    Args:
        state: Current bot state with message

    Returns:
        Updated state dict with intent, confidence, and entities
    """
    user_message = state["whatsapp_message"].get("text", "")

    if not user_message:
        return {
            "intent": "chat",
            "intent_confidence": 1.0,
            "extracted_entities": {},
            "current_query": "",
            "error": None,
        }

    user_lower = user_message.lower()

    # Quick pattern matching for common cases (faster than LLM)

    # PNR pattern (10 digits)
    pnr_match = extract_pnr(user_message)
    if pnr_match and ("pnr" in user_lower or len(user_message.replace(" ", "")) <= 15):
        return {
            "intent": "pnr_status",
            "intent_confidence": 0.95,
            "extracted_entities": {"pnr": pnr_match},
            "current_query": user_message,
            "error": None,
        }

    # Train status
    train_keywords = ["train", "running status", "where is", "train status"]
    if any(kw in user_lower for kw in train_keywords):
        train_num = extract_train_number(user_message)
        if train_num:
            return {
                "intent": "train_status",
                "intent_confidence": 0.9,
                "extracted_entities": {"train_number": train_num},
                "current_query": user_message,
                "error": None,
            }

    # Image generation
    image_keywords = ["generate image", "create image", "make image", "draw", "image of"]
    if any(kw in user_lower for kw in image_keywords):
        return {
            "intent": "image",
            "intent_confidence": 0.9,
            "extracted_entities": {"image_prompt": user_message},
            "current_query": user_message,
            "error": None,
        }

    # Weather
    weather_keywords = ["weather", "temperature", "mausam"]
    if any(kw in user_lower for kw in weather_keywords):
        # Extract city - use \b word boundary to avoid matching "at" in "What"
        city_match = re.search(r"\b(?:in|at|for)\s+([A-Za-z\s]+?)(?:\s*$|\s*\?)", user_message, re.IGNORECASE)
        city = city_match.group(1).strip() if city_match else ""
        return {
            "intent": "weather",
            "intent_confidence": 0.9,
            "extracted_entities": {"city": city},
            "current_query": user_message,
            "error": None,
        }

    # News
    news_keywords = ["news", "headlines", "latest news", "breaking news", "khabar"]
    if any(kw in user_lower for kw in news_keywords):
        # Extract topic/category from query
        news_query = ""
        news_category = ""

        # Detect category from common terms
        category_map = {
            "tech": "technology", "technology": "technology", "tech news": "technology",
            "sport": "sports", "sports": "sports", "cricket": "sports", "football": "sports",
            "business": "business", "finance": "business", "economy": "business",
            "entertainment": "entertainment", "bollywood": "entertainment", "movies": "entertainment",
            "health": "health", "science": "science",
        }
        for term, cat in category_map.items():
            if term in user_lower:
                news_category = cat
                break

        # Extract specific topic if mentioned (e.g., "news about India", "news on AI")
        topic_match = re.search(r"(?:news\s+(?:about|on|of|for))\s+([A-Za-z\s]+?)(?:\s*$|\s*\?)", user_message, re.IGNORECASE)
        if topic_match:
            news_query = topic_match.group(1).strip()

        return {
            "intent": "get_news",
            "intent_confidence": 0.9,
            "extracted_entities": {"news_query": news_query, "news_category": news_category},
            "current_query": user_message,
            "error": None,
        }

    # Metro
    metro_keywords = ["metro", "dmrc", "delhi metro", "metro fare"]
    if any(kw in user_lower for kw in metro_keywords):
        return {
            "intent": "metro_ticket",
            "intent_confidence": 0.85,
            "extracted_entities": {"query": user_message},
            "current_query": user_message,
            "error": None,
        }

    # Word game
    game_keywords = ["word game", "play a game", "anagram", "wordle"]
    if any(kw in user_lower for kw in game_keywords):
        return {
            "intent": "word_game",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "error": None,
        }

    # Reminder / Schedule
    reminder_keywords = ["remind", "reminder", "alarm", "schedule", "scheduled", "alert", "notify me"]
    if any(kw in user_lower for kw in reminder_keywords):
        # Check for time-related words to confirm scheduling intent
        time_words = ["at", "every", "daily", "weekly", "tomorrow", "in", "pm", "am", "hour", "minute"]
        if any(tw in user_lower for tw in time_words):
            return {
                "intent": "set_reminder",
                "intent_confidence": 0.95,
                "extracted_entities": {"reminder_text": user_message},
                "current_query": user_message,
                "error": None,
            }
        return {
            "intent": "set_reminder",
            "intent_confidence": 0.85,
            "extracted_entities": {"reminder_text": user_message},
            "current_query": user_message,
            "error": None,
        }

    # Subscription
    subscription_keywords = ["subscribe", "subscription", "premium", "plan"]
    if any(kw in user_lower for kw in subscription_keywords):
        return {
            "intent": "subscription",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "error": None,
        }

    # --- Astrology Intents ---

    # Tarot
    tarot_keywords = ["tarot", "tarot card", "card reading"]
    if any(kw in user_lower for kw in tarot_keywords):
        spread_type = "three_card"
        if "single" in user_lower or "one card" in user_lower:
            spread_type = "single"
        elif "celtic" in user_lower:
            spread_type = "celtic_cross"
        return {
            "intent": "tarot_reading",
            "intent_confidence": 0.95,
            "extracted_entities": {"spread_type": spread_type},
            "current_query": user_message,
            "error": None,
        }

    # Numerology
    numerology_keywords = ["numerology", "lucky number", "life path"]
    if any(kw in user_lower for kw in numerology_keywords):
        name_match = re.search(r"(?:for|of)\s+([A-Za-z\s]+?)(?:,|\s+born|$)", user_message, re.IGNORECASE)
        extracted_name = name_match.group(1).strip() if name_match else ""
        # Extract birth date
        date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
        extracted_date = date_match.group(1) if date_match else ""
        return {
            "intent": "numerology",
            "intent_confidence": 0.95,
            "extracted_entities": {"name": extracted_name, "birth_date": extracted_date},
            "current_query": user_message,
            "error": None,
        }

    # Kundli matching
    kundli_match_keywords = ["kundli match", "gun milan", "marriage compatibility", "match kundli"]
    if any(kw in user_lower for kw in kundli_match_keywords):
        return {
            "intent": "kundli_matching",
            "intent_confidence": 0.95,
            "extracted_entities": {},
            "current_query": user_message,
            "error": None,
        }

    # Birth chart
    birth_chart_keywords = ["birth chart", "kundli", "kundali", "janam patri", "natal chart"]
    if any(kw in user_lower for kw in birth_chart_keywords):
        date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
        extracted_date = date_match.group(1) if date_match else ""
        return {
            "intent": "birth_chart",
            "intent_confidence": 0.95,
            "extracted_entities": {"birth_date": extracted_date},
            "current_query": user_message,
            "error": None,
        }

    # Dosha check
    dosha_keywords = ["manglik", "kaal sarp", "sade sati", "dosha"]
    if any(kw in user_lower for kw in dosha_keywords):
        specific_dosha = None
        if "manglik" in user_lower:
            specific_dosha = "manglik"
        elif "kaal sarp" in user_lower:
            specific_dosha = "kaal_sarp"
        elif "sade sati" in user_lower:
            specific_dosha = "sade_sati"
        return {
            "intent": "dosha_check",
            "intent_confidence": 0.95,
            "extracted_entities": {"specific_dosha": specific_dosha},
            "current_query": user_message,
            "error": None,
        }

    # Life prediction
    life_keywords = ["when will i", "marriage prediction", "career prediction", "will i get"]
    if any(kw in user_lower for kw in life_keywords):
        prediction_type = "general"
        if any(kw in user_lower for kw in ["married", "marriage", "spouse"]):
            prediction_type = "marriage"
        elif any(kw in user_lower for kw in ["job", "career", "promotion"]):
            prediction_type = "career"
        elif any(kw in user_lower for kw in ["baby", "child", "children"]):
            prediction_type = "children"
        return {
            "intent": "life_prediction",
            "intent_confidence": 0.95,
            "extracted_entities": {"prediction_type": prediction_type},
            "current_query": user_message,
            "error": None,
        }

    # Panchang
    panchang_keywords = ["panchang", "tithi", "nakshatra today", "rahu kaal"]
    if any(kw in user_lower for kw in panchang_keywords):
        return {
            "intent": "get_panchang",
            "intent_confidence": 0.95,
            "extracted_entities": {"location": "Delhi"},
            "current_query": user_message,
            "error": None,
        }

    # Remedy - check before horoscope since queries may contain zodiac signs
    remedy_keywords = [
        "which stone", "which gemstone", "gemstone for", "gemstone should",
        "stone for", "stone should", "wear stone", "wear gemstone",
        "mantra for", "mantra to", "remedy for", "remedy to",
        "puja for", "pooja for", "best stone", "lucky stone",
        "ratna", "neelam", "ruby for", "pearl for", "emerald for",
    ]
    if any(kw in user_lower for kw in remedy_keywords):
        return {
            "intent": "get_remedy",
            "intent_confidence": 0.95,
            "extracted_entities": {"question": user_message},
            "current_query": user_message,
            "error": None,
        }

    # Muhurta
    muhurta_keywords = ["muhurat", "auspicious date", "shubh muhurat", "best date for"]
    if any(kw in user_lower for kw in muhurta_keywords):
        return {
            "intent": "find_muhurta",
            "intent_confidence": 0.9,
            "extracted_entities": {"question": user_message},
            "current_query": user_message,
            "error": None,
        }

    # Horoscope
    zodiac_signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    horoscope_keywords = ["horoscope", "zodiac", "rashifal"]

    if any(kw in user_lower for kw in horoscope_keywords) or any(sign in user_lower for sign in zodiac_signs):
        detected_sign = None
        for sign in zodiac_signs:
            if sign in user_lower:
                detected_sign = sign
                break

        period = "today"
        if "weekly" in user_lower:
            period = "weekly"
        elif "monthly" in user_lower:
            period = "monthly"

        return {
            "intent": "get_horoscope",
            "intent_confidence": 0.95,
            "extracted_entities": {"astro_sign": detected_sign, "astro_period": period},
            "current_query": user_message,
            "error": None,
        }

    # For other cases, use LLM
    try:
        settings = get_settings()
        if not settings.openai_api_key:
            # Fallback to chat if no API key
            return {
                "intent": "chat",
                "intent_confidence": 0.7,
                "extracted_entities": {},
                "current_query": user_message,
                "error": None,
            }

        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key,
        )
        structured_llm = llm.with_structured_output(IntentClassification, method="function_calling")
        chain = INTENT_PROMPT | structured_llm
        result: IntentClassification = chain.invoke({"message": user_message})

        valid_intents = [
            "local_search", "image", "pnr_status", "train_status", "metro_ticket",
            "weather", "word_game", "set_reminder", "get_news",
            "get_horoscope", "birth_chart", "kundli_matching", "ask_astrologer",
            "numerology", "tarot_reading", "life_prediction", "dosha_check",
            "get_panchang", "get_remedy", "find_muhurta", "subscription", "chat",
        ]
        intent = result.intent if result.intent in valid_intents else "chat"

        return {
            "intent": intent,
            "intent_confidence": result.confidence,
            "extracted_entities": result.entities or {},
            "current_query": user_message,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Intent detection error: {e}")
        return {
            "intent": "chat",
            "intent_confidence": 0.5,
            "extracted_entities": {},
            "current_query": user_message,
            "error": f"Intent detection error: {str(e)}",
        }
