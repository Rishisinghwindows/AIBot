"""
Metro Ticket Helper Node

Demo/placeholder for metro ticket booking assistance.
"""

import re
from common.graph.state import BotState
from common.tools.metro_api import get_metro_info, get_metro_stations


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

    Args:
        state: Current bot state with metro info in entities

    Returns:
        Updated state with metro info or booking steps
    """
    entities = state.get("extracted_entities", {})
    query = state.get("current_query", "")

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

                response_lines = [
                    f"*Metro Route*\n",
                    f"From: *{data.get('source', source)}*",
                    f"To: *{data.get('destination', destination)}*\n",
                    f"Line: {data.get('line', 'N/A')}",
                    f"Stations: {data.get('station_count', 'N/A')} stops",
                    f"Travel Time: ~{data.get('travel_time', 'N/A')} min",
                    f"Fare: Rs. {data.get('fare', 'N/A')}",
                ]

                if data.get("interchange_required"):
                    response_lines.append("\n*Note:* Line change required")

                response_lines.extend([
                    "\n*To book tickets:*",
                    "1. Use DMRC official app",
                    "2. Buy at metro station",
                    "3. Use QR code/UPI payment",
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
                return {
                    "response_text": (
                        f"Could not find route.\n\n"
                        f"Error: {result.get('error', 'Station not found')}\n\n"
                        "Try with exact station names like:\n"
                        "• Rajiv Chowk\n"
                        "• Dwarka Sector 21\n"
                        "• Kashmere Gate"
                    ),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": "metro_ticket",
                }

        # No specific stations - provide general help
        return {
            "response_text": (
                "*Metro Ticket Helper*\n\n"
                "I can help you with metro routes and fares!\n\n"
                "*Try asking:*\n"
                "• Metro from Rajiv Chowk to Huda City Centre\n"
                "• Metro fare from Dwarka to Kashmere Gate\n"
                "• How to reach Nehru Place by metro\n\n"
                "*Supported metros:*\n"
                "Delhi Metro (DMRC) - All lines\n\n"
                "_Note: This uses demo data. For real-time info, "
                "please use the official DMRC app._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "metro_ticket",
        }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "Metro information service is currently unavailable. Please try again later.",
            "response_type": "text",
            "should_fallback": True,
            "intent": "metro_ticket",
        }
