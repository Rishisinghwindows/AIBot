"""
WhatsApp LangGraph Workflow

Main workflow for processing WhatsApp messages using intent-based routing.
Ported from D23Bot for unified multi-client architecture.

Context Persistence:
- Uses PostgresSaver for production (durable across restarts)
- Falls back to MemorySaver for development/lite mode
- Thread IDs ensure conversation continuity
"""

from typing import Literal, Optional
from app.logger import logger

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.config import get_settings
from app.graph.state import (
    BotState,
    WhatsAppMessage,
    ClientType,
    create_initial_state,
)
from app.graph.nodes.intent import detect_intent
from app.graph.nodes.chat import handle_chat, handle_fallback
from app.graph.nodes.weather_node import handle_weather
from app.graph.nodes.news_node import handle_news
from app.graph.nodes.travel_node import handle_pnr_status, handle_train_status
from app.graph.nodes.image_node import handle_image_generation
from app.graph.nodes.astro_node import (
    handle_horoscope,
    handle_birth_chart,
    handle_numerology,
    handle_tarot,
    handle_panchang,
    handle_dosha,
    handle_kundli_matching,
    handle_life_prediction,
    handle_ask_astrologer,
)
from app.graph.nodes.schedule_node import handle_schedule
from app.graph.nodes.help_node import handle_help


def route_by_intent(state: BotState) -> str:
    """
    Conditional routing function based on detected intent.

    Args:
        state: Current bot state with intent field

    Returns:
        Name of the next node to execute
    """
    intent = state.get("intent", "chat")

    # Map intents to node names
    intent_to_node = {
        # Core
        "chat": "chat",
        "unknown": "chat",
        # Travel
        "pnr_status": "pnr_status",
        "train_status": "train_status",
        "metro_ticket": "chat",  # Route to chat for now
        # Weather & News
        "weather": "weather",
        "get_news": "get_news",
        # Image
        "image": "image_gen",
        # Astrology
        "get_horoscope": "get_horoscope",
        "birth_chart": "birth_chart",
        "kundli_matching": "kundli_matching",
        "ask_astrologer": "ask_astrologer",
        "numerology": "numerology",
        "tarot_reading": "tarot_reading",
        "dosha_check": "check_dosha",
        "check_dosha": "check_dosha",
        "life_prediction": "life_prediction",
        "get_panchang": "get_panchang",
        "get_remedy": "ask_astrologer",  # Route to ask_astrologer
        "find_muhurta": "get_panchang",  # Related to panchang
        # Other features
        "local_search": "chat",  # Route to chat for now
        "word_game": "chat",  # Route to chat for now
        "set_reminder": "set_schedule",  # Route to schedule node
        "subscription": "chat",  # Route to chat for now
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


def create_whatsapp_graph() -> StateGraph:
    """
    Create the LangGraph workflow for WhatsApp message processing.

    Returns:
        StateGraph (not compiled)
    """
    # Initialize the state graph with our state type
    graph = StateGraph(BotState)

    # Add all nodes
    graph.add_node("intent_detection", detect_intent)
    graph.add_node("chat", handle_chat)
    graph.add_node("fallback", handle_fallback)

    # Feature nodes
    graph.add_node("weather", handle_weather)
    graph.add_node("get_news", handle_news)
    graph.add_node("pnr_status", handle_pnr_status)
    graph.add_node("train_status", handle_train_status)
    graph.add_node("image_gen", handle_image_generation)

    # Astrology nodes
    graph.add_node("get_horoscope", handle_horoscope)
    graph.add_node("birth_chart", handle_birth_chart)
    graph.add_node("numerology", handle_numerology)
    graph.add_node("tarot_reading", handle_tarot)
    graph.add_node("get_panchang", handle_panchang)
    graph.add_node("check_dosha", handle_dosha)
    graph.add_node("kundli_matching", handle_kundli_matching)
    graph.add_node("life_prediction", handle_life_prediction)
    graph.add_node("ask_astrologer", handle_ask_astrologer)

    # Schedule node
    graph.add_node("set_schedule", handle_schedule)

    # Define edges
    # Start -> Intent Detection
    graph.add_edge(START, "intent_detection")

    # Intent Detection -> Route to appropriate handler
    graph.add_conditional_edges(
        "intent_detection",
        route_by_intent,
        {
            "chat": "chat",
            "weather": "weather",
            "get_news": "get_news",
            "pnr_status": "pnr_status",
            "train_status": "train_status",
            "image_gen": "image_gen",
            "get_horoscope": "get_horoscope",
            "birth_chart": "birth_chart",
            "numerology": "numerology",
            "tarot_reading": "tarot_reading",
            "get_panchang": "get_panchang",
            "check_dosha": "check_dosha",
            "kundli_matching": "kundli_matching",
            "life_prediction": "life_prediction",
            "ask_astrologer": "ask_astrologer",
            "set_schedule": "set_schedule",
        },
    )

    # All handler nodes can go to fallback or end
    handler_nodes = [
        "chat",
        "weather",
        "get_news",
        "pnr_status",
        "train_status",
        "image_gen",
        "get_horoscope",
        "birth_chart",
        "numerology",
        "tarot_reading",
        "get_panchang",
        "check_dosha",
        "kundli_matching",
        "life_prediction",
        "ask_astrologer",
        "set_schedule",
    ]

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
        checkpointer: Optional checkpointer instance for conversation persistence

    Returns:
        Compiled graph
    """
    graph = create_whatsapp_graph()
    return graph.compile(checkpointer=checkpointer)


# Singleton instance
_whatsapp_graph = None
_memory_saver = None


def _create_postgres_checkpointer(settings):
    """
    Create an async PostgresSaver checkpointer for durable context persistence.

    Args:
        settings: Application settings

    Returns:
        AsyncPostgresSaver instance or None if unavailable
    """
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool
        import asyncio

        db_uri = (
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )

        async def create_checkpointer():
            pool = AsyncConnectionPool(conninfo=db_uri, max_size=20, open=False)
            await pool.open()
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            return checkpointer

        # Run async setup
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, we can't use run_until_complete
            # Just use MemorySaver as fallback
            logger.warning("async_context_detected_using_memory_saver")
            return None
        except RuntimeError:
            # No running loop, we can create one
            checkpointer = asyncio.run(create_checkpointer())
            logger.info("async_postgres_checkpointer_initialized", db_host=settings.postgres_host)
            return checkpointer

    except ImportError as e:
        logger.warning(f"AsyncPostgresSaver not available (missing deps): {e}")
        return None
    except Exception as e:
        logger.warning(f"AsyncPostgresSaver setup failed: {e}")
        return None


def _is_database_available(settings) -> bool:
    """Check if PostgreSQL database is reachable."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((settings.postgres_host, settings.postgres_port))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_whatsapp_graph():
    """
    Get or create the singleton WhatsApp graph instance.

    Uses MemorySaver for now to avoid async PostgreSQL issues.
    Conversation context is stored in PostgreSQL via context_service separately.

    Returns:
        Compiled LangGraph instance
    """
    global _whatsapp_graph, _memory_saver

    if _whatsapp_graph is None:
        settings = get_settings()

        # Use MemorySaver for graph checkpointing
        # (Conversation history is persisted via context_service in web/router.py)
        _memory_saver = MemorySaver()
        _whatsapp_graph = get_compiled_graph(checkpointer=_memory_saver)
        logger.info(
            "whatsapp_graph_initialized",
            checkpointer="memory",
            note="conversation_history_persisted_via_context_service",
        )

    return _whatsapp_graph


def reset_graph():
    """
    Reset the graph singleton. Useful for testing or reconfiguration.
    """
    global _whatsapp_graph, _memory_saver
    _whatsapp_graph = None
    _memory_saver = None
    logger.info("whatsapp_graph_reset")


async def process_whatsapp_message(
    whatsapp_message: dict,
    user_id: Optional[str] = None,
    user_birth_details: Optional[dict] = None,
    user_language: Optional[str] = None,
) -> dict:
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
            - user_name: Optional[str]
        user_id: Optional user ID from database
        user_birth_details: Optional birth details for astrology
        user_language: Optional preferred language

    Returns:
        Response dictionary with:
            - response_text: str
            - response_type: str ("text", "image", "interactive", "audio")
            - response_media_url: Optional[str]
            - buttons: Optional[list]
            - intent: str
            - error: Optional[str]
    """
    graph = get_whatsapp_graph()

    # Create initial state
    message = WhatsAppMessage(
        message_id=whatsapp_message.get("message_id", ""),
        from_number=whatsapp_message.get("from_number", ""),
        phone_number_id=whatsapp_message.get("phone_number_id", ""),
        timestamp=whatsapp_message.get("timestamp", ""),
        message_type=whatsapp_message.get("message_type", "text"),
        text=whatsapp_message.get("text"),
        media_id=whatsapp_message.get("media_id"),
        user_name=whatsapp_message.get("user_name"),
    )

    initial_state = create_initial_state(
        message=message,
        client_type=ClientType.WHATSAPP,
        user_id=user_id,
        user_birth_details=user_birth_details,
        user_language=user_language,
    )

    # Use phone number as thread ID for conversation persistence
    thread_id = whatsapp_message.get("from_number", "default_thread")
    config = {"configurable": {"thread_id": thread_id}}

    # Execute the graph
    try:
        result = await graph.ainvoke(initial_state, config=config)

        return {
            "response_text": result.get("response_text", ""),
            "response_type": result.get("response_type", "text"),
            "response_media_url": result.get("response_media_url"),
            "buttons": result.get("buttons"),
            "intent": result.get("intent", "unknown"),
            "error": result.get("error"),
            "tool_result": result.get("tool_result"),
        }
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"WhatsApp graph execution error: {e}", exc_info=True)
        logger.error(f"Full traceback: {error_traceback}")
        return {
            "response_text": (
                "I'm having trouble processing your message right now.\n\n"
                "Please try again in a moment, or try one of these:\n"
                "- Weather: 'Weather in Delhi'\n"
                "- Horoscope: 'Aries horoscope'\n"
                "- PNR: 'PNR 1234567890'"
            ),
            "response_type": "text",
            "response_media_url": None,
            "buttons": None,
            "intent": "error",
            "error": str(e),
            "tool_result": None,
        }


def process_whatsapp_message_sync(
    whatsapp_message: dict,
    user_id: Optional[str] = None,
    user_birth_details: Optional[dict] = None,
    user_language: Optional[str] = None,
) -> dict:
    """
    Synchronous version of process_whatsapp_message.

    Args:
        whatsapp_message: WhatsApp message dictionary
        user_id: Optional user ID
        user_birth_details: Optional birth details
        user_language: Optional language preference

    Returns:
        Response dictionary
    """
    graph = get_whatsapp_graph()

    # Create initial state
    message = WhatsAppMessage(
        message_id=whatsapp_message.get("message_id", ""),
        from_number=whatsapp_message.get("from_number", ""),
        phone_number_id=whatsapp_message.get("phone_number_id", ""),
        timestamp=whatsapp_message.get("timestamp", ""),
        message_type=whatsapp_message.get("message_type", "text"),
        text=whatsapp_message.get("text"),
        media_id=whatsapp_message.get("media_id"),
        user_name=whatsapp_message.get("user_name"),
    )

    initial_state = create_initial_state(
        message=message,
        client_type=ClientType.WHATSAPP,
        user_id=user_id,
        user_birth_details=user_birth_details,
        user_language=user_language,
    )

    # Use phone number as thread ID for persistence
    thread_id = whatsapp_message.get("from_number", "default_thread")
    config = {"configurable": {"thread_id": thread_id}}

    # Execute the graph synchronously
    try:
        result = graph.invoke(initial_state, config=config)

        return {
            "response_text": result.get("response_text", ""),
            "response_type": result.get("response_type", "text"),
            "response_media_url": result.get("response_media_url"),
            "buttons": result.get("buttons"),
            "intent": result.get("intent", "unknown"),
            "error": result.get("error"),
            "tool_result": result.get("tool_result"),
        }
    except Exception as e:
        logger.error(f"WhatsApp graph execution error: {e}")
        return {
            "response_text": "I'm having trouble right now. Please try again.",
            "response_type": "text",
            "intent": "error",
            "error": str(e),
        }
