"""
Main LangGraph Workflow Definition

Defines the state graph with conditional routing based on intent detection.
"""

from typing import Literal
import asyncio
from langgraph.graph import StateGraph, START, END

from bot.config import settings
from bot.state import BotState, WhatsAppMessage, create_initial_state
from bot.nodes.intent import detect_intent
from bot.nodes.local_search import handle_local_search
from bot.nodes.image_gen import handle_image_generation
from bot.nodes.pnr_status import handle_pnr_status
from bot.nodes.train_status import handle_train_status
from bot.nodes.metro_ticket import handle_metro_ticket
from bot.nodes.weather import handle_weather
from bot.nodes.word_game import handle_word_game
from bot.nodes.db_node import handle_db_query
from bot.nodes.reminder_node import handle_reminder
from bot.nodes.news_node import handle_news
from bot.nodes.fact_check import handle_fact_check
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
from bot.nodes.subscription_node import handle_subscription
from bot.nodes.chat import handle_chat, handle_fallback
from bot.nodes.help import handle_help
from bot.nodes.event_node import handle_events
from bot.nodes.food_node import handle_food


def route_by_intent(state: BotState) -> str:
    """
    Conditional routing function based on detected intent.

    Args:
        state: Current bot state with intent field

    Returns:
        Name of the next node to execute
    """
    intent = state.get("intent", "chat")

    intent_to_node = {
        "local_search": "local_search",
        "image": "image_gen",
        "pnr_status": "pnr_status",
        "train_status": "train_status",
        "metro_ticket": "metro_ticket",
        "weather": "weather",
        "word_game": "word_game",
        "db_query": "db_query",
        "set_reminder": "set_reminder",
        "get_news": "get_news",
        "fact_check": "fact_check",
        # Astrology nodes
        "get_horoscope": "get_horoscope",
        "birth_chart": "birth_chart",
        "kundli_matching": "kundli_matching",
        "ask_astrologer": "ask_astrologer",
        "numerology": "numerology",
        "tarot_reading": "tarot_reading",
        # New Phase 1 astrology nodes
        "dosha_check": "dosha_check",
        "life_prediction": "life_prediction",
        "get_panchang": "get_panchang",
        "get_remedy": "ask_astrologer",  # Route to ask_astrologer for remedies
        "find_muhurta": "ask_astrologer",  # Route to ask_astrologer for muhurta
        # Subscription management
        "subscription": "subscription",
        # Events
        "events": "events",
        # Food
        "food_order": "food_order",
        # Help
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
    Create the LangGraph workflow.

    Returns:
        StateGraph (not compiled)
    """
    # Initialize the state graph with our state type
    graph = StateGraph(BotState)

    # Add all nodes
    graph.add_node("intent_detection", detect_intent)
    graph.add_node("local_search", handle_local_search)
    graph.add_node("image_gen", handle_image_generation)
    graph.add_node("pnr_status", handle_pnr_status)
    graph.add_node("train_status", handle_train_status)
    graph.add_node("metro_ticket", handle_metro_ticket)
    graph.add_node("weather", handle_weather)
    graph.add_node("word_game", handle_word_game)
    graph.add_node("db_query", handle_db_query)
    graph.add_node("set_reminder", handle_reminder)
    graph.add_node("get_news", handle_news)
    graph.add_node("fact_check", handle_fact_check)
    # Astrology nodes
    graph.add_node("get_horoscope", handle_horoscope)
    graph.add_node("birth_chart", handle_birth_chart)
    graph.add_node("kundli_matching", handle_kundli_matching)
    graph.add_node("ask_astrologer", handle_ask_astrologer)
    graph.add_node("numerology", handle_numerology)
    graph.add_node("tarot_reading", handle_tarot)
    # New Phase 1 astrology nodes
    graph.add_node("dosha_check", handle_dosha_check)
    graph.add_node("life_prediction", handle_life_prediction)
    graph.add_node("get_panchang", handle_panchang)
    # Subscription management
    graph.add_node("subscription", handle_subscription)
    # Events node
    graph.add_node("events", handle_events)
    # Food node
    graph.add_node("food_order", handle_food)
    # Help node
    graph.add_node("help", handle_help)
    # General nodes
    graph.add_node("chat", handle_chat)
    graph.add_node("fallback", handle_fallback)

    # Define edges
    # Start -> Intent Detection
    graph.add_edge(START, "intent_detection")

    # Intent Detection -> Route to appropriate handler
    graph.add_conditional_edges(
        "intent_detection",
        route_by_intent,
        {
            "local_search": "local_search",
            "image_gen": "image_gen",
            "pnr_status": "pnr_status",
            "train_status": "train_status",
            "metro_ticket": "metro_ticket",
            "weather": "weather",
            "word_game": "word_game",
            "db_query": "db_query",
            "set_reminder": "set_reminder",
            "get_news": "get_news",
            "fact_check": "fact_check",
            # Astrology routes
            "get_horoscope": "get_horoscope",
            "birth_chart": "birth_chart",
            "kundli_matching": "kundli_matching",
            "ask_astrologer": "ask_astrologer",
            "numerology": "numerology",
            "tarot_reading": "tarot_reading",
            # New Phase 1 astrology routes
            "dosha_check": "dosha_check",
            "life_prediction": "life_prediction",
            "get_panchang": "get_panchang",
            # Subscription management
            "subscription": "subscription",
            # Events
            "events": "events",
            # Food
            "food_order": "food_order",
            # Help
            "help": "help",
            "chat": "chat",
        },
    )

    # Each handler can go to fallback or end
    for node in [
        "local_search",
        "image_gen",
        "pnr_status",
        "train_status",
        "metro_ticket",
        "weather",
        "word_game",
        "db_query",
        "set_reminder",
        "get_news",
        "fact_check",
        # Astrology nodes
        "get_horoscope",
        "birth_chart",
        "kundli_matching",
        "ask_astrologer",
        "numerology",
        "tarot_reading",
        # New Phase 1 astrology nodes
        "dosha_check",
        "life_prediction",
        "get_panchang",
        # Subscription management
        "subscription",
        # Events
        "events",
        # Food
        "food_order",
        # Help
        "help",
        "chat",
    ]:
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


async def process_message(whatsapp_message: dict) -> dict:
    """
    Main entry point: Process a WhatsApp message through the graph.

    Args:
        whatsapp_message: WhatsApp message dictionary with keys:
            - message_id: str
            - from_number: str
            - phone_number_id: str
            - timestamp: str
            - message_type: str
            - text: Optional[str]
            - media_id: Optional[str]

    Returns:
        Response dictionary with:
            - response_text: str
            - response_type: str ("text" or "image")
            - response_media_url: Optional[str]
            - intent: str
            - error: Optional[str]
    """
    # Get graph (no checkpointer needed for stateless operation)
    graph = get_graph()

    # Create initial state
    initial_state = create_initial_state(
        WhatsAppMessage(
            message_id=whatsapp_message.get("message_id", ""),
            from_number=whatsapp_message.get("from_number", ""),
            phone_number_id=whatsapp_message.get("phone_number_id", ""),
            timestamp=whatsapp_message.get("timestamp", ""),
            message_type=whatsapp_message.get("message_type", "text"),
            text=whatsapp_message.get("text"),
            media_id=whatsapp_message.get("media_id"),
            location=whatsapp_message.get("location"),
        )
    )

    # Use phone number as thread ID for persistence
    thread_id = whatsapp_message.get("from_number", "default_thread")
    config = {"configurable": {"thread_id": thread_id}}

    # Execute the graph asynchronously (required for async node functions)
    result = await graph.ainvoke(initial_state, config=config)

    return {
        "response_text": result.get("response_text", ""),
        "response_type": result.get("response_type", "text"),
        "response_media_url": result.get("response_media_url"),
        "intent": result.get("intent", "unknown"),
        "error": result.get("error"),
        "tool_result": result.get("tool_result"),
    }


def process_message_sync(whatsapp_message: dict) -> dict:
    """
    Synchronous version of process_message.

    Args:
        whatsapp_message: WhatsApp message dictionary

    Returns:
        Response dictionary
    """
    return asyncio.run(process_message(whatsapp_message))
