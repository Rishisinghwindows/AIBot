"""
Astrology Sub-Graph

Handles all astrology-related features:
- Horoscope (daily/weekly/monthly)
- Birth Chart (Kundli)
- Kundli Matching
- Dosha Check (Manglik, Kaal Sarp, Sade Sati)
- Life Predictions (Marriage, Career, Children, etc.)
- Panchang
- Numerology
- Tarot Reading
- Ask Astrologer (Q&A)

This sub-graph:
1. Detects specific astrology intent
2. Checks for user's saved birth details
3. Routes to appropriate handler
4. Saves birth details for future use
"""

import re
import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from bot.state import BotState
from bot.stores.user_store import get_user_store
from bot.validators.birth_details import (
    validate_birth_date,
    validate_birth_time,
    validate_birth_place,
)

# Import astrology handlers
from bot.nodes.astro_node import (
    handle_horoscope,
    handle_birth_chart,
    handle_kundli_matching,
    handle_ask_astrologer,
    handle_numerology,
    handle_tarot,
    handle_panchang,
)
from bot.nodes.dosha_node import handle_dosha_check
from bot.nodes.life_prediction_node import handle_life_prediction

logger = logging.getLogger(__name__)


# Astrology-specific intent type
AstroIntentType = Literal[
    "horoscope",
    "birth_chart",
    "kundli_matching",
    "dosha_check",
    "life_prediction",
    "panchang",
    "numerology",
    "tarot",
    "ask_astrologer",
]


# Intent detection keywords
ASTRO_INTENT_PATTERNS = {
    "horoscope": [
        r"horoscope", r"rashifal", r"zodiac.*prediction",
        r"(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces).*(?:today|weekly|monthly|tomorrow)",
        r"(?:today|weekly|monthly).*(?:prediction|forecast)",
    ],
    "birth_chart": [
        r"kundli", r"kundali", r"birth\s*chart", r"janam\s*patri",
        r"planetary\s*position", r"generate.*chart",
    ],
    "kundli_matching": [
        r"match.*kundli", r"kundli.*match", r"compatibility",
        r"gun\s*milan", r"matching", r"compatible",
    ],
    "dosha_check": [
        r"manglik", r"mangal\s*dosha", r"kuja\s*dosha",
        r"kaal\s*sarp", r"kaalsarp",
        r"sade\s*sati", r"sadesati", r"shani\s*sade",
        r"pitra\s*dosha", r"pitru\s*dosha",
        r"dosha\s*check", r"check.*dosha", r"am\s*i\s*manglik",
    ],
    "life_prediction": [
        r"when\s*will\s*i", r"will\s*i\s*get", r"will\s*i\s*have",
        r"marriage\s*prediction", r"career\s*prediction", r"job\s*prediction",
        r"child.*prediction", r"baby", r"conceive",
        r"foreign.*settlement", r"go\s*abroad", r"settle\s*abroad",
        r"become\s*rich", r"wealth\s*prediction", r"financial\s*future",
        r"health\s*prediction", r"my\s*future",
    ],
    "panchang": [
        r"panchang", r"panchangam", r"tithi", r"nakshatra\s*today",
        r"rahu\s*kaal", r"rahu\s*kalam", r"shubh\s*muhurat",
        r"today.*tithi", r"aaj\s*ka\s*panchang",
    ],
    "numerology": [
        r"numerology", r"lucky\s*number", r"name\s*number",
        r"life\s*path\s*number", r"destiny\s*number",
    ],
    "tarot": [
        r"tarot", r"card\s*reading", r"pick\s*a\s*card",
        r"celtic\s*cross", r"three\s*card",
    ],
}


async def detect_astro_intent(state: BotState) -> dict:
    """
    Detect specific astrology intent from query.

    Also enriches state with user's saved birth details if available.

    Args:
        state: Current bot state

    Returns:
        Updated state with astro_intent and birth details
    """
    query = state.get("current_query", "")
    if not query:
        query = state.get("whatsapp_message", {}).get("text", "")

    query_lower = query.lower()

    # Detect intent using patterns
    detected_intent = "ask_astrologer"  # Default fallback

    for intent, patterns in ASTRO_INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                detected_intent = intent
                break
        if detected_intent != "ask_astrologer":
            break

    # Get phone number for user lookup
    phone = state.get("whatsapp_message", {}).get("from_number", "")

    # Try to get saved birth details
    saved_birth_details = None
    if phone:
        try:
            user_store = get_user_store()
            saved_birth_details = await user_store.get_birth_details(phone)
        except Exception as e:
            logger.warning(f"Could not get birth details: {e}")

    # Extract birth details from current query
    extracted_entities = state.get("extracted_entities", {})

    # Parse and validate date from query
    date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", query)
    if date_match:
        date_result = validate_birth_date(date_match.group(1))
        if date_result.is_valid:
            extracted_entities["birth_date"] = date_result.value
        else:
            # Store raw but mark as potentially invalid
            extracted_entities["birth_date"] = date_match.group(1)
            extracted_entities["birth_date_error"] = date_result.error

    # Parse and validate time from query
    time_match = re.search(r"(\d{1,2}[:.]\d{2})\s*(AM|PM|am|pm)?", query, re.IGNORECASE)
    if time_match:
        time_str = time_match.group(1)
        if time_match.group(2):
            time_str += " " + time_match.group(2).upper()
        time_result = validate_birth_time(time_str)
        if time_result.is_valid:
            extracted_entities["birth_time"] = time_result.value
        else:
            extracted_entities["birth_time"] = time_str
            extracted_entities["birth_time_error"] = time_result.error

    # Parse and validate place from query - multiple patterns
    place_str = ""

    # Pattern 1: "in/at/from <place>"
    place_match = re.search(r"(?:in|at|from)\s+([A-Za-z][A-Za-z\s]*?)(?:\s*$|\s*,|\s*\d|\s*born)", query, re.IGNORECASE)
    if place_match:
        place_str = place_match.group(1).strip()

    # Pattern 2: Place after AM/PM (e.g., "10:30 AM Delhi")
    if not place_str:
        place_after_time = re.search(r"(?:AM|PM|am|pm)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s*$|\s*,)", query)
        if place_after_time:
            place_str = place_after_time.group(1).strip()

    # Pattern 3: Capitalized word at end of string
    if not place_str:
        end_place = re.search(r"\s([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$", query)
        if end_place:
            potential = end_place.group(1).strip()
            # Exclude common non-place words
            if potential not in ["AM", "PM", "Kundli", "Kundali", "Chart", "Horoscope", "Born"]:
                place_str = potential

    if place_str:
        place_result = validate_birth_place(place_str)
        if place_result.is_valid:
            extracted_entities["birth_place"] = place_result.value
        else:
            extracted_entities["birth_place"] = place_str
            extracted_entities["birth_place_error"] = place_result.error

    # Merge with saved details (prefer current query over saved)
    if saved_birth_details:
        if not extracted_entities.get("birth_date"):
            extracted_entities["birth_date"] = saved_birth_details.get("birth_date", "")
        if not extracted_entities.get("birth_time"):
            extracted_entities["birth_time"] = saved_birth_details.get("birth_time", "")
        if not extracted_entities.get("birth_place"):
            extracted_entities["birth_place"] = saved_birth_details.get("birth_place", "")

    # Detect prediction type for life_prediction
    if detected_intent == "life_prediction":
        prediction_type = "general"
        if any(kw in query_lower for kw in ["married", "marriage", "spouse", "husband", "wife", "love"]):
            prediction_type = "marriage"
        elif any(kw in query_lower for kw in ["job", "career", "promotion", "business", "work"]):
            prediction_type = "career"
        elif any(kw in query_lower for kw in ["baby", "child", "children", "conceive"]):
            prediction_type = "children"
        elif any(kw in query_lower for kw in ["abroad", "foreign", "overseas"]):
            prediction_type = "foreign"
        elif any(kw in query_lower for kw in ["rich", "wealth", "money", "financial"]):
            prediction_type = "wealth"
        elif any(kw in query_lower for kw in ["health", "illness", "disease"]):
            prediction_type = "health"
        extracted_entities["prediction_type"] = prediction_type

    # Detect dosha type for dosha_check
    if detected_intent == "dosha_check":
        specific_dosha = None
        if "manglik" in query_lower or "mangal" in query_lower or "kuja" in query_lower:
            specific_dosha = "manglik"
        elif "kaal sarp" in query_lower or "kaalsarp" in query_lower:
            specific_dosha = "kaal_sarp"
        elif "sade sati" in query_lower or "sadesati" in query_lower or "shani sade" in query_lower:
            specific_dosha = "sade_sati"
        elif "pitra" in query_lower or "pitru" in query_lower:
            specific_dosha = "pitra"
        extracted_entities["specific_dosha"] = specific_dosha

    # Detect zodiac sign for horoscope
    if detected_intent == "horoscope":
        signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                 "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
        for sign in signs:
            if sign in query_lower:
                extracted_entities["astro_sign"] = sign.capitalize()
                break

        # Detect period
        if "weekly" in query_lower or "week" in query_lower:
            extracted_entities["astro_period"] = "weekly"
        elif "monthly" in query_lower or "month" in query_lower:
            extracted_entities["astro_period"] = "monthly"
        elif "tomorrow" in query_lower:
            extracted_entities["astro_period"] = "tomorrow"
        else:
            extracted_entities["astro_period"] = "today"

    return {
        "astro_intent": detected_intent,
        "extracted_entities": extracted_entities,
        "intent": f"astro_{detected_intent}",  # For compatibility
        "current_query": query,
    }


def route_astro_intent(state: BotState) -> str:
    """
    Route to appropriate astrology handler.

    Args:
        state: Current bot state with astro_intent

    Returns:
        Node name to route to
    """
    astro_intent = state.get("astro_intent", "ask_astrologer")

    intent_to_node = {
        "horoscope": "horoscope",
        "birth_chart": "birth_chart",
        "kundli_matching": "kundli_matching",
        "dosha_check": "dosha_check",
        "life_prediction": "life_prediction",
        "panchang": "panchang",
        "numerology": "numerology",
        "tarot": "tarot",
        "ask_astrologer": "ask_astrologer",
    }

    return intent_to_node.get(astro_intent, "ask_astrologer")


async def save_birth_details_post_handler(state: BotState) -> dict:
    """
    Post-handler to save birth details if provided.

    Called after astrology handlers to persist birth details.

    Args:
        state: Current bot state with extracted entities

    Returns:
        Updated state (unchanged)
    """
    phone = state.get("whatsapp_message", {}).get("from_number", "")
    entities = state.get("extracted_entities", {})

    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()

    # Only save if all details are provided
    if phone and all([birth_date, birth_time, birth_place]):
        try:
            user_store = get_user_store()
            await user_store.save_birth_details(
                phone=phone,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place
            )
            logger.info(f"Saved birth details for {phone}")
        except Exception as e:
            logger.warning(f"Could not save birth details: {e}")

    return {}


def create_astro_graph() -> StateGraph:
    """
    Create the astrology sub-graph.

    Returns:
        StateGraph for astrology domain
    """
    graph = StateGraph(BotState)

    # Add nodes
    graph.add_node("detect_intent", detect_astro_intent)
    graph.add_node("horoscope", handle_horoscope)
    graph.add_node("birth_chart", handle_birth_chart)
    graph.add_node("kundli_matching", handle_kundli_matching)
    graph.add_node("dosha_check", handle_dosha_check)
    graph.add_node("life_prediction", handle_life_prediction)
    graph.add_node("panchang", handle_panchang)
    graph.add_node("numerology", handle_numerology)
    graph.add_node("tarot", handle_tarot)
    graph.add_node("ask_astrologer", handle_ask_astrologer)
    graph.add_node("save_details", save_birth_details_post_handler)

    # Define edges
    graph.add_edge(START, "detect_intent")

    # Route based on detected intent
    graph.add_conditional_edges(
        "detect_intent",
        route_astro_intent,
        {
            "horoscope": "horoscope",
            "birth_chart": "birth_chart",
            "kundli_matching": "kundli_matching",
            "dosha_check": "dosha_check",
            "life_prediction": "life_prediction",
            "panchang": "panchang",
            "numerology": "numerology",
            "tarot": "tarot",
            "ask_astrologer": "ask_astrologer",
        }
    )

    # All handlers go to save_details, then end
    for node in [
        "horoscope", "birth_chart", "kundli_matching",
        "dosha_check", "life_prediction", "panchang",
        "numerology", "tarot", "ask_astrologer"
    ]:
        graph.add_edge(node, "save_details")

    graph.add_edge("save_details", END)

    return graph


# Compiled graph instance (lazy)
_compiled_astro_graph = None


def get_astro_graph():
    """
    Get compiled astrology sub-graph.

    Returns:
        Compiled StateGraph
    """
    global _compiled_astro_graph
    if _compiled_astro_graph is None:
        _compiled_astro_graph = create_astro_graph().compile()
    return _compiled_astro_graph
