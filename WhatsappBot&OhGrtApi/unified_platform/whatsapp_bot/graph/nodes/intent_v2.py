"""
Intent Detection Node

Uses GPT-4o-mini for intent classification with structured output.
Extracts relevant entities based on detected intent.
"""

import re
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from whatsapp_bot.state import BotState
from common.config.settings import settings as common_settings
from common.utils.entity_extraction import extract_pnr, extract_train_number
from whatsapp_bot.stores.pending_location_store import get_pending_location_store
from common.i18n.detector import detect_language
from whatsapp_bot.graph.context_cache import get_context as get_followup_context

# AI Language Service (optional)
try:
    from common.services.ai_language_service import ai_understand_message
    AI_UNDERSTAND_AVAILABLE = True
except ImportError:
    AI_UNDERSTAND_AVAILABLE = False

logger = logging.getLogger(__name__)

CONTEXT_TTL_SECONDS = 600
CONTEXT_REUSE_INTENTS = {
    "weather",
    "get_news",
    "stock_price",
    "cricket_score",
    "govt_jobs",
    "govt_schemes",
    "farmer_schemes",
    "local_search",
    "events",
    "food_order",
    "image_analysis",
}
CONTEXT_HINTS = [
    "and", "also", "what about", "tomorrow", "today", "now", "this", "same",
    "again", "update", "next", "more", "price", "humidity", "wind",
]
GREETING_ONLY = {"hi", "hello", "hey", "namaste", "hola"}


def _is_smalltalk(message: str) -> bool:
    msg = (message or "").strip().lower()
    smalltalk_phrases = [
        "how are you", "how r u", "how ru", "what's up", "whats up",
        "what are you doing", "what r you doing", "wru doing",
        "good morning", "good afternoon", "good evening", "good night",
        "sup", "yo", "hey there",
        "kaise ho", "kaisi ho", "kaisa hai", "kya kar rahe ho", "kya kar rahe",
        "kya chal raha", "aur batao", "kaise chal raha", "kaise chal rha",
    ]
    return any(phrase in msg for phrase in smalltalk_phrases)


def _should_reuse_context(message: str) -> bool:
    msg = (message or "").strip().lower()
    if not msg or msg in GREETING_ONLY:
        return False
    if _is_smalltalk(msg):
        return False
    if len(msg.split()) <= 4:
        return True
    return any(hint in msg for hint in CONTEXT_HINTS)


def _is_image_followup_request(message: str) -> bool:
    msg = (message or "").lower()
    keywords = [
        "image me", "photo me", "is image", "is photo",
        "jo text", "text hai", "likha", "kya likha",
        "read the text", "extract text", "ocr",
        "image text", "photo text",
    ]
    return any(kw in msg for kw in keywords)


def _maybe_use_recent_context(
    phone: str,
    message: str,
    intent: str,
    confidence: float,
    entities: dict,
) -> tuple[str, float, dict]:
    # Reuse recent intent for short follow-ups to avoid stateless replies.
    if intent not in ["chat", "unknown"] and confidence >= 0.6:
        return intent, confidence, entities
    if not _should_reuse_context(message):
        return intent, confidence, entities

    cached = get_followup_context(phone) if phone else None
    if not cached:
        return intent, confidence, entities
    last_intent = cached.get("last_intent")
    last_entities = cached.get("last_entities") or {}
    if last_intent in CONTEXT_REUSE_INTENTS:
        return last_intent, max(confidence, 0.7), last_entities
    return intent, confidence, entities

class IntentClassification(BaseModel):
    """Structured output for intent classification."""

    intent: str = Field(
        description="The classified intent: local_search, image, image_analysis, pnr_status, train_status, train_journey, metro_ticket, weather, word_game, db_query, set_reminder, get_news, stock_price, cricket_score, govt_jobs, govt_schemes, farmer_schemes, free_audio_sources, echallan, fact_check, get_horoscope, birth_chart, kundli_matching, ask_astrologer, numerology, tarot_reading, life_prediction, dosha_check, get_panchang, get_remedy, find_muhurta, or chat"
    )
    confidence: float = Field(description="Confidence score between 0 and 1")
    entities: dict = Field(
        description="Extracted entities relevant to the intent",
        default_factory=dict,
    )


def _is_followup_request(message: str) -> bool:
    msg = message.lower().strip()
    if not msg or len(msg) > 80:
        return False
    followups = [
        "more", "more result", "more results", "some more", "next", "another",
        "one more", "again", "same", "same please",
        "aur", "aur result", "aur results", "aur bhi", "kuch aur", "phir se",
        "details", "detail", "details of these", "how to get details", "how to apply",
        "link", "links", "website", "site",
    ]
    return any(kw in msg for kw in followups)


INTENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an intent classifier for an Indian WhatsApp assistant similar to puch.ai.

Classify the user message into one of these intents:
- local_search: User wants to find places, restaurants, hospitals, businesses, services nearby or in a location
  Examples: "restaurants near me", "hospitals in dwarka", "cafes in connaught place"
- image: User wants to generate/create an AI image
  Examples: "generate image of sunset", "create picture of cat", "make an image of mountains"
- pnr_status: User wants to check Indian Railways PNR status (look for 10-digit number)
  Examples: "check pnr 1234567890", "pnr status 9876543210", "what is my pnr 1111111111"
- train_status: User wants live running status of a train (look for train numbers like 12301, 22691)
  Examples: "train 12301 status", "where is train 22691", "running status of rajdhani"
- train_journey: User wants to plan a train journey between two cities on a date
  Examples: "plan a train journey from Bengaluru to Delhi on 26 January", "trains from Mumbai to Pune"
- train_journey: User wants to plan a train journey between two cities on a date
  Examples: "plan a train journey from Bengaluru to Delhi on 26 January", "trains from Mumbai to Pune"
- metro_ticket: User wants metro information, fare, or route help (Delhi Metro, Bangalore Metro, etc.)
  Examples: "metro from dwarka to rajiv chowk", "metro fare", "how to reach nehru place by metro"
- weather: User wants to know the current weather conditions for a specific city.
  Examples: "weather in london", "how is the weather in new york", "what's the temperature in paris"
- word_game: User wants to play a word game.
  Examples: "play a game", "word game", "let's play a word game"
- db_query: User wants to query the database for specific information.
  Examples: "how many registered users", "what is the total number of orders", "show me the latest users"
- set_reminder: User wants to set a reminder.
  Examples: "remind me in 5 minutes to call John", "set an alarm for 9 AM to take medicine", "remind me to buy groceries tomorrow"
- get_news: User wants to get news headlines.
  Examples: "latest news", "cricket news", "news about dhoni"
- stock_price: User wants a stock/share price or key stock stats
  Examples: "tata motors stock price", "share price of reliance", "AAPL price"
- cricket_score: User wants live cricket scores or score updates
  Examples: "cricket score", "live score", "IPL score", "scorecard"
- govt_jobs: User wants government job openings or notifications (state-wise or central)
  Examples: "govt jobs in bihar", "sarkari naukri delhi", "central government jobs"
- govt_schemes: User wants government schemes/yojanas (state-wise or central)
  Examples: "schemes in bihar", "sarkari yojana delhi", "central government schemes"
- farmer_schemes: User wants farmer schemes/subsidies (state-wise or central)
  Examples: "farmer subsidy kerala", "kisan scheme up", "farmers scheme in tamilnadu"
- free_audio_sources: User wants free/royalty-free audio sources
  Examples: "free audio sources", "royalty free music", "free songs for use"
- echallan: User wants vehicle/traffic challan checks (All India)
  Examples: "check challan", "traffic challan", "vehicle challan status", "e challan"
- fact_check: User wants to verify if a claim, news, or statement is true or false
  Examples: "fact check: drinking warm water kills coronavirus", "is this true: 5G causes health problems", "verify: earth is flat", "is this news real", "is this fake news", "sach hai kya", "jhooth hai kya"

ASTROLOGY INTENTS (AstroTalk-like features):
- get_horoscope: User wants daily/weekly/monthly horoscope for a zodiac sign
  Examples: "aries horoscope", "leo weekly horoscope", "my horoscope today", "scorpio monthly prediction"
- birth_chart: User wants birth chart/kundli analysis based on birth details
  Examples: "my birth chart", "kundli for 15-08-1990 10:30 AM Delhi", "generate my kundli", "janam patri"
- kundli_matching: User wants compatibility/matching between two people for marriage
  Examples: "match kundli of Rahul and Priya", "compatibility check", "gun milan", "marriage compatibility"
- ask_astrologer: User has general astrology questions (not horoscope, not kundli)
  Examples: "what does saturn return mean", "which gemstone for leo", "is mercury retrograde bad", "what is manglik dosha"
- numerology: User wants numerology analysis based on name or date
  Examples: "numerology for Rahul", "my lucky number", "name numerology", "life path number"
- tarot_reading: User wants a tarot card reading
  Examples: "tarot reading", "pick a tarot card", "tarot for love", "celtic cross spread"

- help: User asks what the bot can do, its features, capabilities, or needs assistance
  Examples: "what can you do", "what are your features", "help me", "what services do you offer"
- chat: General conversation, greetings, or anything that doesn't fit above
  Examples: "hello", "tell me a joke", "who are you", "how are you"

Extract relevant entities based on intent:
- For pnr_status: Extract the 10-digit PNR number as "pnr"
- For train_status: Extract train number as "train_number" and optional date as "date"
- For train_journey: Extract "source_city", "destination_city", and "journey_date"
- For train_journey: Extract "source_city", "destination_city", and "journey_date"
- For local_search: Extract search query as "search_query" and location as "location"
  IMPORTANT: "near me", "nearby", "nearest", "around me", "close to me" are NOT locations - leave location empty for these. Only extract actual place names like "Delhi", "Connaught Place", "BTM Layout" as location.
- For image: Extract the image description as "image_prompt"
- For metro_ticket: Extract "source_station" and "destination_station"
- For weather: Extract the city name as "city"
- For set_reminder: Extract the reminder time as "reminder_time" and the reminder message as "reminder_message"
- For get_news: Extract the news query as "news_query" and news category as "news_category"
- For stock_price: Extract company or ticker as "stock_name"
- For fact_check: Extract the claim to verify as "fact_check_claim"
- For get_horoscope: Extract "astro_sign" (zodiac sign) and "astro_period" (today/tomorrow/weekly/monthly)
- For birth_chart: Extract "name", "birth_date", "birth_time", "birth_place"
- For kundli_matching: Extract "person1_name", "person1_dob", "person1_time", "person1_place", "person2_name", "person2_dob", "person2_time", "person2_place"
- For ask_astrologer: Extract the question as "astro_question", optional "user_sign" and "user_dob"
- For numerology: Extract "name" and optional "birth_date"
- For tarot_reading: Extract "tarot_question" and "spread_type" (single/three_card/celtic_cross)

Be generous with local_search - if user mentions a place type and location, it's local_search.
If unsure between intents, default to chat.

    EXAMPLES:
    User: "Remind me in 5 minutes to drink water"
    Output: {{
        "intent": "set_reminder",
        "confidence": 0.95,
        "entities": {{"reminder_time": "in 5 minutes", "reminder_message": "drink water"}}
    }}

    User: "Kundli for Rahul born on 15-08-1990 at 10:30 AM in Delhi"
    Output: {{
        "intent": "birth_chart",
        "confidence": 0.95,
        "entities": {{
            "name": "Rahul",
            "birth_date": "15-08-1990",
            "birth_time": "10:30 AM",
            "birth_place": "Delhi"
        }}
    }}

    User: "Match kundli of Rahul (15-08-1990) and Priya (22-03-1992)"
    Output: {{
        "intent": "kundli_matching",
        "confidence": 0.95,
        "entities": {{
            "person1_name": "Rahul",
            "person1_dob": "15-08-1990",
            "person2_name": "Priya",
            "person2_dob": "22-03-1992"
        }}
    }}

    User: "Numerology for Rahul Kumar"
    Output: {{
        "intent": "numerology",
        "confidence": 0.95,
        "entities": {{"name": "Rahul Kumar"}}
    }}

    User: "Weather in Mumbai"
    Output: {{
        "intent": "weather",
        "confidence": 0.95,
        "entities": {{"city": "Mumbai"}}
    }}
    
Respond in JSON format with: intent, confidence (0.0-1.0), entities (dict)""",
        ),
        ("human", "{message}"),
    ]
)


async def detect_intent(state: BotState) -> dict:
    """
    Node function: Detect intent from user message.

    Args:
        state: Current bot state with WhatsApp message

    Returns:
        Updated state dict with intent, confidence, entities, and detected_language
    """
    whatsapp_message = state.get("whatsapp_message", {})
    user_message = whatsapp_message.get("text", "")
    message_type = whatsapp_message.get("message_type", "text")
    phone = whatsapp_message.get("from_number", "")

    # Detect language from user message (AI first, fallback to rule-based)
    detected_lang = "en"
    if user_message:
        if AI_UNDERSTAND_AVAILABLE and common_settings.OPENAI_API_KEY:
            try:
                ai_result = await ai_understand_message(
                    user_message,
                    openai_api_key=common_settings.OPENAI_API_KEY,
                )
                detected_lang = ai_result.get("detected_language", "en")
            except Exception as e:
                logger.warning(f"AI language detection failed, falling back: {e}")
                detected_lang = detect_language(user_message)
        else:
            detected_lang = detect_language(user_message)
    logger.info(f"Detected language: {detected_lang} for message: {(user_message or '')[:50]}...")

    # Follow-up handling: reuse last intent + query for short follow-ups
    if user_message and _is_followup_request(user_message):
        cached = get_followup_context(phone) if phone else None
        last_intent = (cached or {}).get("last_intent")
        last_query = (cached or {}).get("last_user_query")
        followup_intents = {
            "govt_jobs",
            "govt_schemes",
            "farmer_schemes",
            "get_news",
            "cricket_score",
            "local_search",
            "free_audio_sources",
        }
        if last_intent in followup_intents and last_query:
            logger.info(f"Follow-up detected. Reusing intent={last_intent}")
            return {
                "intent": last_intent,
                "intent_confidence": 0.9,
                "extracted_entities": {"followup": True},
                "current_query": last_query,
                "detected_language": detected_lang,
                "error": None,
            }

    # Check if this is a location message with a pending search
    if message_type == "location" and whatsapp_message.get("location"):
        pending_store = get_pending_location_store()
        # Peek at pending search (don't remove it - let the handler consume it)
        pending = await pending_store.peek_pending_search(phone)
        logger.info(f"Location message from {phone}, pending_search: {pending}")
        if pending:
            search_query = pending.get("search_query", "")
            # Check if it's a weather location request
            if search_query == "__weather__":
                logger.info(f"Routing location message to weather for pending weather request")
                return {
                    "intent": "weather",
                    "intent_confidence": 1.0,
                    "extracted_entities": {},
                    "current_query": "",
                    "detected_language": detected_lang,
                    "error": None,
                }
            # Check if it's a food/restaurant location request
            elif search_query == "__food__":
                logger.info(f"Routing location message to food_order for pending food search")
                return {
                    "intent": "food_order",
                    "intent_confidence": 1.0,
                    "extracted_entities": {},
                    "current_query": "restaurants near me",
                    "detected_language": detected_lang,
                    "error": None,
                }
            # Check if it's an events location request (IPL, concerts, comedy, etc.)
            elif search_query.startswith("__events"):
                logger.info(f"Routing location message to events for pending event search: {search_query}")
                return {
                    "intent": "events",
                    "intent_confidence": 1.0,
                    "extracted_entities": {},
                    "current_query": pending.get("original_message", "events near me"),
                    "detected_language": detected_lang,
                    "error": None,
                }
            else:
                # Route to local_search to handle the pending search with location
                logger.info(f"Routing location message to local_search for pending search")
                return {
                    "intent": "local_search",
                    "intent_confidence": 1.0,
                    "extracted_entities": {},
                    "current_query": "",
                    "detected_language": detected_lang,
                    "error": None,
                }

    if not user_message:
        return {
            "intent": "chat",
            "intent_confidence": 1.0,
            "extracted_entities": {},
            "current_query": "",
            "detected_language": detected_lang,
            "error": None,
        }

    # Quick pattern matching for common cases (faster than LLM)
    user_lower = user_message.lower()

    # Check for help/what can you do patterns first
    help_keywords = [
        # English
        "what can you do", "what do you do", "what are your features",
        "what services", "how can you help", "what can i ask",
        "show me what you can do", "help me", "help",
        # Hindi
        "मदद", "सहायता", "क्या कर सकते हो", "तुम क्या कर सकते हो",
        "क्या क्या कर सकते हो", "मदद करो", "हेल्प",
        # Bengali
        "সাহায্য", "কি কি করতে পার", "তুমি কি করতে পার", "হেল্প",
        # Tamil
        "உதவி", "என்ன செய்ய முடியும்", "உங்களால் என்ன செய்ய முடியும்",
        # Telugu
        "సహాయం", "ఏం చేయగలవు", "మీరు ఏం చేయగలరు", "హెల్ప్",
        # Kannada
        "ಸಹಾಯ", "ಏನು ಮಾಡಬಹುದು", "ನೀವು ಏನು ಮಾಡಬಹುದು", "ಹೆಲ್ಪ್",
        # Malayalam
        "സഹായം", "സഹായിക്കൂ", "എന്ത് ചെയ്യാൻ കഴിയും", "നിങ്ങൾക്ക് എന്ത് ചെയ്യാൻ കഴിയും",
        # Gujarati
        "મદદ", "શું કરી શકો છો", "તમે શું કરી શકો છો", "હેલ્પ",
        # Marathi
        "मदत", "काय करू शकतो", "तुम्ही काय करू शकता", "हेल्प",
        # Punjabi
        "ਮਦਦ", "ਕੀ ਕਰ ਸਕਦੇ ਹੋ", "ਤੁਸੀਂ ਕੀ ਕਰ ਸਕਦੇ ਹੋ", "ਹੈਲਪ",
        # Odia
        "ସାହାଯ୍ୟ", "କଣ କରିପାରିବ", "ଆପଣ କଣ କରିପାରିବେ", "ହେଲ୍ପ",
    ]
    if any(kw in user_lower for kw in help_keywords):
        return {
            "intent": "help",
            "intent_confidence": 0.95,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for weather patterns EARLY (before food check - "weather" contains "eat")
    weather_keywords = [
        # English
        "weather", "temperature",
        # Hindi
        "मौसम", "mausam", "तापमान", "موسم",
        # Bengali
        "আবহাওয়া", "তাপমাত্রা",
        # Tamil
        "வானிலை", "வெப்பநிலை",
        # Telugu
        "వాతావరణం", "ఉష్ణోగ్రత",
        # Kannada
        "ಹವಾಮಾನ", "ತಾಪಮಾನ",
        # Malayalam
        "കാലാവസ്ഥ", "താപനില",
        # Gujarati
        "હવામાન", "તાપમાન",
        # Marathi
        "हवामान", "तापमान",
        # Punjabi
        "ਮੌਸਮ", "ਤਾਪਮਾਨ",
        # Odia
        "ପାଣିପାଗ", "ତାପମାତ୍ରା",
    ]
    if any(kw in user_lower for kw in weather_keywords) or any(kw in user_message for kw in weather_keywords):
        city = ""
        non_city_words = ["the", "today", "tomorrow", "current", "what", "how", "whats", "hows",
                          "is", "now", "please", "tell", "me", "show", "get", "check", "a", "an",
                          "weather", "temperature", "mausam", "kaisa", "hai", "aaj", "ka", "kal",
                          "में", "का", "की", "के", "कैसा", "बताओ", "बताइए", "क्या"]

        # Hindi/Indian city name to English mapping
        city_name_map = {
            # Hindi
            "दिल्ली": "Delhi", "नई दिल्ली": "New Delhi", "मुंबई": "Mumbai", "बम्बई": "Mumbai",
            "कोलकाता": "Kolkata", "कलकत्ता": "Kolkata", "चेन्नई": "Chennai", "मद्रास": "Chennai",
            "बेंगलुरु": "Bengaluru", "बैंगलोर": "Bangalore", "हैदराबाद": "Hyderabad",
            "अहमदाबाद": "Ahmedabad", "पुणे": "Pune", "जयपुर": "Jaipur", "लखनऊ": "Lucknow",
            "कानपुर": "Kanpur", "नागपुर": "Nagpur", "इंदौर": "Indore", "भोपाल": "Bhopal",
            "पटना": "Patna", "वाराणसी": "Varanasi", "आगरा": "Agra", "सूरत": "Surat",
            "गुड़गांव": "Gurgaon", "नोएडा": "Noida", "चंडीगढ़": "Chandigarh",
            # Tamil
            "சென்னை": "Chennai", "கோயம்புத்தூர்": "Coimbatore", "மதுரை": "Madurai",
            # Telugu
            "హైదరాబాద్": "Hyderabad", "విజయవాడ": "Vijayawada", "విశాఖపట్నం": "Visakhapatnam",
            # Bengali
            "কলকাতা": "Kolkata", "দিল্লি": "Delhi", "মুম্বাই": "Mumbai",
            # Kannada
            "ಬೆಂಗಳೂರು": "Bengaluru", "ಮೈಸೂರು": "Mysore", "ಹುಬ್ಬಳ್ಳಿ": "Hubli",
            # Malayalam
            "കൊച്ചി": "Kochi", "തിരുവനന്തപുരം": "Thiruvananthapuram",
            # Gujarati
            "અમદાવાદ": "Ahmedabad", "સુરત": "Surat", "વડોદરા": "Vadodara",
            # Marathi
            "मुंबई": "Mumbai", "पुणे": "Pune", "नागपूर": "Nagpur",
            # Punjabi
            "ਚੰਡੀਗੜ੍ਹ": "Chandigarh", "ਅੰਮ੍ਰਿਤਸਰ": "Amritsar", "ਲੁਧਿਆਣਾ": "Ludhiana",
            # Odia
            "ଭୁବନେଶ୍ୱର": "Bhubaneswar", "କଟକ": "Cuttack",
        }

        # Pattern 1: English "weather in/of/for/at <city>"
        city_match = re.search(r"weather\s+(?:in|of|for|at)\s+([a-zA-Z][a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+now|\?|$)", user_lower)
        if city_match:
            potential = city_match.group(1).strip()
            if potential and potential not in non_city_words:
                city = potential

        # Pattern 2: English "<city> weather"
        if not city:
            city_match = re.search(r"^([a-zA-Z][a-zA-Z\s]+?)\s+weather", user_lower)
            if city_match:
                potential = city_match.group(1).strip()
                if potential and potential not in non_city_words:
                    city = potential

        # Pattern 3: Hindi "{city} का मौसम" or "{city} में मौसम" or "{city} का तापमान"
        if not city:
            hindi_patterns = [
                r"(.+?)\s+(?:का|में|की)\s+(?:मौसम|तापमान)",  # दिल्ली का मौसम
                r"(?:मौसम|तापमान)\s+(.+?)\s+में",  # मौसम दिल्ली में
            ]
            for pattern in hindi_patterns:
                city_match = re.search(pattern, user_message)
                if city_match:
                    potential = city_match.group(1).strip()
                    # Check if it's a known Hindi city name
                    if potential in city_name_map:
                        city = city_name_map[potential]
                        break
                    # Also check without exact match (partial)
                    for hindi_city, eng_city in city_name_map.items():
                        if hindi_city in potential:
                            city = eng_city
                            break
                    if city:
                        break

        # Pattern 4: Check for any known city name in the message
        if not city:
            for hindi_city, eng_city in city_name_map.items():
                if hindi_city in user_message:
                    city = eng_city
                    break

        # Pattern 5: Simple English extraction "weather in delhi" (more lenient)
        if not city:
            city_match = re.search(r"weather\s+in\s+([a-zA-Z]+)", user_lower)
            if city_match:
                city = city_match.group(1).strip()

        logger.info(f"Weather intent detected: city={city}")
        return {
            "intent": "weather",
            "intent_confidence": 0.95,
            "extracted_entities": {"city": city.title() if city else ""},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for PNR pattern first (10 digits)
    pnr_match = extract_pnr(user_message)
    if pnr_match and ("pnr" in user_lower or len(user_message.replace(" ", "")) <= 15):
        return {
            "intent": "pnr_status",
            "intent_confidence": 0.95,
            "extracted_entities": {"pnr": pnr_match},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for e-challan patterns
    echallan_keywords = [
        "challan",
        "e-challan",
        "echallan",
        "traffic challan",
        "vehicle challan",
        "vehicle fine",
        "traffic fine",
        "challan status",
    ]
    if any(kw in user_lower for kw in echallan_keywords):
        return {
            "intent": "echallan",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for train journey planning (from/to + optional date)
    journey_keywords = [
        "train journey", "plan train", "train from", "trains from", "train to",
        "book train", "railway from", "railway to",
        "यात्रा", "ट्रेन यात्रा", "ट्रेन से", "ट्रेन टिकट",
        "यात्रा योजना", "यात्रा प्लान",
    ]
    has_route_markers = (
        " from " in user_lower
        and " to " in user_lower
    ) or (" से " in user_message and " तक " in user_message)
    if any(kw in user_lower for kw in journey_keywords) and has_route_markers:
        return {
            "intent": "train_journey",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for train status patterns - multi-language support
    train_keywords = [
        # English
        "train", "running status", "where is", "train status",
        # Hindi
        "ट्रेन", "गाड़ी", "स्थिति", "रेलगाड़ी", "ट्रेन की स्थिति", "गाड़ी की स्थिति",
        "ट्रेन स्टेटस", "रनिंग स्टेटस", "कहां है", "कहाँ है",
        # Kannada
        "ರೈಲು", "ಸ್ಥಿತಿ", "ರೈಲು ಸ್ಥಿತಿ", "ಎಲ್ಲಿದೆ",
        # Tamil
        "ரயில்", "நிலை", "ரயில் நிலை", "எங்கே",
        # Telugu
        "రైలు", "స్థితి", "రైలు స్థితి", "ఎక్కడ",
        # Bengali
        "ট্রেন", "অবস্থা", "ট্রেনের অবস্থা", "কোথায়",
        # Marathi
        "ट्रेन", "स्थिती", "गाडी", "ट्रेनची स्थिती",
        # Odia
        "ଟ୍ରେନ୍", "ଅବସ୍ଥା", "ଗାଡ଼ି", "ରେଳଗାଡ଼ି",
        # Punjabi
        "ਟ੍ਰੇਨ", "ਸਟੇਟਸ", "ਗੱਡੀ", "ਰੇਲਗੱਡੀ", "ਟ੍ਰੇਨ ਸਟੇਟਸ", "ਕਿੱਥੇ",
        "ਰਨਿੰਗ ਸਟੇਟਸ", "ਟ੍ਰੇਨ ਦਾ ਸਟੇਟਸ", "ਗੱਡੀ ਦਾ ਸਟੇਟਸ",
        # Gujarati
        "ટ્રેન", "સ્ટેટસ", "ગાડી", "ટ્રેન સ્ટેટસ", "ક્યાં છે",
        "રનિંગ સ્ટેટસ", "ટ્રેનની સ્થિતિ",
        # Malayalam
        "ട്രെയിൻ", "സ്റ്റാറ്റസ്", "തീവണ്ടി", "ട്രെയിൻ സ്റ്റാറ്റസ്", "എവിടെ",
    ]
    if any(kw in user_lower for kw in train_keywords) or any(kw in user_message for kw in train_keywords):
        train_num = extract_train_number(user_message)
        if train_num:
            return {
                "intent": "train_status",
                "intent_confidence": 0.9,
                "extracted_entities": {"train_number": train_num},
                "current_query": user_message,
                "detected_language": detected_lang,
                "error": None,
            }

    # Check for image generation patterns
    image_keywords = [
        # English
        "generate image", "create image", "make image", "draw",
        "generate picture", "create picture", "make picture",
        "generate a", "create a picture", "image of",
        # Hindi
        "चित्र बनाओ", "तस्वीर बनाओ", "इमेज बनाओ", "फोटो बनाओ",
        "ड्रॉ करो", "पिक्चर बनाओ",
        # Bengali
        "ছবি তৈরি করো", "ছবি বানাও", "ইমেজ বানাও",
        # Tamil
        "படம் உருவாக்கு", "படம் வரை", "இமேஜ் உருவாக்கு",
        # Telugu
        "చిత్రం సృష్టించు", "బొమ్మ వేయి", "ఇమేజ్ చేయి",
        # Kannada
        "ಚಿತ್ರ ಮಾಡಿ", "ಚಿತ್ರ ಬಿಡಿಸಿ", "ಇಮೇಜ್ ಮಾಡಿ",
        # Malayalam
        "ചിത്രം സൃഷ്ടിക്കൂ", "ചിത്രം വരയ്ക്കൂ", "ഇമേജ് ഉണ്ടാക്കൂ",
        # Gujarati
        "ચિત્ર બનાવો", "તસવીર બનાવો", "ઇમેજ બનાવો",
        # Marathi
        "चित्र बनवा", "फोटो बनवा", "इमेज बनवा",
        # Punjabi
        "ਤਸਵੀਰ ਬਣਾਓ", "ਚਿੱਤਰ ਬਣਾਓ", "ਇਮੇਜ਼ ਬਣਾਓ",
        # Odia
        "ଚିତ୍ର ତିଆରି କର", "ଛବି ତିଆରି କର", "ଇମେଜ୍ ତିଆରି କର",
    ]
    if any(kw in user_lower for kw in image_keywords):
        return {
            "intent": "image",
            "intent_confidence": 0.9,
            "extracted_entities": {"image_prompt": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for metro patterns
    metro_keywords = [
        # English
        "metro", "dmrc", "delhi metro", "metro fare", "metro ticket",
        "bangalore metro", "mumbai metro", "kolkata metro", "chennai metro",
        # Hindi
        "मेट्रो", "मेट्रो किराया", "मेट्रो टिकट", "मेट्रो स्टेशन",
        # Bengali
        "মেট্রো", "মেট্রো ভাড়া", "মেট্রো টিকিট",
        # Tamil
        "மெட்ரோ", "மெட்ரோ கட்டணம்", "மெட்ரோ டிக்கெட்",
        # Telugu
        "మెట్రో", "మెట్రో ఛార్జ్", "మెట్రో టికెట్",
        # Kannada
        "ಮೆಟ್ರೋ", "ಮೆಟ್ರೋ ದರ", "ಮೆಟ್ರೋ ಟಿಕೆಟ್", "ನಮ್ಮ ಮೆಟ್ರೋ",
        # Malayalam
        "മെട്രോ", "മെട്രോ നിരക്ക്", "മെട്രോ ടിക്കറ്റ്", "കൊച്ചി മെട്രോ",
        # Gujarati
        "મેટ્રો", "મેટ્રો ભાડું", "મેટ્રો ટિકિટ",
        # Marathi
        "मेट्रो", "मेट्रो भाडे", "मेट्रो तिकीट",
        # Punjabi
        "ਮੈਟਰੋ", "ਮੈਟਰੋ ਕਿਰਾਇਆ", "ਮੈਟਰੋ ਟਿਕਟ",
        # Odia
        "ମେଟ୍ରୋ", "ମେଟ୍ରୋ ଭଡ଼ା", "ମେଟ୍ରୋ ଟିକେଟ୍",
    ]
    if any(kw in user_lower for kw in metro_keywords):
        return {
            "intent": "metro_ticket",
            "intent_confidence": 0.85,
            "extracted_entities": {"query": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }
    
    # Check for word game patterns
    word_game_keywords = [
        # English
        "word game", "play a game", "anagram", "word puzzle",
        # Hindi
        "शब्द खेल", "खेल खेलो", "वर्ड गेम", "गेम खेलो", "पहेली",
        # Bengali
        "শব্দ খেলা", "খেলা খেলো", "ওয়ার্ড গেম",
        # Tamil
        "வார்த்தை விளையாட்டு", "விளையாட்டு", "ஒர்ட் கேம்",
        # Telugu
        "పదాల ఆట", "ఆట ఆడు", "వర్డ్ గేమ్",
        # Kannada
        "ಪದ ಆಟ", "ಆಟ ಆಡಿ", "ವರ್ಡ್ ಗೇಮ್",
        # Malayalam
        "വാക്ക് കളി", "കളിക്കാം", "വേർഡ് ഗെയിം",
        # Gujarati
        "શબ્દ રમત", "રમત રમો", "વર્ડ ગેમ",
        # Marathi
        "शब्द खेळ", "खेळ खेळा", "वर्ड गेम",
        # Punjabi
        "ਸ਼ਬਦ ਖੇਡ", "ਖੇਡ ਖੇਡੋ", "ਵਰਡ ਗੇਮ",
        # Odia
        "ଶବ୍ଦ ଖେଳ", "ଖେଳ ଖେଳ", "ୱାର୍ଡ ଗେମ୍",
    ]
    if any(kw in user_lower for kw in word_game_keywords):
        return {
            "intent": "word_game",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for database query patterns
    db_query_keywords = ["database", "query", "users", "orders", "registered", "total number"]
    if any(kw in user_lower for kw in db_query_keywords):
        return {
            "intent": "db_query",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }
    
    # Check for reminder patterns
    reminder_keywords = [
        # English
        "remind", "reminder", "set alarm", "alarm me", "set reminder",
        # Hindi
        "याद दिलाओ", "याद करवाओ", "रिमाइंडर", "अलार्म लगाओ", "याद दिलाना",
        # Bengali
        "মনে করিয়ে দাও", "রিমাইন্ডার", "অ্যালার্ম সেট করো",
        # Tamil
        "நினைவூட்டு", "ரிமைண்டர்", "அலாரம் வை",
        # Telugu
        "గుర్తు చేయి", "రిమైండర్", "అలారం పెట్టు",
        # Kannada
        "ನೆನಪಿಸು", "ರಿಮೈಂಡರ್", "ಅಲಾರ್ಮ್ ಹಾಕು",
        # Malayalam
        "ഓർമ്മിപ്പിക്കൂ", "റിമൈൻഡർ", "അലാറം സെറ്റ് ചെയ്യൂ",
        # Gujarati
        "યાદ કરાવો", "રિમાઇન્ડર", "અલાર્મ સેટ કરો",
        # Marathi
        "आठवण करून द्या", "रिमाइंडर", "अलार्म लावा",
        # Punjabi
        "ਯਾਦ ਕਰਵਾਓ", "ਰਿਮਾਈਂਡਰ", "ਅਲਾਰਮ ਲਗਾਓ",
        # Odia
        "ମନେ ପକାଇଦିଅ", "ରିମାଇଣ୍ଡର", "ଆଲାର୍ମ ସେଟ୍ କର",
    ]
    if any(kw in user_lower for kw in reminder_keywords):
        return {
            "intent": "set_reminder",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    cricket_score_keywords = [
        # English
        "cricket score", "live score", "scorecard", "match score",
        "ipl score", "wpl score", "t20 score", "odi score", "test score",
        "cricket live", "live cricket", "score update", "runs", "overs",
        # Hindi
        "क्रिकेट स्कोर", "लाइव स्कोर", "स्कोरकार्ड", "मैच स्कोर",
        "आईपीएल स्कोर", "डब्ल्यूपीएल स्कोर", "स्कोर अपडेट", "रन", "ओवर",
    ]
    if any(kw in user_lower for kw in cricket_score_keywords) or any(kw in user_message for kw in cricket_score_keywords):
        return {
            "intent": "cricket_score",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    govt_jobs_keywords = [
        # English
        "government jobs", "govt jobs", "sarkari job", "sarkari naukri",
        "job vacancy", "job openings", "recruitment", "bharti", "vacancy",
        "central government jobs", "state government jobs",
        # Hindi
        "सरकारी नौकरी", "सरकारी जॉब", "भर्ती", "वैकेंसी", "नौकरी",
        "केंद्र सरकार नौकरी", "राज्य सरकार नौकरी",
    ]
    if any(kw in user_lower for kw in govt_jobs_keywords) or any(kw in user_message for kw in govt_jobs_keywords):
        return {
            "intent": "govt_jobs",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    farmer_schemes_keywords = [
        # English
        "farmer scheme", "farmers scheme", "farmer subsidy", "farmers subsidy",
        "kisan scheme", "kisan yojana", "krishi yojana", "agri subsidy",
        "agriculture scheme", "agriculture subsidy", "pm kisan", "pm-kisan",
        # Hindi
        "किसान योजना", "किसान सब्सिडी", "कृषि योजना", "कृषि सब्सिडी", "किसान सहायता",
    ]
    farmer_scheme_patterns = [
        r"\b(farmer|farmers|kisan|kisaan|krishi|agri|agriculture)\b.*\b(scheme|yojana|subsidy|subsidies|benefit|grant)\b",
        r"\b(scheme|yojana|subsidy|subsidies|benefit|grant)\b.*\b(farmer|farmers|kisan|kisaan|krishi|agri|agriculture)\b",
        r"(किसान|कृषि).*?(योजना|सब्सिडी|सहायता|लाभ)",
    ]
    if (
        any(kw in user_lower for kw in farmer_schemes_keywords)
        or any(kw in user_message for kw in farmer_schemes_keywords)
        or any(re.search(pattern, user_lower) for pattern in farmer_scheme_patterns)
        or any(re.search(pattern, user_message) for pattern in farmer_scheme_patterns)
    ):
        return {
            "intent": "farmer_schemes",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    govt_schemes_keywords = [
        # English
        "government schemes", "govt schemes", "government scheme",
        "sarkari yojana", "yojana", "scheme", "welfare scheme",
        "central schemes", "state schemes",
        # Hindi
        "सरकारी योजना", "योजना", "स्कीम", "कल्याण योजना",
    ]
    if any(kw in user_lower for kw in govt_schemes_keywords) or any(kw in user_message for kw in govt_schemes_keywords):
        return {
            "intent": "govt_schemes",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    free_audio_keywords = [
        "free audio", "free music", "royalty free music", "royalty free audio",
        "audio library", "free songs", "free mp3", "free bhakti songs",
        "फ्री ऑडियो", "फ्री म्यूजिक", "रॉयल्टी फ्री", "फ्री गाने",
    ]
    if any(kw in user_lower for kw in free_audio_keywords) or any(kw in user_message for kw in free_audio_keywords):
        return {
            "intent": "free_audio_sources",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    travel_plan_keywords = [
        "road trip", "roadtrip", "car trip", "trip plan", "travel plan",
        "route plan", "journey plan", "road trip plan", "car road trip",
        "यात्रा", "यात्रा योजना", "ट्रिप", "ट्रिप प्लान", "रोड ट्रिप",
        "कार ट्रिप", "यात्रा प्लान",
    ]
    if any(kw in user_lower for kw in travel_plan_keywords) or any(kw in user_message for kw in travel_plan_keywords):
        if any(marker in user_lower for marker in [" from ", " to ", " se ", " tak "]) or any(marker in user_message for marker in [" से ", " तक "]):
            return {
                "intent": "chat",
                "intent_confidence": 0.9,
                "extracted_entities": {},
                "current_query": user_message,
                "detected_language": detected_lang,
                "error": None,
            }

    # Check for "near me" patterns (food should take priority over events)
    local_search_indicators = [
        # English
        "near me", "nearby", "nearest", "around me", "close to me", "near here",
        # Hindi
        "मेरे पास", "मेरे आसपास", "पास में", "नजदीक", "आसपास", "मेरे नजदीक",
        "mere paas", "mere aaspaas", "paas mein", "nazdeek", "aaspaas",
        # Kannada
        "ನನ್ನ ಹತ್ತಿರ", "ಹತ್ತಿರ", "ಸಮೀಪ", "ಹತ್ತಿರದ", "ನನ್ನ ಬಳಿ",
        "nanna hattira", "hattira", "sameepa",
        # Tamil
        "என் அருகில்", "அருகில்", "பக்கத்தில்", "என் பக்கத்தில்",
        "en arukil", "arukil", "pakkathil",
        # Telugu
        "నా దగ్గర", "దగ్గర", "సమీపంలో", "నాకు దగ్గర్లో",
        "naa daggara", "daggara", "sameepamlo",
        # Bengali
        "আমার কাছে", "কাছে", "কাছাকাছি",
        # Marathi
        "माझ्या जवळ", "जवळ", "जवळपास",
        # Odia
        "ମୋ ପାଖରେ", "ପାଖରେ", "ନିକଟରେ",
        # Malayalam (ADDED)
        "എന്റെ അടുത്ത്", "അടുത്ത്", "സമീപം", "എന്റെ സമീപം",
        # Gujarati (ADDED)
        "મારી નજીક", "નજીક", "પાસે", "મારી પાસે",
        # Punjabi (ADDED)
        "ਮੇਰੇ ਨੇੜੇ", "ਨੇੜੇ", "ਨਜ਼ਦੀਕ", "ਮੇਰੇ ਕੋਲ",
    ]
    events_near_me_keywords = [
        # English
        "event", "events", "ipl", "match", "matches", "concert", "concerts",
        "comedy", "ticket", "tickets", "cricket", "football",
        "rcb", "csk", "mi", "kkr", "dc", "srh", "rr", "pbks", "gt", "lsg",
        # Hindi
        "इवेंट", "कार्यक्रम", "मैच", "क्रिकेट", "कॉन्सर्ट", "शो", "टिकट",
        "कॉमेडी", "आईपीएल", "फुटबॉल", "घटना",
        # Kannada
        "ಘಟನೆ", "ಘಟನೆಗಳು", "ಕಾರ್ಯಕ್ರಮ", "ಪಂದ್ಯ", "ಕ್ರಿಕೆಟ್", "ಸಂಗೀತ",
        "ಶೋ", "ಟಿಕೆಟ್", "ಕಾಮಿಡಿ", "ಐಪಿಎಲ್", "ಫುಟ್ಬಾಲ್",
        # Tamil
        "நிகழ்வு", "நிகழ்ச்சி", "போட்டி", "கிரிக்கெட்", "இசை", "டிக்கெட்",
        "காமெடி", "ஐபிஎல்", "கால்பந்து",
        # Telugu
        "కార్యక్రమం", "మ్యాచ్", "క్రికెట్", "కాన్సర్ట్", "షో", "టికెట్",
        "కామెడీ", "ఐపీఎల్", "ఫుట్‌బాల్",
        # Bengali
        "ইভেন্ট", "অনুষ্ঠান", "ম্যাচ", "ক্রিকেট", "কনসার্ট", "শো", "টিকিট",
        # Marathi
        "कार्यक्रम", "सामना", "क्रिकेट", "शो", "तिकीट",
        # Odia
        "କାର୍ଯ୍ୟକ୍ରମ", "ମ୍ୟାଚ୍", "କ୍ରିକେଟ୍", "ଶୋ", "ଟିକେଟ୍",
        # Malayalam (ADDED)
        "ഇവന്റ്", "പരിപാടി", "മത്സരം", "ക്രിക്കറ്റ്", "കച്ചേരി", "ഷോ", "ടിക്കറ്റ്",
        "കോമഡി", "ഐപിഎൽ", "ഫുട്ബോൾ",
        # Gujarati (ADDED)
        "ઇવેન્ટ", "કાર્યક્રમ", "મેચ", "ક્રિકેટ", "કોન્સર્ટ", "શો", "ટિકિટ",
        "કોમેડી", "આઈપીએલ", "ફૂટબોલ",
        # Punjabi (ADDED)
        "ਇਵੈਂਟ", "ਪ੍ਰੋਗਰਾਮ", "ਮੈਚ", "ਕ੍ਰਿਕਟ", "ਕਨਸਰਟ", "ਸ਼ੋਅ", "ਟਿਕਟ",
        "ਕਾਮੇਡੀ", "ਆਈਪੀਐਲ", "ਫੁੱਟਬਾਲ",
    ]
    food_near_me_keywords = [
        "restaurant", "restaurants", "food", "eat", "dinner", "lunch", "breakfast",
        "cafe", "coffee", "pizza", "burger", "biryani", "dosa", "idli", "chinese",
        "north indian", "south indian", "italian", "thai", "japanese", "korean",
        "ice cream", "dessert", "bakery", "fast food", "street food", "seafood",
        "zomato", "swiggy",
        # Hindi
        "खाना", "रेस्टोरेंट", "होटल",
        # Kannada
        "ಊಟ", "ಹೋಟೆಲ್",
        # Malayalam (ADDED)
        "ഭക്ഷണം", "റെസ്റ്റോറന്റ്", "ഹോട്ടൽ", "ഊണ്",
        # Gujarati (ADDED)
        "ખાવાનું", "રેસ્ટોરન્ટ", "હોટલ", "જમવાનું",
        # Punjabi (ADDED)
        "ਖਾਣਾ", "ਰੈਸਟੋਰੈਂਟ", "ਹੋਟਲ", "ਭੋਜਨ",
    ]
    has_near_me = any(ind in user_lower for ind in local_search_indicators)
    has_event_keyword = any(kw in user_lower for kw in events_near_me_keywords)
    has_food_keyword = any(kw in user_lower for kw in food_near_me_keywords)

    if has_near_me and has_food_keyword:
        # Treat food/restaurant "near me" as local search to fetch real places
        search_term = user_lower
        for ind in local_search_indicators:
            search_term = search_term.replace(ind, "").strip()
        for prefix in ["find", "search", "show", "get", "where is", "where are", "looking for", "i need", "i want"]:
            if search_term.startswith(prefix):
                search_term = search_term[len(prefix):].strip()

        logger.info(f"Detected food with 'near me' indicator, routing to local_search")
        return {
            "intent": "local_search",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "search_query": search_term or user_message,
                "location": "",  # Empty - will trigger location request
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    if has_near_me and has_event_keyword:
        logger.info(f"Detected events with 'near me' indicator, routing to events")
        return {
            "intent": "events",
            "intent_confidence": 0.95,
            "extracted_entities": {"query": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # IMPORTANT: Check for "near me" patterns - for general local search
    # This ensures location-based queries are handled correctly
    if has_near_me:
        # Extract search term by removing the indicator
        search_term = user_lower
        for ind in local_search_indicators:
            search_term = search_term.replace(ind, "").strip()
        # Remove common prefixes
        for prefix in ["find", "search", "show", "get", "where is", "where are", "looking for", "i need", "i want"]:
            if search_term.startswith(prefix):
                search_term = search_term[len(prefix):].strip()

        logger.info(f"Detected local_search with 'near me' indicator (early check), search_term: {search_term}")
        return {
            "intent": "local_search",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "search_query": search_term or user_message,
                "location": "",  # Empty - will trigger location request
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for food/restaurant patterns
    place_food_keywords = [
        "restaurant", "restaurants",
        "restraunt", "restraunts", "resturant", "resturants", "restarant",
        "restraurant", "restaurent", "restaurents", "restrant", "restrants",
        "cafe", "cafes", "coffee shop", "dhaba", "eatery", "food court", "mess",
        "hotel", "hotels",
    ]
    food_keywords = [
        "restaurant", "restaurants", "food", "order food", "hungry",
        # Common misspellings
        "restraunt", "restraunts", "resturant", "resturants", "restarant",
        "restraurant", "restaurent", "restaurents", "restrant", "restrants",
        "zomato", "swiggy", "food delivery", "eat", "dinner", "lunch",
        "breakfast", "biryani", "pizza", "burger", "dosa", "idli",
        "chinese food", "north indian", "south indian", "italian",
        "thai food", "japanese", "korean", "cafe", "coffee shop",
        "ice cream", "dessert", "bakery", "fast food", "street food",
        "vegetarian restaurant", "non veg", "seafood",
        # Hindi
        "खाना", "रेस्टोरेंट", "रेस्तरां", "होटल", "भोजन", "खाना आर्डर",
        "भूख", "भूखा", "खाना खाना", "बिरयानी", "पिज़्ज़ा", "बर्गर",
        "डोसा", "इडली", "रोटी", "दाल", "सब्जी", "पनीर", "चिकन",
        "मटन", "नाश्ता", "दोपहर का खाना", "रात का खाना", "चाय", "कॉफी",
        "मिठाई", "आइसक्रीम", "समोसा", "पकौड़ा", "चाट", "पानी पूरी",
        # Kannada
        "ಊಟ", "ಹೋಟೆಲ್", "ರೆಸ್ಟೋರೆಂಟ್", "ಆಹಾರ", "ತಿನ್ನು", "ಹಸಿವು",
        "ಬಿರಿಯಾನಿ", "ದೋಸೆ", "ಇಡ್ಲಿ", "ಚಪಾತಿ", "ರೊಟ್ಟಿ", "ಅನ್ನ",
        "ಸಾಂಬಾರ್", "ರಸಂ", "ಪಲ್ಯ", "ಚಿಕನ್", "ಮಟನ್", "ಮೀನು",
        "ತಿಂಡಿ", "ಕಾಫಿ", "ಚಹಾ", "ಸಿಹಿ", "ಐಸ್ ಕ್ರೀಮ್",
        # Odia
        "ଖାଇବା", "ହୋଟେଲ", "ରେଷ୍ଟୁରାଣ୍ଟ", "ଭୋଜନ", "ଖାଦ୍ୟ", "ଭୋକ",
        "ବିରିୟାନି", "ଡୋସା", "ଇଡଲି", "ରୁଟି", "ଭାତ", "ଡାଲି", "ତରକାରୀ",
        "ଚିକେନ", "ମଟନ", "ମାଛ", "ଜଳଖିଆ", "ଚା", "କଫି", "ମିଠା",
        # Tamil
        "உணவு", "உணவகம்", "ஹோட்டல்", "சாப்பாடு", "பசி", "தோசை",
        "இட்லி", "பிரியாணி", "சாம்பார்", "ரசம்", "சிக்கன்", "மட்டன்",
        # Telugu
        "భోజనం", "హోటల్", "రెస్టారెంట్", "ఆకలి", "తిను", "బిర్యానీ",
        "దోశ", "ఇడ్లీ", "చికెన్", "మటన్", "అన్నం", "సాంబార్",
        # Bengali
        "খাবার", "রেস্তোরাঁ", "হোটেল", "খিদে", "বিরিয়ানি", "ডোসা",
        "ইডলি", "চিকেন", "মাটন", "মাছ", "ভাত", "ডাল", "মিষ্টি",
        # Marathi
        "जेवण", "हॉटेल", "रेस्टॉरंट", "भूक", "बिर्याणी", "डोसा",
        "इडली", "चिकन", "मटण", "भात", "आमटी", "गोड",
        # Malayalam (ADDED)
        "ഭക്ഷണം", "റെസ്റ്റോറന്റ്", "ഹോട്ടൽ", "വിശപ്പ്", "ബിരിയാണി",
        "ദോശ", "ഇഡ്ഡലി", "ചിക്കൻ", "മട്ടൺ", "ചോറ്", "സാമ്പാർ",
        # Gujarati (ADDED)
        "ખાવાનું", "રેસ્ટોરન્ટ", "હોટલ", "ભૂખ", "બિરયાની",
        "ઢોસા", "ઇડલી", "ચિકન", "મટન", "ભાત", "દાળ",
        # Punjabi (ADDED)
        "ਖਾਣਾ", "ਰੈਸਟੋਰੈਂਟ", "ਹੋਟਲ", "ਭੁੱਖ", "ਬਿਰਿਆਨੀ",
        "ਡੋਸਾ", "ਇਡਲੀ", "ਚਿਕਨ", "ਮਟਨ", "ਚਾਵਲ", "ਦਾਲ",
        # Restaurant detail queries - known restaurant names
        "meghana foods", "truffles", "empire restaurant", "mtr ", "vidyarthi bhavan",
        "bademiya", "cafe leopold", "swati snacks", "britannia",
        "karim's", "paranthe wali", "bukhara", "haldiram",
        "saravana bhavan", "murugan idli", "anjappar",
        "paradise biryani", "bawarchi", "shah ghouse",
        "dalma", "odisha hotel", "hare krishna", "truptee",
        # Detail query patterns
        "details of", "info about", "more about",
    ]
    if any(kw in user_lower for kw in place_food_keywords):
        return {
            "intent": "local_search",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "search_query": user_message,
                "location": "",
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    if any(kw in user_lower for kw in food_keywords) and any(
        prep in user_lower for prep in [" in ", " near ", " at ", " around "]
    ):
        return {
            "intent": "local_search",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "search_query": user_message,
                "location": "",
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    if any(kw in user_lower for kw in food_keywords):
        return {
            "intent": "food_order",
            "intent_confidence": 0.95,
            "extracted_entities": {"query": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for events/tickets patterns (IPL, concerts, comedy shows)
    events_keywords = [
        # IPL/Cricket - team codes and variations
        "ipl", "ipl match", "ipl matches", "cricket match", "cricket ticket",
        "rcb", "csk", "mi ", "kkr", "dc ", "srh", "rr ", "pbks", "gt ", "lsg",
        "rcb match", "csk match", "mi match", "kkr match", "dc match",
        "srh match", "rr match", "pbks match", "gt match", "lsg match",
        "royal challengers", "chennai super kings", "mumbai indians",
        "kolkata knight riders", "delhi capitals", "sunrisers",
        "rajasthan royals", "punjab kings", "gujarat titans", "lucknow super giants",
        # Concerts
        "concert", "live show", "music show", "arijit singh", "coldplay", "ar rahman",
        "diljit", "diljit dosanjh", "neha kakkar", "shreya ghoshal",
        # Comedy
        "comedy show", "standup", "stand-up comedy", "comedian",
        "zakir khan", "biswa", "kenny sebastian", "anubhav bassi", "samay raina",
        # General events
        "book ticket", "event ticket", "upcoming events", "football match", "isl match",
        "events in", "shows in", "matches in", "tickets for",
    ]
    if any(kw in user_lower for kw in events_keywords):
        return {
            "intent": "events",
            "intent_confidence": 0.95,
            "extracted_entities": {"query": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for stock price patterns
    stock_keywords = [
        "stock price", "share price", "stock quote", "share quote", "stock rate",
        "stock value", "share value", "stock today", "share today",
        "portfolio", "stocks",
        "शेयर भाव", "स्टॉक प्राइस", "शेयर प्राइस", "स्टॉक भाव",
    ]
    if any(kw in user_lower for kw in stock_keywords):
        return {
            "intent": "stock_price",
            "intent_confidence": 0.9,
            "extracted_entities": {"stock_name": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for news patterns
    news_keywords = [
        # English
        "news", "headlines", "latest news", "breaking news",
        # Hindi
        "समाचार", "खबर", "खबरें", "ताजा खबर", "न्यूज़", "ब्रेकिंग न्यूज़",
        # Bengali
        "সংবাদ", "খবর", "সর্বশেষ খবর", "নিউজ",
        # Tamil
        "செய்தி", "செய்திகள்", "சமீபத்திய செய்தி", "நியூஸ்",
        # Telugu
        "వార్తలు", "వార్త", "తాజా వార్తలు", "న్యూస్",
        # Kannada
        "ಸುದ್ದಿ", "ಸುದ್ದಿಗಳು", "ತಾಜಾ ಸುದ್ದಿ", "ನ್ಯೂಸ್",
        # Malayalam
        "വാർത്ത", "വാർത്തകൾ", "പുതിയ വാർത്ത", "ന്യൂസ്",
        # Gujarati
        "સમાચાર", "ખબર", "તાજા સમાચાર", "ન્યૂઝ",
        # Marathi
        "बातम्या", "बातमी", "ताज्या बातम्या", "न्यूज",
        # Punjabi
        "ਖ਼ਬਰਾਂ", "ਖ਼ਬਰ", "ਤਾਜ਼ਾ ਖ਼ਬਰਾਂ", "ਨਿਊਜ਼",
        # Odia
        "ସମାଚାର", "ଖବର", "ତାଜା ଖବର", "ନ୍ୟୁଜ୍",
    ]
    if any(kw in user_lower for kw in news_keywords):
        return {
            "intent": "get_news",
            "intent_confidence": 0.9,
            "extracted_entities": {"news_query": user_message.replace("news about", "").strip()},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for fact-check patterns
    fact_check_keywords = [
        # English patterns
        "fact check", "check fact", "is this true", "is this real",
        "is this correct", "verify this", "true or false",
        "fact or fiction", "myth or fact", "fake or real",
        "is this fake", "fake news", "verify news",
        "is it true", "is it fake", "is it real",
        "can you verify", "please verify", "verify claim",
        # Hindi patterns
        "sach hai", "jhooth hai", "asli hai", "nakli hai",
        "fake hai", "real hai", "verify karo", "check karo",
        "yeh sach hai", "kya yeh sach", "kya yeh real",
        "सच है", "झूठ है", "असली है", "नकली है", "फेक है",
        # Bengali
        "সত্য কি", "মিথ্যা কি", "আসল কি", "নকল কি", "ফেক নিউজ",
        # Tamil
        "உண்மையா", "பொய்யா", "உண்மை சரிபார்", "ஃபேக் நியூஸ்",
        # Telugu
        "నిజమా", "అబద్ధమా", "ఫేక్ న్యూస్", "నిజం చెక్",
        # Kannada
        "ನಿಜವಾ", "ಸುಳ್ಳಾ", "ಫೇಕ್ ನ್ಯೂಸ್", "ನಿಜ ಪರಿಶೀಲನೆ",
        # Malayalam
        "സത്യമാണോ", "കള്ളമാണോ", "ഫേക്ക് ന്യൂസ്", "സത്യം പരിശോധിക്കൂ",
        # Gujarati
        "સાચું છે", "ખોટું છે", "ફેક ન્યૂઝ", "સત્ય તપાસો",
        # Marathi
        "खरे आहे", "खोटे आहे", "फेक न्यूज", "सत्य तपासा",
        # Punjabi
        "ਸੱਚ ਹੈ", "ਝੂਠ ਹੈ", "ਫੇਕ ਨਿਊਜ਼", "ਸੱਚ ਚੈੱਕ",
        # Odia
        "ସତ କି", "ମିଛ କି", "ଫେକ୍ ନ୍ୟୁଜ୍", "ସତ୍ୟ ଯାଞ୍ଚ",
    ]
    if any(kw in user_lower for kw in fact_check_keywords):
        return {
            "intent": "fact_check",
            "intent_confidence": 0.9,
            "extracted_entities": {"fact_check_claim": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Check for weather patterns
    weather_keywords = ["weather", "temperature", "mausam"]
    if any(kw in user_lower for kw in weather_keywords):
        # Extract city if present (pattern: "weather in <city>" or "<city> weather")
        city = ""

        # Words that are NOT city names
        non_city_words = [
            "the", "today", "tomorrow", "current", "what", "how", "whats", "hows",
            "is", "now", "please", "tell", "me", "show", "get", "check", "a", "an",
            "weather", "temperature", "mausam", "kaisa", "hai", "aaj", "ka", "kal"
        ]

        # Pattern 1: "weather in/of/for/at <city>" - most specific
        city_match = re.search(r"weather\s+(?:in|of|for|at)\s+([a-zA-Z][a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+now|\?|$)", user_lower)
        if city_match:
            potential = city_match.group(1).strip()
            # Make sure it's not just filler words
            if potential and potential not in non_city_words:
                city = potential

        # Pattern 2: "temperature in/of/for/at <city>"
        if not city:
            city_match = re.search(r"temperature\s+(?:in|of|for|at)\s+([a-zA-Z][a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+now|\?|$)", user_lower)
            if city_match:
                potential = city_match.group(1).strip()
                if potential and potential not in non_city_words:
                    city = potential

        # Pattern 3: "<city> weather" - but be careful not to match "today weather"
        if not city:
            city_match = re.search(r"^([a-zA-Z][a-zA-Z\s]+?)\s+weather", user_lower)
            if city_match:
                potential = city_match.group(1).strip()
                # Filter out common non-city phrases
                if potential and potential not in non_city_words and not any(w in potential for w in ["what", "how", "the"]):
                    city = potential

        # Pattern 4: "weather today in <city>" or "what is the weather today in <city>"
        if not city:
            city_match = re.search(r"(?:weather|temperature)\s+(?:today|tomorrow|now)\s+(?:in|of|for|at)\s+([a-zA-Z][a-zA-Z\s]+?)(?:\?|$)", user_lower)
            if city_match:
                potential = city_match.group(1).strip()
                if potential and potential not in non_city_words:
                    city = potential

        return {
            "intent": "weather",
            "intent_confidence": 0.9,
            "extracted_entities": {"city": city.title() if city else ""},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # NOTE: "near me" check moved earlier in the file (before food/events checks)
    # to ensure location-based queries are handled correctly

    # Check for astro patterns - more specific matching
    user_lower = user_message.lower()

    # Tarot reading
    tarot_keywords = [
        # English
        "tarot", "tarot card", "tarot reading", "pick a card", "card reading",
        # Hindi
        "टैरो", "टैरो कार्ड", "टैरो रीडिंग", "कार्ड रीडिंग", "भाग्य कार्ड",
        # Bengali
        "ট্যারো", "ট্যারো কার্ড", "কার্ড রিডিং",
        # Tamil
        "டாரோ", "டாரோ கார்ட்", "கார்ட் ரீடிங்",
        # Telugu
        "టారో", "టారో కార్డ్", "కార్డ్ రీడింగ్",
        # Kannada
        "ಟ್ಯಾರೋ", "ಟ್ಯಾರೋ ಕಾರ್ಡ್", "ಕಾರ್ಡ್ ರೀಡಿಂಗ್",
        # Malayalam
        "ടാരോ", "ടാരോ കാർഡ്", "കാർഡ് റീഡിംഗ്",
        # Gujarati
        "ટેરો", "ટેરો કાર્ડ", "કાર્ડ રીડિંગ",
        # Marathi
        "टॅरो", "टॅरो कार्ड", "कार्ड रीडिंग",
        # Punjabi
        "ਟੈਰੋ", "ਟੈਰੋ ਕਾਰਡ", "ਕਾਰਡ ਰੀਡਿੰਗ",
        # Odia
        "ଟାରୋ", "ଟାରୋ କାର୍ଡ", "କାର୍ଡ ରିଡିଂ",
    ]
    if any(kw in user_lower for kw in tarot_keywords):
        # Extract tarot question and spread type
        tarot_question = ""
        spread_type = "three_card"  # default

        # Extract question - "tarot for <question>" or "tarot about <question>"
        question_match = re.search(r"(?:tarot|reading)\s+(?:for|about)\s+(?:my\s+)?(.+?)(?:\s*$|\s+using|\s+with)", user_message, re.IGNORECASE)
        if question_match:
            tarot_question = question_match.group(1).strip()

        # Determine spread type
        if "single" in user_lower or "one card" in user_lower:
            spread_type = "single"
        elif "celtic" in user_lower or "full" in user_lower or "detailed" in user_lower or "10 card" in user_lower:
            spread_type = "celtic_cross"
        elif "three" in user_lower or "3 card" in user_lower:
            spread_type = "three_card"

        return {
            "intent": "tarot_reading",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "tarot_question": tarot_question,
                "spread_type": spread_type
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Numerology
    numerology_keywords = [
        # English
        "numerology", "lucky number", "life path number", "name number", "destiny number",
        # Hindi
        "अंक ज्योतिष", "अंकशास्त्र", "भाग्यशाली अंक", "लकी नंबर", "नाम अंक",
        # Bengali
        "সংখ্যাতত্ত্ব", "ভাগ্যবান সংখ্যা", "নাম সংখ্যা",
        # Tamil
        "எண் கணிதம்", "அதிர்ஷ்ட எண்", "பெயர் எண்",
        # Telugu
        "సంఖ్యాశాస్త్రం", "అదృష్ట సంఖ్య", "పేరు సంఖ్య",
        # Kannada
        "ಸಂಖ್ಯಾಶಾಸ್ತ್ರ", "ಅದೃಷ್ಟ ಸಂಖ್ಯೆ", "ಹೆಸರು ಸಂಖ್ಯೆ",
        # Malayalam
        "സംഖ്യാശാസ്ത്രം", "ഭാഗ്യ നമ്പർ", "പേര് നമ്പർ",
        # Gujarati
        "અંક જ્યોતિષ", "ભાગ્યશાળી નંબર", "નામ નંબર",
        # Marathi
        "अंकशास्त्र", "भाग्यशाली अंक", "नाव अंक",
        # Punjabi
        "ਅੰਕ ਜੋਤਿਸ਼", "ਲੱਕੀ ਨੰਬਰ", "ਨਾਮ ਨੰਬਰ",
        # Odia
        "ଅଙ୍କ ଜ୍ୟୋତିଷ", "ଭାଗ୍ୟ ନମ୍ବର", "ନାମ ନମ୍ବର",
    ]
    if any(kw in user_lower for kw in numerology_keywords):
        # Extract name from message
        extracted_name = ""
        # Pattern: "numerology for <name>" or "numerology of <name>"
        name_match = re.search(r"numerology\s+(?:for|of)\s+([A-Za-z\s]+?)(?:,|\s+born|\s+\d|$)", user_message, re.IGNORECASE)
        if name_match:
            extracted_name = name_match.group(1).strip()
        else:
            # Pattern: "my numerology - <name>"
            name_match = re.search(r"my\s+numerology\s*[-:]\s*([A-Za-z\s]+?)(?:,|\s+born|\s+\d|$)", user_message, re.IGNORECASE)
            if name_match:
                extracted_name = name_match.group(1).strip()

        # Extract birth date if present
        extracted_date = ""
        date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
        if date_match:
            extracted_date = date_match.group(1)

        return {
            "intent": "numerology",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "name": extracted_name,
                "birth_date": extracted_date
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Kundli matching / compatibility
    kundli_match_keywords = ["kundli match", "kundali match", "gun milan", "marriage compatibility", "compatibility check", "match kundli", "match horoscope"]
    if any(kw in user_lower for kw in kundli_match_keywords):
        # Extract names and DOBs for both persons
        # Pattern: "Match kundli of <name1> (<dob1>) and <name2> (<dob2>)"
        # Pattern: "Compatibility check for <name1> (<dob1>) and <name2> (<dob2>)"

        person1_name = ""
        person1_dob = ""
        person2_name = ""
        person2_dob = ""

        # Try to extract pattern: "name1 (dob1) and name2 (dob2)"
        match = re.search(
            r"(?:of|for|between)\s+([A-Za-z]+)\s*\(?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*\)?\s*(?:and|&)\s*([A-Za-z]+)\s*\(?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*\)?",
            user_message,
            re.IGNORECASE
        )
        if match:
            person1_name = match.group(1).strip()
            person1_dob = match.group(2).strip()
            person2_name = match.group(3).strip()
            person2_dob = match.group(4).strip()
        else:
            # Try simpler pattern: just two dates
            dates = re.findall(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
            if len(dates) >= 2:
                person1_dob = dates[0]
                person2_dob = dates[1]

            # Try to extract names
            names = re.findall(r"([A-Z][a-z]+)\s*(?:\(|\d|and|&)", user_message)
            if len(names) >= 2:
                person1_name = names[0]
                person2_name = names[1]

        return {
            "intent": "kundli_matching",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "person1_name": person1_name,
                "person1_dob": person1_dob,
                "person2_name": person2_name,
                "person2_dob": person2_dob
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Birth chart / Kundli
    birth_chart_keywords = [
        # English
        "birth chart", "kundli", "kundali", "janam patri", "janam kundli", "natal chart", "my chart",
        # Hindi
        "कुंडली", "जन्म कुंडली", "जन्म पत्री", "जन्मपत्रिका", "बर्थ चार्ट",
        # Bengali
        "কুণ্ডলী", "জন্ম কুণ্ডলী", "জন্মপত্রী",
        # Tamil
        "ஜாதகம்", "ஜாதக கட்டம்", "பிறப்பு ஜாதகம்",
        # Telugu
        "కుండలి", "జన్మ కుండలి", "జాతకం",
        # Kannada
        "ಕುಂಡಲಿ", "ಜನ್ಮ ಕುಂಡಲಿ", "ಜಾತಕ",
        # Malayalam
        "കുണ്ഡലി", "ജന്മ കുണ്ഡലി", "ജാതകം",
        # Gujarati
        "કુંડળી", "જન્મ કુંડળી", "જાતક",
        # Marathi
        "कुंडली", "जन्म कुंडली", "पत्रिका",
        # Punjabi
        "ਕੁੰਡਲੀ", "ਜਨਮ ਕੁੰਡਲੀ", "ਜਨਮ ਪੱਤਰੀ",
        # Odia
        "କୁଣ୍ଡଳୀ", "ଜନ୍ମ କୁଣ୍ଡଳୀ", "ଜାତକ",
    ]
    if any(kw in user_lower for kw in birth_chart_keywords):
        # Extract name, birth_date, birth_time, birth_place
        # Pattern: "Kundli for <name> born on <date> at <time> in <place>"

        extracted_name = ""
        extracted_date = ""
        extracted_time = ""
        extracted_place = ""

        # Extract name - "for <name>" or "of <name>"
        name_match = re.search(r"(?:for|of)\s+([A-Za-z]+)\s+(?:born|dob|\d)", user_message, re.IGNORECASE)
        if name_match:
            extracted_name = name_match.group(1).strip()

        # Extract date - various formats
        date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
        if date_match:
            extracted_date = date_match.group(1)

        # Extract time - "at <time> AM/PM" or just time pattern
        time_match = re.search(r"(?:at\s+)?(\d{1,2}[:.]\d{2})\s*(AM|PM|am|pm)?", user_message, re.IGNORECASE)
        if time_match:
            extracted_time = time_match.group(1)
            if time_match.group(2):
                extracted_time += " " + time_match.group(2).upper()

        # Extract place - multiple patterns
        # Pattern 1: "in <place>" or "at <place>"
        place_match = re.search(r"(?:in|at)\s+([A-Za-z][A-Za-z\s]*?)(?:\s*$|\s*,|\s*\d)", user_message, re.IGNORECASE)
        if place_match:
            extracted_place = place_match.group(1).strip()
            # Clean up common suffixes
            extracted_place = re.sub(r"\s+(born|at|on).*$", "", extracted_place, flags=re.IGNORECASE).strip()

        # Pattern 2: Place after AM/PM (e.g., "10:30 AM Delhi")
        if not extracted_place:
            place_after_time = re.search(r"(?:AM|PM|am|pm)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s*$|\s*,)", user_message)
            if place_after_time:
                extracted_place = place_after_time.group(1).strip()

        # Pattern 3: City name at end of string (capitalized word at end)
        if not extracted_place:
            # Look for capitalized word(s) at the end that might be a city
            end_place = re.search(r"\s([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$", user_message)
            if end_place:
                potential_place = end_place.group(1).strip()
                # Exclude common non-place words
                exclude_words = ["AM", "PM", "Kundli", "Kundali", "Chart", "Horoscope", "Born"]
                if potential_place not in exclude_words:
                    extracted_place = potential_place

        return {
            "intent": "birth_chart",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "name": extracted_name,
                "birth_date": extracted_date,
                "birth_time": extracted_time,
                "birth_place": extracted_place
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # =============================================================================
    # NEW PHASE 1 ASTROLOGY INTENTS
    # =============================================================================

    # Dosha Check - Manglik, Kaal Sarp, Sade Sati, Pitra
    dosha_keywords = ["manglik", "mangal dosha", "kuja dosha", "kaal sarp", "kaalsarp", "sade sati", "sadesati", "shani sade", "pitra dosha", "pitru dosha", "am i manglik", "dosha check", "check dosha"]
    if any(kw in user_lower for kw in dosha_keywords):
        # Determine which dosha
        specific_dosha = None
        if "manglik" in user_lower or "mangal" in user_lower or "kuja" in user_lower:
            specific_dosha = "manglik"
        elif "kaal sarp" in user_lower or "kaalsarp" in user_lower:
            specific_dosha = "kaal_sarp"
        elif "sade sati" in user_lower or "sadesati" in user_lower or "shani sade" in user_lower:
            specific_dosha = "sade_sati"
        elif "pitra" in user_lower or "pitru" in user_lower:
            specific_dosha = "pitra"

        # Extract birth details if present
        birth_date = ""
        birth_time = ""
        birth_place = ""

        date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
        if date_match:
            birth_date = date_match.group(1)

        time_match = re.search(r"(?:at\s+)?(\d{1,2}[:.]\d{2})\s*(AM|PM|am|pm)?", user_message, re.IGNORECASE)
        if time_match:
            birth_time = time_match.group(1)
            if time_match.group(2):
                birth_time += " " + time_match.group(2).upper()

        # Pattern 1: "in/at/from <place>"
        place_match = re.search(r"(?:in|at|from)\s+([A-Za-z][A-Za-z\s]*?)(?:\s*$|\s*,|\s*\d)", user_message, re.IGNORECASE)
        if place_match:
            birth_place = place_match.group(1).strip()

        # Pattern 2: Place after AM/PM
        if not birth_place:
            place_after_time = re.search(r"(?:AM|PM|am|pm)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s*$|\s*,)", user_message)
            if place_after_time:
                birth_place = place_after_time.group(1).strip()

        # Pattern 3: Capitalized word at end
        if not birth_place:
            end_place = re.search(r"\s([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$", user_message)
            if end_place:
                potential = end_place.group(1).strip()
                if potential not in ["AM", "PM", "Dosha", "Check", "Manglik"]:
                    birth_place = potential

        return {
            "intent": "dosha_check",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "specific_dosha": specific_dosha,
                "birth_date": birth_date,
                "birth_time": birth_time,
                "birth_place": birth_place
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Life Prediction - Marriage, Career, Children, Health timing questions
    life_prediction_keywords = [
        "when will i get married", "marriage prediction", "marriage timing", "when will i marry",
        "when will i get job", "job prediction", "career prediction", "when will i get promoted",
        "when will i have baby", "children prediction", "child prediction", "when will i conceive",
        "will i get married", "will i find love", "will i get rich", "will i succeed",
        "will my business", "foreign settlement", "will i go abroad", "when will i",
        "prediction for my", "my future", "what is my future"
    ]
    if any(kw in user_lower for kw in life_prediction_keywords):
        # Determine prediction type
        prediction_type = "general"
        if any(kw in user_lower for kw in ["married", "marriage", "spouse", "husband", "wife", "love", "relationship"]):
            prediction_type = "marriage"
        elif any(kw in user_lower for kw in ["job", "career", "promotion", "business", "work", "profession"]):
            prediction_type = "career"
        elif any(kw in user_lower for kw in ["baby", "child", "children", "conceive", "pregnancy", "son", "daughter"]):
            prediction_type = "children"
        elif any(kw in user_lower for kw in ["abroad", "foreign", "overseas", "visa", "immigration"]):
            prediction_type = "foreign"
        elif any(kw in user_lower for kw in ["rich", "wealth", "money", "financial", "property"]):
            prediction_type = "wealth"
        elif any(kw in user_lower for kw in ["health", "illness", "disease", "recovery"]):
            prediction_type = "health"

        # Extract birth details
        birth_date = ""
        birth_time = ""
        birth_place = ""

        date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
        if date_match:
            birth_date = date_match.group(1)

        time_match = re.search(r"(?:at\s+)?(\d{1,2}[:.]\d{2})\s*(AM|PM|am|pm)?", user_message, re.IGNORECASE)
        if time_match:
            birth_time = time_match.group(1)
            if time_match.group(2):
                birth_time += " " + time_match.group(2).upper()

        # Pattern 1: "in/at/from <place>"
        place_match = re.search(r"(?:in|at|from)\s+([A-Za-z][A-Za-z\s]*?)(?:\s*$|\s*,|\s*\d)", user_message, re.IGNORECASE)
        if place_match:
            birth_place = place_match.group(1).strip()

        # Pattern 2: Place after AM/PM
        if not birth_place:
            place_after_time = re.search(r"(?:AM|PM|am|pm)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s*$|\s*,)", user_message)
            if place_after_time:
                birth_place = place_after_time.group(1).strip()

        # Pattern 3: Capitalized word at end
        if not birth_place:
            end_place = re.search(r"\s([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$", user_message)
            if end_place:
                potential = end_place.group(1).strip()
                if potential not in ["AM", "PM", "Prediction", "Future", "Marriage", "Career"]:
                    birth_place = potential

        return {
            "intent": "life_prediction",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "prediction_type": prediction_type,
                "birth_date": birth_date,
                "birth_time": birth_time,
                "birth_place": birth_place,
                "question": user_message
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Panchang - Daily Vedic calendar
    panchang_keywords = [
        # English / romanized
        "panchang", "panchangam", "tithi today", "nakshatra today", "rahu kaal",
        "rahu kalam", "rahukaal", "today's tithi", "shubh muhurat", "aaj ka panchang",
        # Hindi
        "पंचांग", "आज का पंचांग", "तिथि", "नक्षत्र", "राहु काल", "शुभ मुहूर्त",
        # Bengali
        "পঞ্চাং", "আজকের পঞ্চাং", "তিথি", "নক্ষত্র", "রাহু কাল",
        # Tamil
        "பஞ்சாங்கம்", "இன்றைய பஞ்சாங்கம்", "திதி", "நட்சத்திரம்", "ராகு காலம்",
        # Telugu
        "పంచాంగం", "నేటి పంచాంగం", "తిథి", "నక్షత్రం", "రాహు కాలం",
        # Kannada
        "ಪಂಚಾಂಗ", "ಇಂದಿನ ಪಂಚಾಂಗ", "ತಿಥಿ", "ನಕ್ಷತ್ರ", "ರಾಹು ಕಾಲ",
        # Malayalam
        "പഞ്ചാംഗം", "ഇന്നത്തെ പഞ്ചാംഗം", "തിഥി", "നക്ഷത്രം", "രാഹുകാലം",
        # Gujarati
        "પંચાંગ", "આજનું પંચાંગ", "તિથિ", "નક્ષત્ર", "રાહુ કાળ",
        # Marathi
        "पंचांग", "आजचे पंचांग", "तिथी", "नक्षत्र", "राहू काळ",
        # Punjabi
        "ਪੰਚਾਂਗ", "ਅੱਜ ਦਾ ਪੰਚਾਂਗ", "ਤਿਥੀ", "ਨਕਸ਼ੱਤਰ", "ਰਾਹੂ ਕਾਲ",
        # Odia
        "ପଞ୍ଚାଙ୍ଗ", "ଆଜିର ପଞ୍ଚାଙ୍ଗ", "ତିଥି", "ନକ୍ଷତ୍ର", "ରାହୁ କାଳ",
    ]
    if any(kw in user_lower for kw in panchang_keywords):
        # Extract date if specified
        date_str = ""
        date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", user_message)
        if date_match:
            date_str = date_match.group(1)

        # Extract location
        location = "Delhi"
        place_match = re.search(r"(?:in|at|for)\s+([A-Za-z\s]+?)(?:\s*$|\s*,|\s*\d|panchang)", user_message, re.IGNORECASE)
        if place_match:
            location = place_match.group(1).strip()

        return {
            "intent": "get_panchang",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "date": date_str,
                "location": location
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Remedy suggestions
    remedy_keywords = ["which stone", "which gemstone", "gemstone for", "stone for", "which mantra", "mantra for", "remedy for", "remedies for", "which rudraksha", "puja for", "upay for"]
    if any(kw in user_lower for kw in remedy_keywords):
        # Determine remedy type
        remedy_type = "general"
        if any(kw in user_lower for kw in ["stone", "gemstone", "gem"]):
            remedy_type = "gemstone"
        elif any(kw in user_lower for kw in ["mantra", "chant"]):
            remedy_type = "mantra"
        elif any(kw in user_lower for kw in ["puja", "pooja", "worship"]):
            remedy_type = "puja"
        elif any(kw in user_lower for kw in ["rudraksha"]):
            remedy_type = "rudraksha"
        elif any(kw in user_lower for kw in ["fast", "vrat", "fasting"]):
            remedy_type = "fasting"

        # Extract what the remedy is for
        remedy_for = ""
        for_match = re.search(r"(?:for|to)\s+(.+?)(?:\s*$|\s*\?)", user_message, re.IGNORECASE)
        if for_match:
            remedy_for = for_match.group(1).strip()

        return {
            "intent": "get_remedy",
            "intent_confidence": 0.9,
            "extracted_entities": {
                "remedy_type": remedy_type,
                "remedy_for": remedy_for,
                "question": user_message
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Muhurta - Auspicious timing
    muhurta_keywords = ["muhurat", "muhurta", "auspicious date", "auspicious time", "shubh muhurat", "best date for", "good date for", "best time for", "wedding date", "marriage date", "griha pravesh"]
    if any(kw in user_lower for kw in muhurta_keywords):
        # Determine muhurta type
        muhurta_type = "general"
        if any(kw in user_lower for kw in ["wedding", "marriage", "vivah", "shaadi"]):
            muhurta_type = "wedding"
        elif any(kw in user_lower for kw in ["griha", "house", "home", "pravesh"]):
            muhurta_type = "griha_pravesh"
        elif any(kw in user_lower for kw in ["business", "shop", "office", "opening"]):
            muhurta_type = "business"
        elif any(kw in user_lower for kw in ["travel", "journey", "yatra"]):
            muhurta_type = "travel"
        elif any(kw in user_lower for kw in ["vehicle", "car", "bike"]):
            muhurta_type = "vehicle"
        elif any(kw in user_lower for kw in ["naming", "namkaran", "baby name"]):
            muhurta_type = "naming"

        # Extract date range
        year = ""
        month = ""
        year_match = re.search(r"(202\d)", user_message)
        if year_match:
            year = year_match.group(1)

        months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
        for m in months:
            if m in user_lower:
                month = m.capitalize()
                break

        return {
            "intent": "find_muhurta",
            "intent_confidence": 0.9,
            "extracted_entities": {
                "muhurta_type": muhurta_type,
                "year": year,
                "month": month,
                "question": user_message
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Ask astrologer - general astrology questions (CHECK BEFORE HOROSCOPE!)
    # This must come before horoscope to handle questions like "Which gemstone for Pisces?"
    astro_question_keywords = ["saturn return", "mercury retrograde", "planet", "rahu", "ketu", "dasha", "nakshatra", "yantra"]
    if any(kw in user_lower for kw in astro_question_keywords):
        return {
            "intent": "ask_astrologer",
            "intent_confidence": 0.9,
            "extracted_entities": {"astro_question": user_message},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # Horoscope (daily/weekly/monthly) - with keywords in multiple languages
    horoscope_keywords = ["horoscope", "zodiac", "rashifal", "prediction",
                          "राशिफल", "राशि",  # Hindi
                          "ರಾಶಿಫಲ", "ರಾಶಿ",  # Kannada
                          "ராசி", "ராசிபலன்",  # Tamil
                          "రాశిఫలం", "రాశి",  # Telugu
                          "রাশিফল", "রাশি",  # Bengali
                          "രാശിഫലം", "രാശി",  # Malayalam
                          "ਰਾਸ਼ੀਫਲ", "ਰਾਸ਼ੀ",  # Punjabi
                          "ରାଶିଫଳ", "ରାଶି",  # Odia
                          "રાશિફળ", "રાશિ",  # Gujarati (ADDED)
                          "राशीभविष्य", "राशी"]  # Marathi (ADDED)
    zodiac_signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
                    "mesh", "vrishabh", "mithun", "kark", "singh", "kanya",
                    "tula", "vrishchik", "dhanu", "makar", "kumbh", "meen",
                    # Hindi script
                    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
                    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन",
                    # Kannada script
                    "ಮೇಷ", "ವೃಷಭ", "ಮಿಥುನ", "ಕರ್ಕ", "ಸಿಂಹ", "ಕನ್ಯಾ",
                    "ತುಲಾ", "ವೃಶ್ಚಿಕ", "ಧನು", "ಮಕರ", "ಕುಂಭ", "ಮೀನ",
                    # Tamil script
                    "மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி",
                    "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்",
                    # Telugu script
                    "మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య",
                    "తుల", "వృశ్చికం", "ధనస్సు", "మకరం", "కుంభం", "మీనం",
                    # Bengali script
                    "মেষ", "বৃষ", "মিথুন", "কর্কট", "সিংহ", "কন্যা",
                    "তুলা", "বৃশ্চিক", "ধনু", "মকর", "কুম্ভ", "মীন",
                    # Malayalam script
                    "മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം", "ചിങ്ങം", "കന്നി",
                    "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം",
                    # Punjabi script
                    "ਮੇਖ", "ਬ੍ਰਿਖ", "ਮਿਥੁਨ", "ਕਰਕ", "ਸਿੰਘ", "ਕੰਨਿਆ",
                    "ਤੁਲਾ", "ਬ੍ਰਿਸ਼ਚਕ", "ਧਨੁ", "ਮਕਰ", "ਕੁੰਭ", "ਮੀਨ",
                    # Odia script
                    "ମେଷ", "ବୃଷ", "ମିଥୁନ", "କର୍କଟ", "ସିଂହ", "କନ୍ୟା",
                    "ତୁଳା", "ବୃଶ୍ଚିକ", "ଧନୁ", "ମକର", "କୁମ୍ଭ", "ମୀନ",
                    # Gujarati script (ADDED)
                    "મેષ", "વૃષભ", "મિથુન", "કર્ક", "સિંહ", "કન્યા",
                    "તુલા", "વૃશ્ચિક", "ધન", "મકર", "કુંભ", "મીન",
                    # Marathi script (ADDED)
                    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
                    "तूळ", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]

    if any(kw in user_lower for kw in horoscope_keywords) or any(sign in user_lower for sign in zodiac_signs) or any(sign in user_message for sign in zodiac_signs):
        # Check if it's asking about a specific sign's horoscope
        detected_sign = None

        # Check script signs first (in original message, not lowercased)
        script_to_english = {
            # Hindi script
            "मेष": "मेष", "वृषभ": "वृषभ", "मिथुन": "मिथुन",
            "कर्क": "कर्क", "सिंह": "सिंह", "कन्या": "कन्या",
            "तुला": "तुला", "वृश्चिक": "वृश्चिक", "धनु": "धनु",
            "मकर": "मकर", "कुंभ": "कुंभ", "मीन": "मीन",
            # Kannada script
            "ಮೇಷ": "ಮೇಷ", "ವೃಷಭ": "ವೃಷಭ", "ಮಿಥುನ": "ಮಿಥುನ",
            "ಕರ್ಕ": "ಕರ್ಕ", "ಸಿಂಹ": "ಸಿಂಹ", "ಕನ್ಯಾ": "ಕನ್ಯಾ",
            "ತುಲಾ": "ತುಲಾ", "ವೃಶ್ಚಿಕ": "ವೃಶ್ಚಿಕ", "ಧನು": "ಧನು",
            "ಮಕರ": "ಮಕರ", "ಕುಂಭ": "ಕುಂಭ", "ಮೀನ": "ಮೀನ",
            # Tamil script
            "மேஷம்": "மேஷம்", "ரிஷபம்": "ரிஷபம்", "மிதுனம்": "மிதுனம்",
            "கடகம்": "கடகம்", "சிம்மம்": "சிம்மம்", "கன்னி": "கன்னி",
            "துலாம்": "துலாம்", "விருச்சிகம்": "விருச்சிகம்", "தனுசு": "தனுசு",
            "மகரம்": "மகரம்", "கும்பம்": "கும்பம்", "மீனம்": "மீனம்",
            # Telugu script
            "మేషం": "మేషం", "వృషభం": "వృషభం", "మిథునం": "మిథునం",
            "కర్కాటకం": "కర్కాటకం", "సింహం": "సింహం", "కన్య": "కన్య",
            "తుల": "తుల", "వృశ్చికం": "వృశ్చికం", "ధనస్సు": "ధనస్సు",
            "మకరం": "మకరం", "కుంభం": "కుంభం", "మీనం": "మీనం",
            # Bengali script
            "মেষ": "মেষ", "বৃষ": "বৃষ", "মিথুন": "মিথুন",
            "কর্কট": "কর্কট", "সিংহ": "সিংহ", "কন্যা": "কন্যা",
            "তুলা": "তুলা", "বৃশ্চিক": "বৃশ্চিক", "ধনু": "ধনু",
            "মকর": "মকর", "কুম্ভ": "কুম্ভ", "মীন": "মীন",
            # Malayalam script
            "മേടം": "മേടം", "ഇടവം": "ഇടവം", "മിഥുനം": "മിഥുനം",
            "കർക്കടകം": "കർക്കടകം", "ചിങ്ങം": "ചിങ്ങം", "കന്നി": "കന്നി",
            "തുലാം": "തുലാം", "വൃശ്ചികം": "വൃശ്ചികം", "ധനു": "ധനു",
            "മകരം": "മകരം", "കുംഭം": "കുംഭം", "മീനം": "മീനം",
            # Punjabi script
            "ਮੇਖ": "ਮੇਖ", "ਬ੍ਰਿਖ": "ਬ੍ਰਿਖ", "ਮਿਥੁਨ": "ਮਿਥੁਨ",
            "ਕਰਕ": "ਕਰਕ", "ਸਿੰਘ": "ਸਿੰਘ", "ਕੰਨਿਆ": "ਕੰਨਿਆ",
            "ਤੁਲਾ": "ਤੁਲਾ", "ਬ੍ਰਿਸ਼ਚਕ": "ਬ੍ਰਿਸ਼ਚਕ", "ਧਨੁ": "ਧਨੁ",
            "ਮਕਰ": "ਮਕਰ", "ਕੁੰਭ": "ਕੁੰਭ", "ਮੀਨ": "ਮੀਨ",
            # Odia script
            "ମେଷ": "ମେଷ", "ବୃଷ": "ବୃଷ", "ମିଥୁନ": "ମିଥୁନ",
            "କର୍କଟ": "କର୍କଟ", "ସିଂହ": "ସିଂହ", "କନ୍ୟା": "କନ୍ୟା",
            "ତୁଳା": "ତୁଳା", "ବୃଶ୍ଚିକ": "ବୃଶ୍ଚିକ", "ଧନୁ": "ଧନୁ",
            "ମକର": "ମକର", "କୁମ୍ଭ": "କୁମ୍ଭ", "ମୀନ": "ମୀନ",
        }
        for script_sign in script_to_english.keys():
            if script_sign in user_message:
                detected_sign = script_sign  # Keep native script for display
                break

        # Check English/romanized signs
        if not detected_sign:
            for sign in zodiac_signs[:12]:  # English signs only for extraction
                if sign in user_lower:
                    detected_sign = sign
                    break

        period = "today"
        if "weekly" in user_lower or "week" in user_lower:
            period = "weekly"
        elif "monthly" in user_lower or "month" in user_lower:
            period = "monthly"
        elif "tomorrow" in user_lower:
            period = "tomorrow"
        elif "yesterday" in user_lower:
            period = "yesterday"

        return {
            "intent": "get_horoscope",
            "intent_confidence": 0.95,
            "extracted_entities": {
                "astro_sign": detected_sign or "",
                "astro_period": period
            },
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # For other cases, use LLM for classification
    try:
        llm = ChatOpenAI(
            model=common_settings.OPENAI_MODEL,
            temperature=0,
            api_key=common_settings.OPENAI_API_KEY,
        )
        structured_llm = llm.with_structured_output(
            IntentClassification, method="function_calling"
        )

        chain = INTENT_PROMPT | structured_llm

        result: IntentClassification = chain.invoke({"message": user_message})

        # Validate intent is one of our known types
        valid_intents = [
            "local_search",
            "image",
            "image_analysis",
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
            "cricket_score",
            "govt_jobs",
            "govt_schemes",
            "farmer_schemes",
            "free_audio_sources",
            "echallan",
            "fact_check",
            # Astrology intents
            "get_horoscope",
            "birth_chart",
            "kundli_matching",
            "ask_astrologer",
            "numerology",
            "tarot_reading",
            # New Phase 1 astrology intents
            "life_prediction",
            "dosha_check",
            "get_panchang",
            "get_remedy",
            "find_muhurta",
            # Events
            "events",
            # Food
            "food_order",
            "help",
            "chat",
        ]
        intent = result.intent if result.intent in valid_intents else "chat"
        phone = whatsapp_message.get("from_number", "")
        if _is_image_followup_request(user_message):
            cached = get_followup_context(phone) if phone else None
            if cached and cached.get("last_intent") == "image_analysis":
                return {
                    "intent": "image_analysis",
                    "intent_confidence": 0.9,
                    "extracted_entities": {"use_last_image": True},
                    "current_query": user_message,
                    "detected_language": detected_lang,
                    "error": None,
                }
        intent, confidence, entities = _maybe_use_recent_context(
            phone=phone,
            message=user_message,
            intent=intent,
            confidence=result.confidence,
            entities=result.entities or {},
        )

        return {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_entities": entities or {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    except Exception as e:
        # Fallback to chat on error
        phone = whatsapp_message.get("from_number", "")
        intent, confidence, entities = _maybe_use_recent_context(
            phone=phone,
            message=user_message,
            intent="chat",
            confidence=0.5,
            entities={},
        )
        return {
            "intent": intent,
            "intent_confidence": confidence,
            "extracted_entities": entities or {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": f"Intent detection error: {str(e)}",
        }
