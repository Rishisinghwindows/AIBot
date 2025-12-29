"""
LangGraph Node Functions

Each node handles a specific intent or processing step.
"""

from bot.nodes.intent import detect_intent
from bot.nodes.chat import handle_chat, handle_fallback
from bot.nodes.local_search import handle_local_search
from bot.nodes.image_gen import handle_image_generation
from bot.nodes.pnr_status import handle_pnr_status
from bot.nodes.train_status import handle_train_status
from bot.nodes.metro_ticket import handle_metro_ticket

__all__ = [
    "detect_intent",
    "handle_chat",
    "handle_fallback",
    "handle_local_search",
    "handle_image_generation",
    "handle_pnr_status",
    "handle_train_status",
    "handle_metro_ticket",
]
