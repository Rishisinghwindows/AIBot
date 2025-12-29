"""
PNR Status Node

Checks Indian Railways PNR status using Railway API.
"""

import logging
from bot.state import BotState
from bot.tools.railway_api import get_pnr_status
from bot.utils.response_formatter import sanitize_error, create_service_error_response
from bot.utils.entity_extraction import extract_pnr

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "pnr_status"


def handle_pnr_status(state: BotState) -> dict:
    """
    Node function: Check PNR status.

    Args:
        state: Current bot state with PNR number in entities

    Returns:
        Updated state with PNR status or error
    """
    entities = state.get("extracted_entities", {})
    pnr = entities.get("pnr", "")

    # Try to extract PNR from query if not in entities
    if not pnr:
        pnr = extract_pnr(state.get("current_query", "")) or ""

    # Validate PNR format
    if not pnr or len(pnr) != 10 or not pnr.isdigit():
        return {
            "response_text": (
                "*PNR Status*\n\n"
                "Please provide a valid 10-digit PNR number.\n\n"
                "*Example:* PNR 1234567890\n\n"
                "_You can find your PNR on your ticket or booking confirmation._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    try:
        logger.info(f"Checking PNR status for: {pnr}")
        result = get_pnr_status(pnr)
        logger.debug(f"PNR API result: {result}")

        if result["success"]:
            data = result["data"]

            # Validate that we have meaningful data
            train_name = data.get('train_name', 'N/A')
            train_number = data.get('train_number', 'N/A')

            # Check if data is essentially empty (all N/A)
            if train_name == 'N/A' and train_number == 'N/A':
                logger.warning(f"PNR {pnr} returned empty data: {data}")
                return {
                    "tool_result": result,
                    "response_text": (
                        f"*PNR Status: {pnr}*\n\n"
                        "Could not retrieve PNR details.\n\n"
                        "*Possible reasons:*\n"
                        "- PNR number may be incorrect\n"
                        "- PNR may have expired (60 days old)\n"
                        "- Railway server is not responding\n\n"
                        "_Please verify your PNR and try again._"
                    ),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }

            # Format PNR status for WhatsApp
            response_lines = [
                f"*PNR Status: {pnr}*\n",
                f"Train: *{train_name}* ({train_number})",
                f"From: {data.get('from_station', 'N/A')}",
                f"To: {data.get('to_station', 'N/A')}",
                f"Date: {data.get('journey_date', 'N/A')}",
                f"Class: {data.get('class', 'N/A')}",
            ]

            # Chart status
            chart_status = "Yes" if data.get("chart_prepared") else "No"
            response_lines.append(f"Chart Prepared: {chart_status}")

            # Passenger status
            passengers = data.get("passengers", [])
            if passengers:
                response_lines.append("\n*Passenger Status:*")
                for i, p in enumerate(passengers, 1):
                    booking = p.get("booking_status", "N/A")
                    current = p.get("current_status", "N/A")
                    coach = p.get("coach", "")
                    berth = p.get("berth", "")

                    status_line = f"{i}. Booking: {booking}"
                    if current and current != booking:
                        status_line += f" → Current: {current}"
                    if coach and berth:
                        status_line += f" ({coach}/{berth})"

                    response_lines.append(status_line)
            else:
                response_lines.append("\n_No passenger details available_")

            logger.info(f"Successfully retrieved PNR status for {pnr}")
            return {
                "tool_result": result,
                "response_text": "\n".join(response_lines),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "Unable to fetch PNR status")
            logger.warning(f"PNR lookup failed for {pnr}: {raw_error}")
            user_message = sanitize_error(raw_error, "PNR status")
            return {
                "tool_result": result,
                "response_text": (
                    f"*PNR Status: {pnr}*\n\n"
                    f"{user_message}\n\n"
                    "*Possible reasons:*\n"
                    "- PNR not found or expired\n"
                    "- Railway server temporarily down\n\n"
                    "_Please verify the PNR and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"PNR status handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="PNR Status",
            raw_error=str(e)
        )
