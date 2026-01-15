"""
Cricket Score Node

Fetches live cricket score updates via web search and formats a concise summary.
"""

import logging
from datetime import datetime
from typing import Dict, List

from common.graph.state import BotState
from common.tools.serper_search import search_google
from common.utils.response_formatter import sanitize_error

logger = logging.getLogger(__name__)

INTENT = "cricket_score"


def _format_items(results: List[Dict[str, str]], lang: str) -> List[str]:
    lines: List[str] = []
    for item in results[:6]:
        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        snippet = item.get("snippet", "").strip()

        if not title and not link:
            continue

        if title:
            lines.append(f"*{title}*")
        if snippet:
            short = snippet[:180].rstrip()
            lines.append(f"_{short}_")
        if link:
            if lang == "hi":
                lines.append(f"👉 लिंक: {link}")
            else:
                lines.append(f"👉 Link: {link}")
        lines.append("")
    return lines


async def handle_cricket_score(state: BotState) -> dict:
    detected_lang = state.get("detected_language", "en")
    query = (
        "live cricket score scorecard site:cricbuzz.com OR site:cricheroes.com OR site:espncricinfo.com"
    )

    try:
        result = await search_google(query=query, max_results=8, country="in", locale="en")
        if not result["success"]:
            error_msg = sanitize_error(result.get("error", ""), "search")
            return {
                "tool_result": result,
                "response_text": error_msg or "Could not fetch cricket scores right now.",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        results = (result.get("data") or {}).get("results", [])
        date_str = datetime.now().strftime("%d %B %Y")

        if detected_lang == "hi":
            header = f"क्रिकेट स्कोर अपडेट्स ({date_str})"
            lines = [f"🏏 *{header}*\n"]
        else:
            header = f"Cricket score updates ({date_str})"
            lines = [f"🏏 *{header}*\n"]

        lines.extend(_format_items(results, detected_lang))
        if detected_lang == "hi":
            lines.append("क्या आप किसी खास मैच या टीम का स्कोर चाहते हैं?")
        else:
            lines.append("Want the score for a specific match or team?")

        response_text = "\n".join([line for line in lines if line is not None])
        return {
            "tool_result": result,
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Cricket score handler error: {e}")
        return {
            "response_text": "Could not fetch cricket scores right now.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
