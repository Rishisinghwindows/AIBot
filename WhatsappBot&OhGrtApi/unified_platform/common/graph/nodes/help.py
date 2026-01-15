"""
Help Node

Handles "what can you do" type questions with a comprehensive feature list.
"""

import logging
from common.graph.state import BotState

logger = logging.getLogger(__name__)

INTENT = "help"

HELP_RESPONSE = """👋 Welcome to D23AI
I can help you with everyday things — just ask in your language.
Here’s what I can do for you:
• 🍽️ Find restaurants by city and cuisine
• 🚆 Check live train status & PNR updates
• 🏛️ Get government jobs & schemes in your language
• 🏏 Get live cricket score updates
• 🌤️ Weather updates for any city
• 🔮 Astrology: horoscope, kundli & predictions
• 🖼️ Generate images from descriptions
• 📅 Set reminders for tasks & meetings
• 📍 Find nearby ATMs, hospitals & places
• 📰 Latest news headlines
• 📝 Fact-check news and claims
• 🎫 Find IPL matches, concerts & events
And this is just the start.
👉 Ask me anything, anytime."""


def handle_help(state: BotState) -> dict:
    """
    Handle help/what can you do queries.

    Args:
        state: Current bot state

    Returns:
        Updated state with help response
    """
    return {
        "response_text": HELP_RESPONSE,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
