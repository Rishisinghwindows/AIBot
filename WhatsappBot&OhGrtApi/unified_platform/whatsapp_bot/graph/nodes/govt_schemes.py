"""
Government Schemes Node

Fetches state-wise or central government schemes via web search and formats links + short summaries.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from whatsapp_bot.state import BotState
from common.tools.serper_search import search_google
from common.utils.response_formatter import sanitize_error

logger = logging.getLogger(__name__)

INTENT = "govt_schemes"

STATE_ALIASES = {
    "delhi": "Delhi",
    "bihar": "Bihar",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "maharashtra": "Maharashtra",
    "karnataka": "Karnataka",
    "tamil nadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    "rajasthan": "Rajasthan",
    "gujarat": "Gujarat",
    "kerala": "Kerala",
    "telangana": "Telangana",
    "andhra pradesh": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    "jharkhand": "Jharkhand",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "haryana": "Haryana",
    "chhattisgarh": "Chhattisgarh",
    "assam": "Assam",
    "jammu": "Jammu & Kashmir",
    "kashmir": "Jammu & Kashmir",
}


def _extract_state(query: str) -> Optional[str]:
    query_lower = query.lower()
    for key, label in STATE_ALIASES.items():
        if key in query_lower:
            return label
    match = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)$", query_lower)
    if match:
        candidate = match.group(1).strip()
        return candidate.title() if candidate else None
    return None


def _build_search_query(state: Optional[str]) -> str:
    if state:
        return (
            f"government schemes {state} yojana benefits eligibility "
            "site:gov.in OR site:nic.in OR site:india.gov.in"
        )
    return (
        "central government schemes yojana benefits eligibility "
        "site:india.gov.in OR site:gov.in"
    )


def _format_items(results: List[Dict[str, str]], lang: str, limit: int = 8) -> List[str]:
    lines = []
    for item in results[:limit]:
        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        snippet = item.get("snippet", "").strip()

        if not title and not link:
            continue

        if title:
            lines.append(f"*{title}*")
        if snippet:
            short = snippet[:160].rstrip()
            lines.append(f"_{short}_")
        if link:
            if lang == "hi":
                lines.append(f"👉 लिंक: {link}")
            else:
                lines.append(f"👉 Link: {link}")
        lines.append("")
    return lines


async def handle_govt_schemes(state: BotState) -> dict:
    user_message = state.get("current_query", "").strip() or state.get("whatsapp_message", {}).get("text", "")
    detected_lang = state.get("detected_language", "en")

    entities = state.get("extracted_entities", {}) or {}
    is_followup = bool(entities.get("followup"))
    state_name = _extract_state(user_message or "")
    search_query = _build_search_query(state_name)

    try:
        max_results = 20 if is_followup else 10
        result = await search_google(query=search_query, max_results=max_results, country="in", locale="en")
        if not result["success"]:
            error_msg = sanitize_error(result.get("error", ""), "search")
            return {
                "tool_result": result,
                "response_text": error_msg or "Could not fetch schemes right now.",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        results = (result.get("data") or {}).get("results", [])
        date_str = datetime.now().strftime("%d %B %Y")

        if detected_lang == "hi":
            header = f"सरकारी योजनाएं ({date_str})"
            scope = f"{state_name} के लिए" if state_name else "केंद्र सरकार के लिए"
            lines = [f"📌 *{header}* — {scope}\n"]
        else:
            header = f"Government schemes ({date_str})"
            scope = f"for {state_name}" if state_name else "for central government"
            lines = [f"📌 *{header}* — {scope}\n"]

        limit = 12 if is_followup else 8
        lines.extend(_format_items(results, detected_lang, limit=limit))
        if detected_lang == "hi":
            lines.append("क्या आप किसी खास योजना या विभाग की जानकारी चाहते हैं?")
        else:
            lines.append("Want details for a specific scheme or department?")

        response_text = "\n".join([line for line in lines if line is not None])
        return {
            "tool_result": result,
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Govt schemes handler error: {e}")
        return {
            "response_text": "Could not fetch schemes right now.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
