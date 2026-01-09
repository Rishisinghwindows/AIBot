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

from common.graph.state import BotState
from common.config.settings import settings
from common.utils.entity_extraction import extract_pnr, extract_train_number
from whatsapp_bot.stores.pending_location_store import get_pending_location_store
from common.i18n.detector import detect_language

# AI Language Service (optional)
try:
    from common.services.ai_language_service import ai_understand_message
    AI_UNDERSTAND_AVAILABLE = True
except ImportError:
    AI_UNDERSTAND_AVAILABLE = False

logger = logging.getLogger(__name__)


class IntentClassification(BaseModel):
    """Structured output for intent classification."""

    intent: str = Field(
        description="The classified intent: local_search, image, pnr_status, train_status, metro_ticket, weather, word_game, db_query, set_reminder, get_news, fact_check, get_horoscope, birth_chart, kundli_matching, ask_astrologer, numerology, tarot_reading, life_prediction, dosha_check, get_panchang, get_remedy, find_muhurta, or chat"
    )
    confidence: float = Field(description="Confidence score between 0 and 1")
    entities: dict = Field(
        description="Extracted entities relevant to the intent",
        default_factory=dict,
    )


INTENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an intelligent intent classifier for an Indian WhatsApp assistant. Your job is to UNDERSTAND what the user wants, not just match keywords.

INTENTS (in priority order):

**FOOD & DINING** - food_order:
Use this for ANY food-related query - hungry, cravings, want to eat, order food, find restaurants, etc.
Examples: "craving for pizza", "I'm hungry", "want to eat biryani", "food near me", "restaurants", "order dinner", "pizza delivery", "best chinese food", "where to eat", "kuch khana hai", "bhook lagi hai"
Extract: "dish" (specific food item), "cuisine" (cuisine type), "city" (if mentioned)

**WEATHER** - weather:
Use this when user wants to know weather, temperature, climate conditions.
Examples: "weather", "what's the weather like", "is it going to rain", "temperature", "how hot is it", "mausam kaisa hai", "will it rain today", "weather forecast"
Extract: "city" (if mentioned, leave empty if not)

**EVENTS & ENTERTAINMENT** - events:
Use this for events, concerts, shows, matches, movies, things to do.
Examples: "events near me", "concerts today", "what's happening", "IPL match", "comedy shows", "movies", "things to do", "kya ho raha hai"
Extract: "query" (what they're looking for), "city" (if mentioned)

**LOCAL SEARCH** - local_search:
Use this for finding any local places/services - hospitals, ATMs, plumbers, electricians, shops, etc.
Examples: "hospitals near me", "find a plumber", "ATM nearby", "petrol pump", "electrician", "salon", "gym near me", "pharmacies"
Extract: "search_query" (what they're looking for), "location" (actual place name, NOT "near me")

**TRAVEL - PNR Status** - pnr_status:
Use when user provides a 10-digit PNR number to check railway booking status.
Examples: "check pnr 1234567890", "pnr status", "my pnr is 9876543210"
Extract: "pnr" (10-digit number)

**TRAVEL - Train Status** - train_status:
Use for live train running status (train numbers like 12301, 22691).
Examples: "train 12301 status", "where is rajdhani", "running status"
Extract: "train_number", "date"

**TRAVEL - Metro** - metro_ticket:
Use for metro routes, fares, information.
Examples: "metro from dwarka to rajiv chowk", "metro fare"
Extract: "source_station", "destination_station"

**IMAGE GENERATION** - image:
Use when user wants to create/generate an AI image.
Examples: "generate image of sunset", "create picture", "make an image"
Extract: "image_prompt"

**REMINDERS** - set_reminder:
Use when user wants to set a reminder or alarm.
Examples: "remind me in 5 minutes", "set alarm for 9 AM"
Extract: "reminder_time", "reminder_message"

**NEWS** - get_news:
Use for news and current affairs.
Examples: "latest news", "cricket news", "news about India"
Extract: "news_query", "news_category"

**FACT CHECK** - fact_check:
Use when user wants to verify a claim or check if something is true/fake.
Examples: "is this true", "fact check", "is this fake news"
Extract: "fact_check_claim"

**ASTROLOGY INTENTS**:
- get_horoscope: Daily/weekly horoscope ("aries horoscope", "my horoscope today")
- birth_chart: Kundli/birth chart ("my kundli", "birth chart for...")
- kundli_matching: Marriage compatibility ("match kundli", "gun milan")
- ask_astrologer: General astrology questions
- numerology: Name/number analysis
- tarot_reading: Tarot card readings

**DEFAULT** - chat:
Use for greetings, general questions, help, or unclear queries.
Examples: "hello", "what can you do", "tell me a joke"

IMPORTANT RULES:
1. UNDERSTAND INTENT from context, not just keywords
2. "craving for pizza" = food_order (not local_search)
3. "I'm hungry" = food_order
4. "what's the weather" without city = weather (city: "")
5. "near me", "nearby" are NOT locations - leave location empty
6. When in doubt between food_order and local_search for restaurants, use food_order
7. Be smart about Indian languages - "kuch khana hai" = food_order, "mausam" = weather

    EXAMPLES:
    User: "craving for pizza"
    Output: {{"intent": "food_order", "confidence": 0.95, "entities": {{"dish": "pizza"}}}}

    User: "I'm hungry"
    Output: {{"intent": "food_order", "confidence": 0.95, "entities": {{}}}}

    User: "restaurants near me"
    Output: {{"intent": "food_order", "confidence": 0.95, "entities": {{}}}}

    User: "biryani in hyderabad"
    Output: {{"intent": "food_order", "confidence": 0.95, "entities": {{"dish": "biryani", "city": "Hyderabad"}}}}

    User: "weather"
    Output: {{"intent": "weather", "confidence": 0.95, "entities": {{"city": ""}}}}

    User: "what's the weather like"
    Output: {{"intent": "weather", "confidence": 0.95, "entities": {{"city": ""}}}}

    User: "weather in delhi"
    Output: {{"intent": "weather", "confidence": 0.95, "entities": {{"city": "Delhi"}}}}

    User: "events near me"
    Output: {{"intent": "events", "confidence": 0.95, "entities": {{"query": "events"}}}}

    User: "IPL match today"
    Output: {{"intent": "events", "confidence": 0.95, "entities": {{"query": "IPL match"}}}}

    User: "hospitals near me"
    Output: {{"intent": "local_search", "confidence": 0.95, "entities": {{"search_query": "hospitals", "location": ""}}}}

    User: "find a plumber"
    Output: {{"intent": "local_search", "confidence": 0.95, "entities": {{"search_query": "plumber", "location": ""}}}}

    User: "ATM in connaught place"
    Output: {{"intent": "local_search", "confidence": 0.95, "entities": {{"search_query": "ATM", "location": "Connaught Place"}}}}

    User: "remind me in 5 minutes to drink water"
    Output: {{"intent": "set_reminder", "confidence": 0.95, "entities": {{"reminder_time": "in 5 minutes", "reminder_message": "drink water"}}}}

    User: "aries horoscope"
    Output: {{"intent": "get_horoscope", "confidence": 0.95, "entities": {{"astro_sign": "aries"}}}}

    User: "hello"
    Output: {{"intent": "chat", "confidence": 0.95, "entities": {{}}}}

Respond ONLY in JSON format: {{"intent": "...", "confidence": 0.0-1.0, "entities": {{...}}}}""",
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
    detected_lang = state.get("detected_language") or "en"
    if user_message and not state.get("detected_language"):
        if AI_UNDERSTAND_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                ai_result = await ai_understand_message(
                    user_message,
                    openai_api_key=settings.OPENAI_API_KEY,
                )
                detected_lang = ai_result.get("detected_language", "en")
            except Exception as e:
                logger.warning(f"AI language detection failed, falling back: {e}")
                detected_lang = detect_language(user_message)
        else:
            detected_lang = detect_language(user_message)
    logger.info(f"Detected language: {detected_lang} for message: {(user_message or '')[:50]}...")

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
    help_keywords = ["what can you do", "what do you do", "what are your features",
                     "what services", "how can you help", "what can i ask",
                     "show me what you can do", "help me"]
    if any(kw in user_lower for kw in help_keywords):
        return {
            "intent": "help",
            "intent_confidence": 0.95,
            "extracted_entities": {},
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

    # Check for train status patterns
    train_keywords = ["train", "running status", "where is", "train status"]
    if any(kw in user_lower for kw in train_keywords):
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
        "generate image",
        "create image",
        "make image",
        "draw",
        "generate picture",
        "create picture",
        "make picture",
        "generate a",
        "create a picture",
        "image of",
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
    metro_keywords = ["metro", "dmrc", "delhi metro", "metro fare", "metro ticket"]
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
    word_game_keywords = ["word game", "play a game", "anagram"]
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
    reminder_keywords = ["remind", "reminder", "set alarm", "alarm me"]
    if any(kw in user_lower for kw in reminder_keywords):
        return {
            "intent": "set_reminder",
            "intent_confidence": 0.9,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    # EARLY CHECK: "near me", "nearby" etc - intelligently route based on what's being searched
    # This MUST come before food/events/weather checks to properly handle "X near me" queries
    location_indicators = ["near me", "nearby", "nearest", "around me", "close to me", "near here"]
    if any(ind in user_lower for ind in location_indicators):
        # Extract search term by removing the indicator
        search_term = user_lower
        for ind in location_indicators:
            search_term = search_term.replace(ind, "").strip()
        # Remove common prefixes
        for prefix in ["find", "search", "show", "get", "where is", "where are", "looking for", "i need", "i want"]:
            if search_term.startswith(prefix):
                search_term = search_term[len(prefix):].strip()

        logger.info(f"Detected 'near me' query, search_term: '{search_term}'")

        # Determine the intent based on what's being searched
        # Weather queries
        if search_term in ["weather", "temperature", "mausam", "weather today", "current weather"]:
            logger.info(f"Routing 'near me' query to weather intent")
            return {
                "intent": "weather",
                "intent_confidence": 0.95,
                "extracted_entities": {"city": ""},  # Empty - will trigger location request
                "current_query": user_message,
                "detected_language": detected_lang,
                "error": None,
            }

        # Food/Restaurant queries
        food_terms = ["restaurant", "restaurants", "food", "cafe", "cafes", "hotel", "hotels",
                      "biryani", "pizza", "burger", "dosa", "idli", "chinese", "italian",
                      "north indian", "south indian", "breakfast", "lunch", "dinner", "eat",
                      "khana", "restro", "dhaba", "eatery"]
        if any(term in search_term for term in food_terms):
            logger.info(f"Routing 'near me' query to local_search intent (food/restaurant)")
            return {
                "intent": "local_search",
                "intent_confidence": 0.95,
                "extracted_entities": {
                    "search_query": user_message,
                    "location": "",  # Empty - will trigger location request
                },
                "current_query": user_message,
                "detected_language": detected_lang,
                "error": None,
            }

        # Event queries
        event_terms = ["event", "events", "concert", "concerts", "shows", "match", "matches",
                       "ipl", "cricket", "comedy", "standup", "festival", "movie", "movies", "theatre"]
        if any(term in search_term for term in event_terms):
            logger.info(f"Routing 'near me' query to events intent")
            return {
                "intent": "events",
                "intent_confidence": 0.95,
                "extracted_entities": {"query": user_message},
                "current_query": user_message,
                "detected_language": detected_lang,
                "error": None,
            }

        # Default: route to local_search for generic location queries
        # (hospitals, ATMs, petrol pumps, plumbers, electricians, etc.)
        logger.info(f"Routing 'near me' query to local_search intent")
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
        # Natural expressions
        "craving", "crave", "want to eat", "feel like eating", "in mood for",
        "starving", "famished", "peckish", "appetite", "where to eat",
        # Common misspellings
        "restraunt", "restraunts", "resturant", "resturants", "restarant",
        "restraurant", "restaurent", "restaurents", "restrant", "restrants",
        "zomato", "swiggy", "food delivery", "to eat", "lets eat", "let's eat", "dinner", "lunch",
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
        # IPL/Cricket
        "ipl", "ipl match", "cricket match", "cricket ticket",
        "rcb match", "csk match", "mi match", "kkr match", "dc match",
        "srh match", "rr match", "pbks match", "gt match", "lsg match",
        "royal challengers", "chennai super kings", "mumbai indians",
        "kolkata knight riders", "delhi capitals", "sunrisers",
        "rajasthan royals", "punjab kings", "gujarat titans", "lucknow super giants",
        # Concerts
        "concert", "live show", "music show", "arijit singh", "coldplay", "ar rahman",
        # Comedy
        "comedy show", "standup", "stand-up comedy", "comedian",
        "zakir khan", "biswa", "kenny sebastian",
        # General events
        "book ticket", "event ticket", "upcoming events", "football match", "isl match",
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

    # Check for news patterns
    news_keywords = ["news", "headlines", "latest news", "breaking news"]
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

    # Check for astro patterns - more specific matching
    user_lower = user_message.lower()

    # Tarot reading
    tarot_keywords = ["tarot", "tarot card", "tarot reading", "pick a card", "card reading"]
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
    numerology_keywords = ["numerology", "lucky number", "life path number", "name number", "destiny number"]
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
    birth_chart_keywords = ["birth chart", "kundli", "kundali", "janam patri", "janam kundli", "natal chart", "my chart"]
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
    panchang_keywords = ["panchang", "panchangam", "tithi today", "nakshatra today", "rahu kaal", "rahu kalam", "rahukaal", "today's tithi", "shubh muhurat", "aaj ka panchang"]
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
                          "ରାଶିଫଳ", "ରାଶି"]  # Odia
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
                    "ତୁଳା", "ବୃଶ୍ଚିକ", "ଧନୁ", "ମକର", "କୁମ୍ଭ", "ମୀନ"]

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
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
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
            "pnr_status",
            "train_status",
            "metro_ticket",
            "weather",
            "word_game",
            "db_query",
            "set_reminder",
            "get_news",
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

        return {
            "intent": intent,
            "intent_confidence": result.confidence,
            "extracted_entities": result.entities or {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": None,
        }

    except Exception as e:
        # Fallback to chat on error
        return {
            "intent": "chat",
            "intent_confidence": 0.5,
            "extracted_entities": {},
            "current_query": user_message,
            "detected_language": detected_lang,
            "error": f"Intent detection error: {str(e)}",
        }
