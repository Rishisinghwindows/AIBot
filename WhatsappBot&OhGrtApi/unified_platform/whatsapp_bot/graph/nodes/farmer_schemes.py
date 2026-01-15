"""
Farmer Schemes Node

Fetches farmer-focused government schemes/subsidies via web search
and formats links + short summaries.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from whatsapp_bot.state import BotState
from common.tools.serper_search import search_google
from common.utils.response_formatter import sanitize_error

logger = logging.getLogger(__name__)

INTENT = "farmer_schemes"

FALLBACK_LINKS_EN = [
    {
        "title": "PM-KISAN Samman Nidhi",
        "snippet": "Direct income support for eligible farmers.",
        "link": "https://pmkisan.gov.in",
    },
    {
        "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "snippet": "Crop insurance coverage against losses.",
        "link": "https://pmfby.gov.in",
    },
    {
        "title": "Soil Health Card Scheme",
        "snippet": "Soil testing and crop advisory support.",
        "link": "https://soilhealth.dac.gov.in",
    },
    {
        "title": "Kisan Credit Card (KCC)",
        "snippet": "Easy credit access for agriculture needs.",
        "link": "https://www.kisan.gov.in",
    },
    {
        "title": "e-NAM (National Agriculture Market)",
        "snippet": "Online trading platform for agri produce.",
        "link": "https://enam.gov.in",
    },
    {
        "title": "Department of Agriculture & Farmers Welfare",
        "snippet": "Official portal with schemes and updates.",
        "link": "https://agriwelfare.gov.in",
    },
]

FALLBACK_LINKS_HI = [
    {
        "title": "पीएम-किसान सम्मान निधि",
        "snippet": "योग्य किसानों को प्रत्यक्ष आय सहायता।",
        "link": "https://pmkisan.gov.in",
    },
    {
        "title": "प्रधानमंत्री फसल बीमा योजना (PMFBY)",
        "snippet": "फसल नुकसान पर बीमा सुरक्षा।",
        "link": "https://pmfby.gov.in",
    },
    {
        "title": "मृदा स्वास्थ्य कार्ड योजना",
        "snippet": "मिट्टी जांच और फसल सलाह।",
        "link": "https://soilhealth.dac.gov.in",
    },
    {
        "title": "किसान क्रेडिट कार्ड (KCC)",
        "snippet": "कृषि जरूरतों के लिए आसान ऋण।",
        "link": "https://www.kisan.gov.in",
    },
    {
        "title": "ई-नाम (राष्ट्रीय कृषि बाजार)",
        "snippet": "कृषि उपज का ऑनलाइन बाजार।",
        "link": "https://enam.gov.in",
    },
    {
        "title": "कृषि एवं किसान कल्याण विभाग",
        "snippet": "योजनाएं और अपडेट का सरकारी पोर्टल।",
        "link": "https://agriwelfare.gov.in",
    },
]

STATE_ALIASES = {
    "andhra pradesh": "Andhra Pradesh",
    "andhrapradesh": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "delhi": "Delhi",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "kerla": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "mp": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "telangana": "Telangana",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
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
    base = "farmer agriculture kisan subsidy schemes benefits eligibility"
    if state:
        return (
            f"{base} {state} government yojana "
            "site:gov.in OR site:nic.in OR site:india.gov.in"
        )
    return (
        f"{base} central government yojana "
        "site:india.gov.in OR site:gov.in"
    )


def _format_items(results: List[Dict[str, str]], lang: str, limit: int = 8) -> List[str]:
    lines: List[str] = []
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


def _fallback_items(lang: str) -> List[Dict[str, str]]:
    return FALLBACK_LINKS_HI if lang == "hi" else FALLBACK_LINKS_EN


async def handle_farmer_schemes(state: BotState) -> dict:
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
            results = _fallback_items(detected_lang)
            result = {"success": False, "data": {"results": results}, "error": result.get("error")}
        else:
            results = (result.get("data") or {}).get("results", [])

        if not results:
            results = _fallback_items(detected_lang)

        date_str = datetime.now().strftime("%d %B %Y")

        if detected_lang == "hi":
            header = f"किसानों के लिए योजनाएं/सब्सिडी ({date_str})"
            scope = f"{state_name} के लिए" if state_name else "केंद्र सरकार के लिए"
            lines = [f"📌 *{header}* — {scope}\n"]
        else:
            header = f"Farmer schemes/subsidies ({date_str})"
            scope = f"for {state_name}" if state_name else "for central government"
            lines = [f"📌 *{header}* — {scope}\n"]

        limit = 12 if is_followup else 8
        lines.extend(_format_items(results, detected_lang, limit=limit))
        if detected_lang == "hi":
            lines.append("क्या आप किसी खास योजना, पात्रता या आवेदन लिंक की जानकारी चाहते हैं?")
        else:
            lines.append("Want details, eligibility, or official apply links for a specific scheme?")

        response_text = "\n".join([line for line in lines if line is not None])
        return {
            "tool_result": result,
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Farmer schemes handler error: {e}")
        return {
            "response_text": "Could not fetch farmer schemes right now.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
