"""
Free Audio Sources Node

Returns a curated list of free/royalty-free audio sources.
"""

import logging
from datetime import datetime

from whatsapp_bot.state import BotState

logger = logging.getLogger(__name__)

INTENT = "free_audio_sources"


async def handle_free_audio_sources(state: BotState) -> dict:
    detected_lang = state.get("detected_language", "en")
    date_str = datetime.now().strftime("%d %B %Y")

    if detected_lang == "hi":
        lines = [
            f"🎵 *फ्री ऑडियो सोर्सेस* ({date_str})",
            "",
            "• YouTube Audio Library — https://www.youtube.com/audiolibrary",
            "• Pixabay Music — https://pixabay.com/music/",
            "• Free Music Archive — https://freemusicarchive.org/",
            "• Jamendo (फ्री ट्रैक्स) — https://www.jamendo.com/",
            "• ccMixter — https://ccmixter.org/",
            "• Openverse (CC सर्च) — https://openverse.org/audio",
            "• Wikimedia Commons — https://commons.wikimedia.org/wiki/Category:Audio",
            "• Internet Archive — https://archive.org/details/audio",
            "",
            "नोट: हर ट्रैक की लाइसेंस/अट्रीब्यूशन शर्तें जरूर चेक करें।",
        ]
    else:
        lines = [
            f"🎵 *Free Audio Sources* ({date_str})",
            "",
            "• YouTube Audio Library — https://www.youtube.com/audiolibrary",
            "• Pixabay Music — https://pixabay.com/music/",
            "• Free Music Archive — https://freemusicarchive.org/",
            "• Jamendo (free tracks) — https://www.jamendo.com/",
            "• ccMixter — https://ccmixter.org/",
            "• Openverse (CC search) — https://openverse.org/audio",
            "• Wikimedia Commons — https://commons.wikimedia.org/wiki/Category:Audio",
            "• Internet Archive — https://archive.org/details/audio",
            "",
            "Note: Always verify license/attribution requirements per track.",
        ]

    return {
        "response_text": "\n".join(lines),
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
