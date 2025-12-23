"""
Graph Package

Contains LangGraph workflow definitions for different processing pipelines.
"""

from app.graph.whatsapp_graph import (
    get_whatsapp_graph,
    process_whatsapp_message,
    process_whatsapp_message_sync,
    create_whatsapp_graph,
)
from app.graph.state import (
    BotState,
    WhatsAppMessage,
    ClientType,
    create_initial_state,
    message_from_ios,
    message_from_web,
)

__all__ = [
    # WhatsApp graph
    "get_whatsapp_graph",
    "process_whatsapp_message",
    "process_whatsapp_message_sync",
    "create_whatsapp_graph",
    # State types
    "BotState",
    "WhatsAppMessage",
    "ClientType",
    "create_initial_state",
    "message_from_ios",
    "message_from_web",
]
