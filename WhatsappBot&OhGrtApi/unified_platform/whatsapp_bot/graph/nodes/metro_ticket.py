"""
Metro Ticket Helper Node

Demo/placeholder for metro ticket booking assistance.
Supports multilingual responses (11+ Indian languages).
"""

import re
from whatsapp_bot.state import BotState
from common.tools.metro_api import get_metro_info, get_metro_stations
from common.i18n.responses import get_metro_label


def _extract_stations(text: str) -> tuple[str, str]:
    """
    Extract source and destination stations from text.

    Handles patterns like:
    - "metro from X to Y"
    - "X to Y metro"
    - "how to reach Y from X"
    """
    text_lower = text.lower()

    # Pattern: "from X to Y"
    match = re.search(r"from\s+(.+?)\s+to\s+(.+?)(?:\s+metro|\s+by|\s*$)", text_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern: "X to Y"
    match = re.search(r"metro\s+(.+?)\s+to\s+(.+?)(?:\s|$)", text_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern: general "X to Y"
    match = re.search(r"(.+?)\s+to\s+(.+?)(?:\s+metro|\s+fare|\s*$)", text_lower)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    return "", ""


def handle_metro_ticket(state: BotState) -> dict:
    """
    Node function: Handle metro ticket queries.
    Returns response in user's detected language.

    Args:
        state: Current bot state with metro info in entities

    Returns:
        Updated state with metro info or booking steps
    """
    entities = state.get("extracted_entities", {})
    query = state.get("current_query", "")
    detected_lang = state.get("detected_language", "en")

    source = entities.get("source_station", "")
    destination = entities.get("destination_station", "")

    # Try to extract stations from query if not in entities
    if not source or not destination:
        extracted_source, extracted_dest = _extract_stations(query)
        source = source or extracted_source
        destination = destination or extracted_dest

    try:
        # If we have both stations, get route info
        if source and destination:
            result = get_metro_info(source, destination)

            if result["success"]:
                data = result["data"]

                # Get localized labels
                title = get_metro_label("title", detected_lang)
                from_label = get_metro_label("from", detected_lang)
                to_label = get_metro_label("to", detected_lang)
                line_label = get_metro_label("line", detected_lang)
                stations_label = get_metro_label("stations", detected_lang)
                travel_time_label = get_metro_label("travel_time", detected_lang)
                fare_label = get_metro_label("fare", detected_lang)
                interchange = get_metro_label("interchange", detected_lang)
                booking = get_metro_label("booking", detected_lang)

                response_lines = [
                    f"*{title}*\n",
                    f"{from_label}: *{data.get('source', source)}*",
                    f"{to_label}: *{data.get('destination', destination)}*\n",
                    f"{line_label}: {data.get('line', 'N/A')}",
                    f"{stations_label}: {data.get('station_count', 'N/A')}",
                    f"{travel_time_label}: ~{data.get('travel_time', 'N/A')} min",
                    f"{fare_label}: Rs. {data.get('fare', 'N/A')}",
                ]

                if data.get("interchange_required"):
                    response_lines.append(f"\n*{interchange}*")

                response_lines.extend([
                    f"\n*{booking}*",
                    "1. DMRC App",
                    "2. Metro Station",
                    "3. QR/UPI",
                ])

                if data.get("note"):
                    response_lines.append(f"\n_{data.get('note')}_")

                return {
                    "tool_result": result,
                    "response_text": "\n".join(response_lines),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": "metro_ticket",
                }
            else:
                # Station not found
                not_found = get_metro_label("not_found", detected_lang)
                return {
                    "response_text": not_found,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": "metro_ticket",
                }

        # No specific stations - provide general help
        ask_route = get_metro_label("ask_route", detected_lang)
        return {
            "response_text": ask_route,
            "response_type": "text",
            "should_fallback": False,
            "intent": "metro_ticket",
        }

    except Exception as e:
        error_msg = get_metro_label("error", detected_lang)
        return {
            "error": str(e),
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": True,
            "intent": "metro_ticket",
        }
