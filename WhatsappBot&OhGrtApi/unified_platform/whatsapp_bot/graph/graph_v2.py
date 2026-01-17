"""
Main Graph V2 - Domain-Based Routing Architecture

This version introduces:
1. Domain classification as first routing step
2. Sub-graphs for domain-specific processing
3. User profile persistence for session management
4. Cleaner separation of concerns

Architecture:
┌─────────────────────────────────────────┐
│           DOMAIN CLASSIFIER             │
│   (astrology/travel/utility/game/chat)  │
└──────────────────┬──────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
     ▼             ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ ASTRO   │ │ TRAVEL  │ │ UTILITY │
│ Graph   │ │ Handlers│ │ Handlers│
└─────────┘ └─────────┘ └─────────┘

To use this new architecture:
    from bot.graph_v2 import process_message_v2
"""

import asyncio
import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

# Timeout for sub-graph execution (seconds)
SUBGRAPH_TIMEOUT = 30

from whatsapp_bot.config import settings
from whatsapp_bot.state import BotState, WhatsAppMessage, create_initial_state

# Domain classifier
from whatsapp_bot.graphs.domain_classifier import classify_domain, DomainType

# Conversation context manager (WhatsApp-specific)
from bot.conversation_manager import enrich_with_context, get_conversation_manager

# Astrology sub-graph
from whatsapp_bot.graphs.astro_graph import get_astro_graph

# Travel handlers
from whatsapp_bot.graph.nodes.pnr_status import handle_pnr_status
from whatsapp_bot.graph.nodes.train_status import handle_train_status
from whatsapp_bot.graph.nodes.train_journey import handle_train_journey
from whatsapp_bot.graph.nodes.metro_ticket import handle_metro_ticket

# Utility handlers
from whatsapp_bot.graph.nodes.local_search import handle_local_search
from whatsapp_bot.graph.nodes.image_gen import handle_image_generation
from whatsapp_bot.graph.nodes.weather import handle_weather
from whatsapp_bot.graph.nodes.db_node import handle_db_query
from whatsapp_bot.graph.nodes.reminder_node import handle_reminder
from whatsapp_bot.graph.nodes.news_node import handle_news
from whatsapp_bot.graph.nodes.stock_price import handle_stock_price

# Game handler
from whatsapp_bot.graph.nodes.word_game import handle_word_game

# Chat handlers
from whatsapp_bot.graph.nodes.chat import handle_chat, handle_fallback

# Intent detection (for backward compatibility)
from whatsapp_bot.graph.nodes.intent import detect_intent


def route_by_domain(state: BotState) -> str:
    """
    Route to domain-specific handler based on classification.

    Args:
        state: Current bot state with domain field

    Returns:
        Node name to route to
    """
    domain = state.get("domain", "conversation")

    domain_to_node = {
        "astrology": "astrology_graph",
        "travel": "travel_router",
        "utility": "utility_router",
        "game": "game",
        "conversation": "chat",
    }

    return domain_to_node.get(domain, "chat")


def route_travel(state: BotState) -> dict:
    """
    Route within travel domain based on query.

    This is a node function that sets travel_intent for routing.

    Args:
        state: Current bot state

    Returns:
        Updated state with travel_intent
    """
    query = state.get("current_query", "").lower()

    if "pnr" in query:
        return {"travel_intent": "pnr_status"}
    elif "from" in query and "to" in query:
        return {"travel_intent": "train_journey"}
    elif "train" in query or "running status" in query:
        return {"travel_intent": "train_status"}
    elif "metro" in query:
        return {"travel_intent": "metro_ticket"}
    else:
        return {"travel_intent": "train_status"}


def select_travel_handler(state: BotState) -> str:
    """Select travel handler based on intent."""
    travel_intent = state.get("travel_intent", "train_status")
    return {
        "pnr_status": "pnr_status",
        "train_status": "train_status",
        "train_journey": "train_journey",
        "metro_ticket": "metro_ticket",
    }.get(travel_intent, "train_status")


def route_utility(state: BotState) -> dict:
    """
    Route within utility domain based on query.

    This is a node function that sets utility_intent for routing.

    Args:
        state: Current bot state

    Returns:
        Updated state with utility_intent
    """
    # Check if utility_intent is already set (e.g., for location messages)
    if state.get("utility_intent"):
        return {"utility_intent": state.get("utility_intent")}

    query = state.get("current_query", "").lower()

    if any(kw in query for kw in ["weather", "temperature", "forecast", "rain"]):
        return {"utility_intent": "weather"}
    elif any(kw in query for kw in ["stock price", "share price", "stock", "portfolio"]):
        return {"utility_intent": "stock_price"}
    elif any(kw in query for kw in ["news", "headlines", "breaking"]):
        return {"utility_intent": "news"}
    elif any(kw in query for kw in ["generate image", "create image", "draw", "picture"]):
        return {"utility_intent": "image"}
    elif any(kw in query for kw in ["remind", "reminder", "alarm"]):
        return {"utility_intent": "reminder"}
    elif any(kw in query for kw in ["search", "find", "near me", "nearby"]):
        return {"utility_intent": "local_search"}
    # Check for place-based queries (hospitals, restaurants, etc.)
    elif any(kw in query for kw in [
        "hospital", "restaurant", "hotel", "atm", "bank", "pharmacy",
        "petrol", "gas station", "mall", "shop", "store", "clinic",
        "school", "college", "gym", "park", "temple", "mosque", "church",
        "police", "airport", "railway station", "bus stand", "metro station"
    ]) and any(loc in query for loc in ["in", "at", "near", "around"]):
        return {"utility_intent": "local_search"}
    else:
        return {"utility_intent": "db_query"}


def select_utility_handler(state: BotState) -> str:
    """Select utility handler based on intent."""
    utility_intent = state.get("utility_intent", "db_query")
    return {
        "weather": "weather",
        "stock_price": "stock_price",
        "news": "news",
        "image": "image_gen",
        "reminder": "reminder",
        "local_search": "local_search",
        "db_query": "db_query",
    }.get(utility_intent, "db_query")


def check_fallback(state: BotState) -> Literal["fallback", "end"]:
    """Check if fallback is needed."""
    if state.get("should_fallback", False):
        return "fallback"
    return "end"


async def enrich_context_node(state: BotState) -> dict:
    """
    Enrich state with conversation context.

    This handles WhatsApp-specific challenges:
    - Topic switching without explicit "new chat"
    - Multi-turn flows (birth details collection)
    - Context expiry for stale conversations

    Args:
        state: Current bot state

    Returns:
        Enriched state with context info
    """
    return await enrich_with_context(state)


def create_graph_v2() -> StateGraph:
    """
    Create the main graph with domain-based routing.

    Returns:
        StateGraph (not compiled)
    """
    graph = StateGraph(BotState)

    # =========================================================================
    # DOMAIN CLASSIFICATION & CONTEXT ENRICHMENT
    # =========================================================================
    graph.add_node("classify_domain", classify_domain)
    graph.add_node("enrich_context", enrich_context_node)

    # =========================================================================
    # ASTROLOGY DOMAIN (Sub-graph)
    # =========================================================================
    # The astro graph handles its own intent detection and routing
    astro_graph = get_astro_graph()

    async def run_astro_graph(state: BotState) -> dict:
        """Execute astrology sub-graph with timeout protection."""
        try:
            result = await asyncio.wait_for(
                astro_graph.ainvoke(state),
                timeout=SUBGRAPH_TIMEOUT
            )
            return {
                "response_text": result.get("response_text", ""),
                "response_type": result.get("response_type", "text"),
                "tool_result": result.get("tool_result"),
                "should_fallback": result.get("should_fallback", False),
                "intent": result.get("intent", "astrology"),
            }
        except asyncio.TimeoutError:
            logger.error(f"Astrology sub-graph timed out after {SUBGRAPH_TIMEOUT}s")
            return {
                "response_text": "Sorry, the request took too long. Please try again.",
                "response_type": "text",
                "should_fallback": False,
                "intent": "astrology",
                "error": "timeout",
            }
        except Exception as e:
            logger.error(f"Error in astrology sub-graph: {e}", exc_info=True)
            return {
                "response_text": "Sorry, something went wrong. Please try again.",
                "response_type": "text",
                "should_fallback": True,
                "intent": "astrology",
                "error": str(e),
            }

    graph.add_node("astrology_graph", run_astro_graph)

    # =========================================================================
    # TRAVEL DOMAIN
    # =========================================================================
    graph.add_node("travel_router", route_travel)
    graph.add_node("pnr_status", handle_pnr_status)
    graph.add_node("train_status", handle_train_status)
    graph.add_node("train_journey", handle_train_journey)
    graph.add_node("metro_ticket", handle_metro_ticket)

    # =========================================================================
    # UTILITY DOMAIN
    # =========================================================================
    graph.add_node("utility_router", route_utility)
    graph.add_node("weather", handle_weather)
    graph.add_node("stock_price", handle_stock_price)
    graph.add_node("news", handle_news)
    graph.add_node("image_gen", handle_image_generation)
    graph.add_node("reminder", handle_reminder)
    graph.add_node("local_search", handle_local_search)
    graph.add_node("db_query", handle_db_query)

    # =========================================================================
    # GAME DOMAIN
    # =========================================================================
    graph.add_node("game", handle_word_game)

    # =========================================================================
    # CONVERSATION (Fallback)
    # =========================================================================
    graph.add_node("chat", handle_chat)
    graph.add_node("fallback", handle_fallback)

    # =========================================================================
    # EDGES
    # =========================================================================

    # Start -> Domain Classification -> Context Enrichment
    graph.add_edge(START, "classify_domain")
    graph.add_edge("classify_domain", "enrich_context")

    # Context Enrichment -> Domain Handlers (based on domain)
    graph.add_conditional_edges(
        "enrich_context",
        route_by_domain,
        {
            "astrology_graph": "astrology_graph",
            "travel_router": "travel_router",
            "utility_router": "utility_router",
            "game": "game",
            "chat": "chat",
        }
    )

    # Astrology graph -> End (already handled internally)
    graph.add_conditional_edges(
        "astrology_graph",
        check_fallback,
        {"fallback": "fallback", "end": END}
    )

    # Travel router -> Travel handlers
    graph.add_conditional_edges(
        "travel_router",
        select_travel_handler,
        {
            "pnr_status": "pnr_status",
            "train_status": "train_status",
            "train_journey": "train_journey",
            "metro_ticket": "metro_ticket",
        }
    )

    # Utility router -> Utility handlers
    graph.add_conditional_edges(
        "utility_router",
        select_utility_handler,
        {
            "weather": "weather",
            "stock_price": "stock_price",
            "news": "news",
            "image_gen": "image_gen",
            "reminder": "reminder",
            "local_search": "local_search",
            "db_query": "db_query",
        }
    )

    # All terminal handlers -> Check fallback -> End
    terminal_nodes = [
        "pnr_status", "train_status", "train_journey", "metro_ticket",
        "weather", "stock_price", "news", "image_gen", "reminder", "local_search", "db_query",
        "game", "chat"
    ]

    for node in terminal_nodes:
        graph.add_conditional_edges(
            node,
            check_fallback,
            {"fallback": "fallback", "end": END}
        )

    # Fallback -> End
    graph.add_edge("fallback", END)

    return graph


def get_compiled_graph_v2(checkpointer=None):
    """
    Get a compiled graph ready for execution.

    Args:
        checkpointer: Optional checkpointer instance

    Returns:
        Compiled graph
    """
    graph = create_graph_v2()
    return graph.compile(checkpointer=checkpointer)


# Singleton instance
_graph_v2 = None


def get_graph_v2():
    """
    Get or create the singleton graph instance.

    Returns:
        Compiled LangGraph instance
    """
    global _graph_v2
    if _graph_v2 is None:
        # Create DB URI from settings
        db_uri = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

        # Initialize connection pool
        pool = ConnectionPool(conninfo=db_uri, max_size=20)

        # Initialize checkpointer
        checkpointer = PostgresSaver(pool)

        # Ensure schema exists
        checkpointer.setup()

        _graph_v2 = get_compiled_graph_v2(checkpointer=checkpointer)
    return _graph_v2


async def process_message_v2(whatsapp_message: dict) -> dict:
    """
    Process a WhatsApp message through the V2 graph.

    This uses domain-based routing for cleaner architecture.

    Args:
        whatsapp_message: WhatsApp message dictionary

    Returns:
        Response dictionary
    """
    graph = get_graph_v2()

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
        )
    )

    # Use phone number as thread ID for persistence
    thread_id = whatsapp_message.get("from_number", "default_thread")
    config = {"configurable": {"thread_id": thread_id}}

    # Execute the graph
    result = await graph.ainvoke(initial_state, config=config)

    return {
        "response_text": result.get("response_text", ""),
        "response_type": result.get("response_type", "text"),
        "response_media_url": result.get("response_media_url"),
        "intent": result.get("intent", "unknown"),
        "domain": result.get("domain", "unknown"),
        "error": result.get("error"),
        "tool_result": result.get("tool_result"),
    }


# =============================================================================
# COMPARISON: V1 vs V2
# =============================================================================
"""
V1 Architecture (current graph.py):
- 25+ nodes at same level
- Direct intent -> node routing
- All intents detected in one place
- Flat structure

V2 Architecture (this file):
- Domain classification first
- Sub-graphs for complex domains (astrology)
- Hierarchical routing
- User profile persistence
- Cleaner separation

Migration path:
1. Test V2 alongside V1
2. Gradually switch traffic
3. Remove V1 when stable

To switch to V2 in main.py:
    # Old
    from bot.graph import process_message

    # New
    from bot.graph_v2 import process_message_v2 as process_message
"""
