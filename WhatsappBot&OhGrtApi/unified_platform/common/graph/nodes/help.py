"""
Help Node

Handles "what can you do" type questions with a comprehensive feature list.
"""

import logging
from common.graph.state import BotState

logger = logging.getLogger(__name__)

INTENT = "help"

HELP_RESPONSE = """I can help you with a variety of tasks tailored for Indian users! Here's what I can do for you:

• 🎫 *Events & Tickets*: Find IPL matches, concerts, comedy shows, and book tickets.
• 🏏 *IPL Matches*: Get upcoming IPL matches, team schedules (RCB, CSK, MI, etc.).
• 🎵 *Concerts*: Find live music shows and concerts near you.
• 😂 *Comedy Shows*: Discover standup comedy events.
• 🍽️ *Food & Restaurants*: Find restaurants by city and cuisine, popular dishes and ratings.
• 🚆 *Train Info*: Check live train status, PNR status, schedules, or trains between stations.
• 🔍 *Web Search*: Get the latest news, facts, or info not in my training data.
• 📝 *Fact-Checking*: Verify the truthfulness of any text or claim.
• 📅 *Reminders*: Set reminders for tasks, meetings, or events.
• 📍 *Nearby Places*: Find ATMs, hospitals, petrol pumps, or landmarks near you.
• 🖼️ *Media Creation*: Generate images, videos, or stickers based on your description.
• 📰 *Read Webpages*: Extract content from specific URLs.
• 🌤️ *Weather*: Get current weather and forecasts for any city.
• 🔮 *Astrology*: Daily horoscope, Kundli, compatibility matching, and predictions.
• ❓ *General Help*: Answer questions, explain concepts, or guide you through anything else!

Just let me know what you need — whether it's finding a restaurant, checking train timings, or even creating a fun sticker! 😊

Need help with something specific? Just ask!"""


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
