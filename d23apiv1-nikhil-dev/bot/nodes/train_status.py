"""
Train Running Status Node

Checks live train running status using Railway API.
"""

import logging
from datetime import datetime
from bot.state import BotState
from bot.tools.railway_api import get_train_status
from bot.utils.response_formatter import sanitize_error, create_service_error_response
from bot.utils.entity_extraction import extract_train_number

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "train_status"


def handle_train_status(state: BotState) -> dict:
    """
    Node function: Check live train running status.

    Args:
        state: Current bot state with train number in entities

    Returns:
        Updated state with train status or error
    """
    entities = state.get("extracted_entities", {})
    train_number = entities.get("train_number", "")
    date = entities.get("date", "")

    # Try to extract train number from query if not in entities
    if not train_number:
        train_number = extract_train_number(state.get("current_query", "")) or ""

    # Validate train number
    if not train_number:
        return {
            "response_text": (
                "*Train Status*\n\n"
                "Please provide a train number.\n\n"
                "*Example:* Train 12301 status\n\n"
                "*Popular trains:*\n"
                "- 12301/12302 - Rajdhani Express\n"
                "- 12951/12952 - Mumbai Rajdhani\n"
                "- 22691/22692 - Rajdhani Express"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    # Use today's date if not provided
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        result = get_train_status(train_number, date)

        if result["success"]:
            data = result["data"]

            # Determine status emoji
            delay = data.get("delay_minutes", 0)
            if delay == 0:
                status_emoji = "✅"
                delay_text = "On Time"
            elif delay > 0:
                status_emoji = "⚠️"
                delay_text = f"Late by {delay} min"
            else:
                status_emoji = "🟢"
                delay_text = f"Early by {abs(delay)} min"

            # Format train status for WhatsApp
            response_lines = [
                f"*Train: {data.get('train_name', 'N/A')}* ({train_number})\n",
                f"{status_emoji} Status: {data.get('running_status', 'N/A')}",
                f"Delay: {delay_text}",
            ]

            last_station = data.get("last_station")
            if last_station:
                last_time = data.get("last_station_time", "")
                response_lines.append(f"\nLast Station: *{last_station}*")
                if last_time:
                    response_lines.append(f"Time: {last_time}")

            next_station = data.get("next_station")
            if next_station:
                eta = data.get("eta_next_station", "")
                response_lines.append(f"\nNext Station: *{next_station}*")
                if eta:
                    response_lines.append(f"ETA: {eta}")

            return {
                "tool_result": result,
                "response_text": "\n".join(response_lines),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "train status")
            return {
                "tool_result": result,
                "response_text": (
                    f"*Train Status: {train_number}*\n\n"
                    f"{user_message}\n\n"
                    "*Possible reasons:*\n"
                    "- Train not running today\n"
                    "- Invalid train number\n"
                    "- Railway server temporarily down\n\n"
                    "_Please verify and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Train status handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="Train Status",
            raw_error=str(e)
        )
