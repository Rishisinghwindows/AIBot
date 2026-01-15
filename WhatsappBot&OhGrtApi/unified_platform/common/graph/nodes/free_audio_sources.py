"""
Free Audio Sources Node

Returns curated free/royalty-free audio sources.
"""

import logging
from typing import Dict, List

from common.graph.state import BotState

logger = logging.getLogger(__name__)

INTENT = "free_audio_sources"


def _get_sources(lang: str) -> List[str]:
    if lang == "hi":
        return [
            "*Free Audio Sources (फ्री/रॉयल्टी‑फ्री)*",
            "1) Free Music Archive — https://freemusicarchive.org/",
            "2) Incompetech — https://incompetech.com/music/",
            "3) YouTube Audio Library — https://www.youtube.com/audiolibrary",
            "4) Pixab​ay Music — https://pixabay.com/music/",
            "5) Openverse (audio) — https://openverse.org/audio",
        ]
    return [
        "*Free Audio Sources (Free/Royalty‑free)*",
        "1) Free Music Archive — https://freemusicarchive.org/",
        "2) Incompetech — https://incompetech.com/music/",
        "3) YouTube Audio Library — https://www.youtube.com/audiolibrary",
        "4) Pixabay Music — https://pixabay.com/music/",
        "5) Openverse (audio) — https://openverse.org/audio",
    ]


async def handle_free_audio_sources(state: BotState) -> dict:
    detected_lang = state.get("detected_language", "en")
    lines = _get_sources(detected_lang)
    if detected_lang == "hi":
        lines.append("\nक्या आप किसी खास प्रकार (भक्ति/गीत/इंस्ट्रूमेंटल) की तलाश में हैं?")
    else:
        lines.append("\nLooking for a specific type (bhakti/song/instrumental)?")

    return {
        "response_text": "\n".join(lines),
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
