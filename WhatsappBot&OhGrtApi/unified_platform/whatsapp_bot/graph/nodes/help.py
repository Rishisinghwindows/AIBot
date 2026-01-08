"""
Help Node

Handles "what can you do" type questions with a comprehensive feature list.
Supports multilingual responses (11+ Indian languages).
"""

import logging
from typing import Dict

from common.graph.state import BotState
from common.i18n.responses import get_help_response

logger = logging.getLogger(__name__)

INTENT = "help"


async def handle_help(state: BotState) -> Dict:
    """
    Handle help/what can you do queries.
    Returns response in user's detected language.

    Args:
        state: Current bot state

    Returns:
        Updated state with help response
    """
    # Get user's language (default to English)
    detected_lang = state.get("detected_language", "en")

    # Get localized help response
    response = get_help_response(detected_lang)

    return {
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
        "route_log": state.get("route_log", []) + ["help:displayed"],
    }
