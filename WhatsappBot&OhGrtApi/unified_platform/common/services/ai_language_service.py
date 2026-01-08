"""
AI-Powered Language Understanding Service

Uses GPT-4o-mini for:
1. Language detection
2. Intent understanding
3. Entity extraction
4. Response translation

This replaces regex-based pattern matching with AI-first approach.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LanguageUnderstanding(BaseModel):
    """Structured output for language understanding."""

    detected_language: str = Field(
        description="ISO language code: en, hi, bn, ta, te, kn, ml, gu, mr, pa, or"
    )
    intent: str = Field(
        description="The detected intent"
    )
    confidence: float = Field(
        description="Confidence score 0-1"
    )
    entities: dict = Field(
        description="Extracted entities relevant to intent",
        default_factory=dict
    )
    normalized_query: str = Field(
        description="The query normalized to English for processing",
        default=""
    )


# Language understanding prompt - uses AI instead of regex
UNDERSTAND_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a multilingual AI assistant that understands 11 Indian languages.

Your job is to:
1. Detect the language of the user's message
2. Understand their intent
3. Extract relevant entities (like city names, dates, etc.)
4. Normalize any non-English values to English for API calls

SUPPORTED LANGUAGES:
- en: English
- hi: Hindi (हिंदी)
- bn: Bengali (বাংলা)
- ta: Tamil (தமிழ்)
- te: Telugu (తెలుగు)
- kn: Kannada (ಕನ್ನಡ)
- ml: Malayalam (മലയാളം)
- gu: Gujarati (ગુજરાતી)
- mr: Marathi (मराठी)
- pa: Punjabi (ਪੰਜਾਬੀ)
- or: Odia (ଓଡ଼ିଆ)

INTENTS:
- weather: User wants weather info for a city/location
- local_search: User wants to find places/restaurants/businesses
- pnr_status: User wants PNR status (10-digit number)
- train_status: User wants train running status
- metro_ticket: User wants metro info/fare
- image: User wants AI image generation
- word_game: User wants to play word game
- get_news: User wants news
- fact_check: User wants to verify a claim
- get_horoscope: User wants daily/weekly horoscope
- birth_chart: User wants kundli/birth chart
- kundli_matching: User wants compatibility matching
- ask_astrologer: General astrology question
- numerology: User wants numerology analysis
- tarot_reading: User wants tarot reading
- life_prediction: User wants life predictions
- dosha_check: User wants dosha analysis
- get_panchang: User wants panchang
- get_remedy: User wants remedies
- find_muhurta: User wants auspicious timing
- set_reminder: User wants to set reminder
- help: User asks what the bot can do
- chat: General conversation/greetings

ENTITY EXTRACTION RULES:
- For weather: Extract "city" (MUST be in English, e.g., "दिल्ली" → "Delhi")
- For local_search: Extract "search_query" and "location"
- For pnr_status: Extract "pnr" (10-digit number)
- For train_status: Extract "train_number"
- For get_horoscope: Extract "astro_sign" and "astro_period"
- For get_news: Extract "news_query" and "news_category"

CRITICAL: All entity values must be normalized to English for API calls.
City names in any language should be converted to English:
- दिल्ली → Delhi
- मुंबई → Mumbai
- चेन्नई → Chennai
- కోల్‌కతా → Kolkata
- বেঙ্গালুরু → Bengaluru
etc.

Examples:
User: "दिल्ली का मौसम बताओ"
Output: {{
    "detected_language": "hi",
    "intent": "weather",
    "confidence": 0.95,
    "entities": {{"city": "Delhi"}},
    "normalized_query": "Tell me Delhi weather"
}}

User: "சென்னை வானிலை"
Output: {{
    "detected_language": "ta",
    "intent": "weather",
    "confidence": 0.95,
    "entities": {{"city": "Chennai"}},
    "normalized_query": "Chennai weather"
}}

User: "हैदराबाद में रेस्टोरेंट"
Output: {{
    "detected_language": "hi",
    "intent": "local_search",
    "confidence": 0.95,
    "entities": {{"search_query": "restaurants", "location": "Hyderabad"}},
    "normalized_query": "restaurants in Hyderabad"
}}

User: "ਅੰਮ੍ਰਿਤਸਰ ਦਾ ਮੌਸਮ"
Output: {{
    "detected_language": "pa",
    "intent": "weather",
    "confidence": 0.95,
    "entities": {{"city": "Amritsar"}},
    "normalized_query": "Amritsar weather"
}}

Respond ONLY with valid JSON."""),
    ("human", "{message}")
])


# Translation prompt for converting tool results to user's language
TRANSLATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a translation assistant. Translate the following response into {target_language}.

LANGUAGE CODES:
- hi: Hindi (हिंदी)
- bn: Bengali (বাংলা)
- ta: Tamil (தமிழ்)
- te: Telugu (తెలుగు)
- kn: Kannada (ಕನ್ನಡ)
- ml: Malayalam (മലയാളം)
- gu: Gujarati (ગુજરાતી)
- mr: Marathi (मराठी)
- pa: Punjabi (ਪੰਜਾਬੀ)
- or: Odia (ଓଡ଼ିଆ)

RULES:
1. Keep numbers, dates, times, and proper nouns (city names, app names) as-is
2. Translate only the descriptive text
3. Keep emojis and formatting (*, _, etc.)
4. Be natural and conversational in the target language
5. Keep units like °C, km, ₹ as-is

Example (Hindi):
Input: "Weather in Delhi: 25°C, Sunny, Humidity: 60%"
Output: "दिल्ली का मौसम: 25°C, धूप, नमी: 60%"

Translate to {target_language}:"""),
    ("human", "{text}")
])


class AILanguageService:
    """AI-powered language understanding and translation service."""

    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the AI language service."""
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.1,
            api_key=openai_api_key
        )
        self.understand_chain = UNDERSTAND_PROMPT | self.llm
        self.translate_chain = TRANSLATE_PROMPT | self.llm

    async def understand_message(self, message: str) -> Dict[str, Any]:
        """
        Understand user message using AI.

        Returns:
            Dict with detected_language, intent, confidence, entities, normalized_query
        """
        if not message or not message.strip():
            return {
                "detected_language": "en",
                "intent": "chat",
                "confidence": 1.0,
                "entities": {},
                "normalized_query": ""
            }

        try:
            response = await self.understand_chain.ainvoke({"message": message})
            content = response.content.strip()

            # Parse JSON response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            result = json.loads(content)

            # Ensure required fields
            return {
                "detected_language": result.get("detected_language", "en"),
                "intent": result.get("intent", "chat"),
                "confidence": result.get("confidence", 0.8),
                "entities": result.get("entities", {}),
                "normalized_query": result.get("normalized_query", message)
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                "detected_language": "en",
                "intent": "chat",
                "confidence": 0.5,
                "entities": {},
                "normalized_query": message
            }
        except Exception as e:
            logger.error(f"AI understanding failed: {e}")
            return {
                "detected_language": "en",
                "intent": "chat",
                "confidence": 0.5,
                "entities": {},
                "normalized_query": message
            }

    async def translate_response(self, text: str, target_language: str) -> str:
        """
        Translate response text to target language.

        Args:
            text: Response text in English
            target_language: Target language code (hi, bn, ta, etc.)

        Returns:
            Translated text
        """
        # Don't translate if already in English
        if target_language == "en" or not text:
            return text

        language_names = {
            "hi": "Hindi",
            "bn": "Bengali",
            "ta": "Tamil",
            "te": "Telugu",
            "kn": "Kannada",
            "ml": "Malayalam",
            "gu": "Gujarati",
            "mr": "Marathi",
            "pa": "Punjabi",
            "or": "Odia"
        }

        target_lang_name = language_names.get(target_language, "Hindi")

        try:
            response = await self.translate_chain.ainvoke({
                "target_language": target_lang_name,
                "text": text
            })
            return response.content.strip()
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text  # Return original on failure


# Singleton instance
_ai_service: Optional[AILanguageService] = None


def get_ai_language_service() -> Optional[AILanguageService]:
    """Get the AI language service singleton."""
    global _ai_service
    return _ai_service


def init_ai_language_service(openai_api_key: str, model: str = "gpt-4o-mini") -> AILanguageService:
    """Initialize the AI language service singleton."""
    global _ai_service
    _ai_service = AILanguageService(openai_api_key, model)
    return _ai_service


async def ai_understand_message(message: str, openai_api_key: str = None) -> Dict[str, Any]:
    """
    Convenience function to understand a message using AI.

    This is the main entry point for AI-based language understanding.
    """
    global _ai_service

    if _ai_service is None and openai_api_key:
        _ai_service = AILanguageService(openai_api_key)

    if _ai_service is None:
        # Fallback if service not initialized
        return {
            "detected_language": "en",
            "intent": "chat",
            "confidence": 0.5,
            "entities": {},
            "normalized_query": message
        }

    return await _ai_service.understand_message(message)


async def ai_translate_response(text: str, target_language: str, openai_api_key: str = None) -> str:
    """
    Convenience function to translate a response.
    """
    global _ai_service

    if _ai_service is None and openai_api_key:
        _ai_service = AILanguageService(openai_api_key)

    if _ai_service is None or target_language == "en":
        return text

    return await _ai_service.translate_response(text, target_language)
