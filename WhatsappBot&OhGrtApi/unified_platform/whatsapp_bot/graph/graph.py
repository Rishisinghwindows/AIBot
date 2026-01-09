"""
Main LangGraph Workflow for WhatsApp Bot.

Defines the state graph with conditional routing based on intent detection.
"""

import asyncio
import logging
import re
from typing import Dict, Literal

from langgraph.graph import StateGraph, START, END

from common.graph.state import BotState, create_state_from_whatsapp
from common.config.settings import settings as common_settings
from common.i18n.detector import detect_language
from whatsapp_bot.graph.nodes.intent_v2 import detect_intent
from common.graph.nodes.chat import handle_chat, handle_fallback
from common.graph.nodes.weather import handle_weather
from whatsapp_bot.graph.nodes.news_node import handle_news

# Import pending location store for location message routing
from whatsapp_bot.stores.pending_location_store import get_pending_location_store

# Import bot-specific nodes
from whatsapp_bot.graph.nodes.pnr_status import handle_pnr_status
from whatsapp_bot.graph.nodes.train_status import handle_train_status
from whatsapp_bot.graph.nodes.subscription import handle_subscription
from whatsapp_bot.graph.nodes.astro import handle_horoscope
from whatsapp_bot.graph.nodes.image import handle_image_generation
from whatsapp_bot.graph.nodes.image_analysis import handle_image_analysis
from whatsapp_bot.graph.nodes.reminder import handle_reminder
from whatsapp_bot.graph.nodes.help import handle_help

# Import new nodes from d23apiv1
try:
    from whatsapp_bot.graph.nodes.dosha_node import handle_dosha
    DOSHA_AVAILABLE = True
except ImportError:
    DOSHA_AVAILABLE = False
    handle_dosha = None

try:
    from whatsapp_bot.graph.nodes.life_prediction_node import handle_life_prediction
    LIFE_PREDICTION_AVAILABLE = True
except ImportError:
    LIFE_PREDICTION_AVAILABLE = False
    handle_life_prediction = None

try:
    from whatsapp_bot.graph.nodes.local_search import handle_local_search
    LOCAL_SEARCH_AVAILABLE = True
except ImportError:
    LOCAL_SEARCH_AVAILABLE = False
    handle_local_search = None

try:
    from whatsapp_bot.graph.nodes.metro_ticket import handle_metro_ticket
    METRO_AVAILABLE = True
except ImportError:
    METRO_AVAILABLE = False
    handle_metro_ticket = None

try:
    from whatsapp_bot.graph.nodes.word_game import handle_word_game
    WORD_GAME_AVAILABLE = True
except ImportError:
    WORD_GAME_AVAILABLE = False
    handle_word_game = None

try:
    from whatsapp_bot.graph.nodes.fact_check import handle_fact_check
    FACT_CHECK_AVAILABLE = True
except ImportError:
    FACT_CHECK_AVAILABLE = False
    handle_fact_check = None

try:
    from whatsapp_bot.graph.nodes.event_node import handle_events as handle_event
    EVENT_AVAILABLE = True
except ImportError:
    EVENT_AVAILABLE = False
    handle_event = None

try:
    from whatsapp_bot.graph.nodes.food_node import handle_food
    FOOD_AVAILABLE = True
except ImportError:
    FOOD_AVAILABLE = False
    handle_food = None

try:
    from whatsapp_bot.graph.nodes.db_node import handle_db_query
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    handle_db_query = None

logger = logging.getLogger(__name__)

# AI Language Service (optional)
try:
    from common.services.ai_language_service import ai_understand_message, ai_translate_response
    AI_LANGUAGE_AVAILABLE = True
except ImportError:
    ai_understand_message = None
    ai_translate_response = None
    AI_LANGUAGE_AVAILABLE = False


def _looks_like_hinglish(text: str) -> bool:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return False
    hints = {
        "mujhe", "batao", "ka", "ki", "kya", "kyun", "hai", "nahi", "haan",
        "kripya", "aap", "tum", "mera", "meri", "hum", "hain", "mein",
        "kaise", "kab", "kahan", "kaha", "se", "ke", "ko", "mat",
    }
    zodiac_hinglish = {
        "mesh", "vrishabh", "mithun", "kark", "singh", "simha", "kanya",
        "tula", "vrishchik", "dhanu", "makar", "kumbh", "meen",
        "rashifal", "rashi",
    }
    if any(t in zodiac_hinglish for t in tokens):
        return True

    return sum(1 for t in tokens if t in hints) >= 2


async def _detect_language(message: str) -> str:
    if not message:
        return "en"

    if AI_LANGUAGE_AVAILABLE and common_settings.OPENAI_API_KEY and ai_understand_message:
        try:
            ai_result = await ai_understand_message(
                message,
                openai_api_key=common_settings.OPENAI_API_KEY,
            )
            detected = ai_result.get("detected_language", "en")
        except Exception as e:
            logger.warning(f"AI language detection failed, falling back: {e}")
            detected = detect_language(message)
    else:
        detected = detect_language(message)

    if detected == "en" and _looks_like_hinglish(message):
        return "hi"

    return detected


async def _translate_response(text: str, target_lang: str) -> str:
    if not text or target_lang == "en":
        return text

    if AI_LANGUAGE_AVAILABLE and common_settings.OPENAI_API_KEY and ai_translate_response:
        try:
            return await ai_translate_response(
                text=text,
                target_language=target_lang,
                openai_api_key=common_settings.OPENAI_API_KEY,
            )
        except Exception as e:
            logger.warning(f"AI translation failed, returning original: {e}")

    return text


# Add bot-specific intent patterns
BOT_INTENT_PATTERNS = {
    # India Travel
    "pnr_status": [
        r"\bpnr\b",
        r"\bpnr\s*status\b",
        r"\b\d{10}\b",  # 10-digit PNR
    ],
    "train_status": [
        r"\btrain\b.*\bstatus\b",
        r"\btrain\b.*\b(running|where)\b",
        r"\bwhere\s+is\s+train\b",
    ],
    "metro_ticket": [
        r"\bmetro\b",
        r"\bmetro\s*ticket\b",
        r"\bbook\s*metro\b",
        r"\bdelhi\s*metro\b",
    ],
    # Astrology
    "get_horoscope": [
        r"\bhoroscope\b",
        r"\brashifal\b",
        r"\bkundli\b",
        r"\bzodiac\b",
        r"\b(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)\b",
        r"\b(mesh|vrishabh|mithun|kark|singh|kanya|tula|vrishchik|dhanu|makar|kumbh|meen)\b",
    ],
    "birth_chart": [
        r"\bbirth\s*chart\b",
        r"\bjanam\s*kundli\b",
        r"\bnatal\s*chart\b",
    ],
    "dosha": [
        r"\bmanglik\b",
        r"\bkaal\s*sarp\b",
        r"\bsade\s*sati\b",
        r"\bdosha\b",
        r"\bpitra\s*dosh\b",
    ],
    "life_prediction": [
        r"\bcareer\s*prediction\b",
        r"\bmarriage\s*prediction\b",
        r"\bjob\s*prediction\b",
        r"\blife\s*prediction\b",
        r"\bfuture\s*prediction\b",
    ],
    "subscription": [
        r"\bsubscribe\b",
        r"\bunsubscribe\b",
        r"\bmy\s*subscriptions?\b",
        r"\bdaily\s*horoscope\b",
    ],
    # Utilities
    "set_reminder": [
        r"\bremind\b",
        r"\breminder\b",
        r"\bset\s*reminder\b",
        r"\balarm\b",
    ],
    "local_search": [
        r"\bnearby\b",
        r"\brestaurants?\s*near\b",
        r"\bfind\s*(near|around)\b",
        r"\bsearch\s*local\b",
    ],
    "word_game": [
        r"\bword\s*game\b",
        r"\bplay\s*word\b",
        r"\bguess\s*word\b",
        r"\bwordle\b",
    ],
    "fact_check": [
        r"\bfact\s*check\b",
        r"\bis\s*(it|this)\s*true\b",
        r"\bverify\b",
        r"\btrue\s*or\s*false\b",
    ],
    "event": [
        r"\bevent\b",
        r"\bfestival\b",
        r"\bholiday\b",
        r"\bcalendar\b",
    ],
    "food": [
        r"\bfood\b",
        r"\brecipe\b",
        r"\bcalories\b",
        r"\bnutrition\b",
        r"\bcooking\b",
    ],
    "db_query": [
        r"\bdatabase\b",
        r"\bquery\b",
        r"\bsql\b",
    ],
}

async def check_message_type(state: BotState) -> str:
    """
    Pre-router: Check message type and route accordingly.

    Handles special routing for:
    - Image messages -> image_analysis
    - Location messages with pending search -> local_search

    Args:
        state: Current bot state

    Returns:
        Next node name based on message type
    """
    whatsapp_message = state.get("whatsapp_message", {})
    message_type = whatsapp_message.get("message_type", "text")
    phone = whatsapp_message.get("from_number", "")

    # Route image messages directly to analysis
    if message_type == "image":
        return "image_analysis"

    # Route location messages based on pending search type
    if message_type == "location":
        pending_store = get_pending_location_store()
        pending = await pending_store.peek_pending_search(phone)
        if pending:
            search_query = pending.get("search_query", "")
            # Route to weather handler for weather location requests
            if search_query == "__weather__":
                logger.info(f"Location message from {phone} with pending weather request, routing to weather")
                return "weather"
            # Route to food handler for food location requests
            elif search_query == "__food__":
                logger.info(f"Location message from {phone} with pending food request, routing to food")
                return "food" if FOOD_AVAILABLE else "local_search"
            # Default: route to local_search for other location queries
            else:
                logger.info(f"Location message from {phone} with pending search '{search_query}', routing to local_search")
                return "local_search"
        else:
            logger.info(f"Location message from {phone} without pending search, going to intent detection")

    # All other messages go through intent detection
    return "intent_detection"


def route_by_intent(state: BotState) -> str:
    """
    Route to appropriate handler based on detected intent.

    Args:
        state: Current bot state with intent field

    Returns:
        Name of the next node to execute
    """
    intent = state.get("intent", "chat")

    intent_to_node = {
        # Travel
        "pnr_status": "pnr_status",
        "train_status": "train_status",
        "metro_ticket": "metro_ticket" if METRO_AVAILABLE else "chat",
        # Astrology
        "get_horoscope": "get_horoscope",
        "birth_chart": "get_horoscope",  # Route to same handler
        "dosha": "dosha" if DOSHA_AVAILABLE else "get_horoscope",
        "life_prediction": "life_prediction" if LIFE_PREDICTION_AVAILABLE else "get_horoscope",
        # Subscription
        "subscription": "subscription",
        # Utilities
        "weather": "weather",
        "get_news": "get_news",
        "image": "image_gen",
        "set_reminder": "set_reminder",
        "local_search": "local_search" if LOCAL_SEARCH_AVAILABLE else "chat",
        "word_game": "word_game" if WORD_GAME_AVAILABLE else "chat",
        "fact_check": "fact_check" if FACT_CHECK_AVAILABLE else "chat",
        "event": "event" if EVENT_AVAILABLE else "chat",
        "events": "event" if EVENT_AVAILABLE else "chat",  # Alias for event
        "food": "food" if FOOD_AVAILABLE else "chat",
        "food_order": "food" if FOOD_AVAILABLE else "chat",  # Alias for food
        "db_query": "db_query" if DB_AVAILABLE else "chat",
        "help": "help",
        "chat": "chat",
        "unknown": "chat",
    }

    return intent_to_node.get(intent, "chat")


def check_fallback(state: BotState) -> Literal["fallback", "end"]:
    """
    Check if we need to go to fallback node.

    Args:
        state: Current bot state

    Returns:
        "fallback" if should_fallback is True, else "end"
    """
    if state.get("should_fallback", False):
        return "fallback"
    return "end"


def create_graph() -> StateGraph:
    """
    Create the LangGraph workflow for WhatsApp Bot.

    Returns:
        StateGraph (not compiled)
    """
    graph = StateGraph(BotState)

    # Add all nodes
    graph.add_node("intent_detection", detect_intent)
    graph.add_node("chat", handle_chat)
    graph.add_node("weather", handle_weather)
    graph.add_node("get_news", handle_news)
    graph.add_node("pnr_status", handle_pnr_status)
    graph.add_node("train_status", handle_train_status)
    graph.add_node("get_horoscope", handle_horoscope)
    graph.add_node("subscription", handle_subscription)
    graph.add_node("image_gen", handle_image_generation)
    graph.add_node("image_analysis", handle_image_analysis)
    graph.add_node("set_reminder", handle_reminder)
    graph.add_node("help", handle_help)
    graph.add_node("fallback", handle_fallback)

    # Add optional nodes if available
    if DOSHA_AVAILABLE and handle_dosha:
        graph.add_node("dosha", handle_dosha)
    if LIFE_PREDICTION_AVAILABLE and handle_life_prediction:
        graph.add_node("life_prediction", handle_life_prediction)
    if LOCAL_SEARCH_AVAILABLE and handle_local_search:
        graph.add_node("local_search", handle_local_search)
    if METRO_AVAILABLE and handle_metro_ticket:
        graph.add_node("metro_ticket", handle_metro_ticket)
    if WORD_GAME_AVAILABLE and handle_word_game:
        graph.add_node("word_game", handle_word_game)
    if FACT_CHECK_AVAILABLE and handle_fact_check:
        graph.add_node("fact_check", handle_fact_check)
    if EVENT_AVAILABLE and handle_event:
        graph.add_node("event", handle_event)
    if FOOD_AVAILABLE and handle_food:
        graph.add_node("food", handle_food)
    if DB_AVAILABLE and handle_db_query:
        graph.add_node("db_query", handle_db_query)

    # Define edges - First check message type
    # Build start routing map
    start_routing_map = {
        "image_analysis": "image_analysis",
        "intent_detection": "intent_detection",
        "weather": "weather",  # For location messages with pending weather request
    }
    # Add local_search route if available (for location messages with pending search)
    if LOCAL_SEARCH_AVAILABLE:
        start_routing_map["local_search"] = "local_search"
    # Add food route if available
    if FOOD_AVAILABLE:
        start_routing_map["food"] = "food"

    graph.add_conditional_edges(
        START,
        check_message_type,
        start_routing_map,
    )

    # Build routing map dynamically based on available nodes
    routing_map = {
        "pnr_status": "pnr_status",
        "train_status": "train_status",
        "get_horoscope": "get_horoscope",
        "subscription": "subscription",
        "weather": "weather",
        "get_news": "get_news",
        "image_gen": "image_gen",
        "set_reminder": "set_reminder",
        "help": "help",
        "chat": "chat",
    }

    # Add optional routes
    if DOSHA_AVAILABLE:
        routing_map["dosha"] = "dosha"
    if LIFE_PREDICTION_AVAILABLE:
        routing_map["life_prediction"] = "life_prediction"
    if LOCAL_SEARCH_AVAILABLE:
        routing_map["local_search"] = "local_search"
    if METRO_AVAILABLE:
        routing_map["metro_ticket"] = "metro_ticket"
    if WORD_GAME_AVAILABLE:
        routing_map["word_game"] = "word_game"
    if FACT_CHECK_AVAILABLE:
        routing_map["fact_check"] = "fact_check"
    if EVENT_AVAILABLE:
        routing_map["event"] = "event"
        routing_map["events"] = "event"  # Alias
    if FOOD_AVAILABLE:
        routing_map["food"] = "food"
        routing_map["food_order"] = "food"  # Alias
    if DB_AVAILABLE:
        routing_map["db_query"] = "db_query"

    # Intent Detection -> Route to appropriate handler
    graph.add_conditional_edges(
        "intent_detection",
        route_by_intent,
        routing_map,
    )

    # Each handler can go to fallback or end
    handler_nodes = [
        "chat",
        "weather",
        "get_news",
        "pnr_status",
        "train_status",
        "get_horoscope",
        "subscription",
        "image_gen",
        "image_analysis",
        "set_reminder",
        "help",
    ]

    # Add optional handler nodes
    if DOSHA_AVAILABLE:
        handler_nodes.append("dosha")
    if LIFE_PREDICTION_AVAILABLE:
        handler_nodes.append("life_prediction")
    if LOCAL_SEARCH_AVAILABLE:
        handler_nodes.append("local_search")
    if METRO_AVAILABLE:
        handler_nodes.append("metro_ticket")
    if WORD_GAME_AVAILABLE:
        handler_nodes.append("word_game")
    if FACT_CHECK_AVAILABLE:
        handler_nodes.append("fact_check")
    if EVENT_AVAILABLE:
        handler_nodes.append("event")
    if FOOD_AVAILABLE:
        handler_nodes.append("food")
    if DB_AVAILABLE:
        handler_nodes.append("db_query")

    for node in handler_nodes:
        graph.add_conditional_edges(
            node,
            check_fallback,
            {
                "fallback": "fallback",
                "end": END,
            },
        )

    # Fallback always ends
    graph.add_edge("fallback", END)

    return graph


def get_compiled_graph(checkpointer=None):
    """
    Get a compiled graph ready for execution.

    Args:
        checkpointer: Optional checkpointer instance

    Returns:
        Compiled graph
    """
    graph = create_graph()
    return graph.compile(checkpointer=checkpointer)


# Singleton instance
_graph = None


def get_graph():
    """
    Get or create the singleton graph instance.

    Returns:
        Compiled LangGraph instance
    """
    global _graph
    if _graph is None:
        _graph = get_compiled_graph(checkpointer=None)
    return _graph


async def process_message(whatsapp_message: Dict) -> Dict:
    """
    Process a WhatsApp message through the graph.

    Args:
        whatsapp_message: WhatsApp message dictionary

    Returns:
        Response dictionary
    """
    graph = get_graph()

    # Create initial state from message
    initial_state = create_state_from_whatsapp(whatsapp_message)

    # Use phone number as thread ID
    thread_id = whatsapp_message.get("from_number", "default_thread")
    config = {"configurable": {"thread_id": thread_id}}

    # Execute the graph
    result = await graph.ainvoke(initial_state, config=config)

    response_text = result.get("response_text", "")
    response_type = result.get("response_type", "text")
    detected_lang = result.get("detected_language") or await _detect_language(
        whatsapp_message.get("text", "")
    )
    if response_type in ["text", "location_request"] and response_text:
        response_text = await _translate_response(response_text, detected_lang)

    return {
        "response_text": response_text,
        "response_type": response_type,
        "response_media_url": result.get("response_media_url"),
        "intent": result.get("intent", "unknown"),
        "error": result.get("error"),
        "tool_result": result.get("tool_result"),
        "buttons": result.get("buttons"),
    }


def process_message_sync(whatsapp_message: Dict) -> Dict:
    """Synchronous version of process_message."""
    return asyncio.run(process_message(whatsapp_message))
