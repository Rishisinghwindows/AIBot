"""
PNR Status Node.

Handles Indian Railway PNR status queries.
Supports multilingual responses (11+ Indian languages).
"""

import logging
import re
from typing import Dict, Optional

import httpx

from common.graph.state import BotState
from common.i18n.responses import get_train_label, get_phrase

logger = logging.getLogger(__name__)

INTENT = "pnr_status"


def extract_pnr(text: str) -> Optional[str]:
    """
    Extract PNR number from text.

    Args:
        text: User message

    Returns:
        10-digit PNR or None
    """
    # Look for 10-digit number
    match = re.search(r'\b(\d{10})\b', text)
    if match:
        return match.group(1)
    return None


async def get_pnr_status(pnr: str, api_key: str) -> Dict:
    """
    Fetch PNR status from Indian Railways API.

    Args:
        pnr: 10-digit PNR number
        api_key: RapidAPI key

    Returns:
        PNR status data
    """
    url = "https://irctc1.p.rapidapi.com/api/v3/getPNRStatus"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "irctc1.p.rapidapi.com",
    }

    params = {"pnrNumber": pnr}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


def format_pnr_response(data: Dict, lang: str = "en") -> str:
    """
    Format PNR status data as a readable message (localized).

    Args:
        data: PNR API response
        lang: Language code

    Returns:
        Formatted message
    """
    if not data or not data.get("status"):
        return get_train_label("not_found", lang)

    pnr_data = data.get("data", {})

    # Get localized labels
    title = get_train_label("title", lang)
    train_label = get_train_label("train_name", lang)
    from_to_label = get_train_label("from_to", lang)
    date_label = get_train_label("date", lang)
    class_label = get_train_label("class", lang)
    passenger_label = get_train_label("passenger", lang)

    train_info = f"{train_label}: {pnr_data.get('trainName', 'N/A')} ({pnr_data.get('trainNumber', '')})"
    journey_info = f"{from_to_label}: {pnr_data.get('sourceStation', 'N/A')} → {pnr_data.get('destinationStation', 'N/A')}"
    date_info = f"{date_label}: {pnr_data.get('dateOfJourney', 'N/A')}"
    class_info = f"{class_label}: {pnr_data.get('journeyClass', 'N/A')}"

    passengers = pnr_data.get("passengerList", [])
    passenger_info = []
    for i, p in enumerate(passengers, 1):
        status = p.get("currentStatus", "N/A")
        booking = p.get("bookingStatus", "N/A")
        passenger_info.append(f"  {passenger_label} {i}: {booking} → {status}")

    lines = [
        f"*🎫 {title}*",
        "",
        train_info,
        journey_info,
        date_info,
        class_info,
        "",
        f"*{passenger_label}:*",
        *passenger_info,
    ]

    return "\n".join(lines)


async def handle_pnr_status(state: BotState) -> Dict:
    """
    Handle PNR status queries.
    Returns response in user's detected language.

    Args:
        state: Current bot state

    Returns:
        State update with PNR status
    """
    query = state.get("current_query", "")
    entities = state.get("extracted_entities", {})
    detected_lang = state.get("detected_language", "en")

    # Try to get PNR from entities or extract from query
    pnr = entities.get("pnr") or extract_pnr(query)

    if not pnr:
        prompt = get_train_label("pnr_prompt", detected_lang)
        return {
            "response_text": prompt,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "route_log": state.get("route_log", []) + ["pnr_status:missing_pnr"],
        }

    try:
        # Get API key from config
        from whatsapp_bot.config import settings
        api_key = settings.railway_api_key

        if not api_key:
            return {
                "response_text": "PNR service is not configured.",
                "response_type": "text",
                "should_fallback": True,
                "intent": INTENT,
            }

        # Fetch PNR status
        data = await get_pnr_status(pnr, api_key)

        # Format response
        response = format_pnr_response(data, detected_lang)

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "tool_result": data,
            "route_log": state.get("route_log", []) + ["pnr_status:success"],
        }

    except Exception as e:
        logger.error(f"PNR status error: {e}")
        error_msg = get_phrase("error_occurred", detected_lang)
        return {
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": True,
            "intent": INTENT,
            "error": str(e),
            "route_log": state.get("route_log", []) + ["pnr_status:error"],
        }
