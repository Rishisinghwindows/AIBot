"""
Travel Node

Handles Indian Railways features:
- PNR Status
- Train Running Status

Uses the OhGrtApi TravelService.
"""

import re
from app.graph.state import BotState
from app.services.travel_service import get_travel_service
from app.config import get_settings
from app.logger import logger

PNR_INTENT = "pnr_status"
TRAIN_INTENT = "train_status"


def extract_pnr(text: str) -> str:
    """Extract 10-digit PNR number from text."""
    match = re.search(r'\b(\d{10})\b', text)
    return match.group(1) if match else ""


def extract_train_number(text: str) -> str:
    """Extract 4-5 digit train number from text."""
    match = re.search(r'\b(\d{4,5})\b', text)
    return match.group(1) if match else ""


async def handle_pnr_status(state: BotState) -> dict:
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
        pnr = extract_pnr(state.get("current_query", ""))

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
            "intent": PNR_INTENT,
        }

    try:
        settings = get_settings()
        travel_service = get_travel_service(settings.railway_api_key)

        logger.info(f"Checking PNR status for: {pnr}")
        result = await travel_service.get_pnr_status(pnr)

        if result.get("success"):
            data = result.get("data", {})

            # Validate that we have meaningful data
            train_name = data.get('train_name', 'N/A')
            train_number = data.get('train_number', 'N/A')

            # Check if data is essentially empty
            if train_name == 'N/A' and train_number == 'N/A':
                logger.warning(f"PNR {pnr} returned empty data")
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
                    "intent": PNR_INTENT,
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
                "intent": PNR_INTENT,
            }
        else:
            error = result.get("error", "Unable to fetch PNR status")
            logger.warning(f"PNR lookup failed for {pnr}: {error}")
            return {
                "tool_result": result,
                "response_text": (
                    f"*PNR Status: {pnr}*\n\n"
                    "Could not fetch PNR status.\n\n"
                    "*Possible reasons:*\n"
                    "- PNR not found or expired\n"
                    "- Railway server temporarily down\n\n"
                    "_Please verify the PNR and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": PNR_INTENT,
            }

    except Exception as e:
        logger.error(f"PNR status handler error: {e}")
        return {
            "response_text": (
                "*PNR Status*\n\n"
                "An error occurred while checking PNR status.\n\n"
                "_Please try again later._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": PNR_INTENT,
            "error": str(e),
        }


async def handle_train_status(state: BotState) -> dict:
    """
    Node function: Check train running status.

    Args:
        state: Current bot state with train number in entities

    Returns:
        Updated state with train status or error
    """
    entities = state.get("extracted_entities", {})
    train_number = entities.get("train_number", "")

    # Try to extract train number from query if not in entities
    if not train_number:
        train_number = extract_train_number(state.get("current_query", ""))

    # Validate train number format
    if not train_number or not (4 <= len(train_number) <= 5) or not train_number.isdigit():
        return {
            "response_text": (
                "*Train Status*\n\n"
                "Please provide a valid train number (4-5 digits).\n\n"
                "*Example:* Train 12301 status\n\n"
                "_You can find your train number on your ticket._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": TRAIN_INTENT,
        }

    try:
        settings = get_settings()
        travel_service = get_travel_service(settings.railway_api_key)

        logger.info(f"Checking train status for: {train_number}")
        result = await travel_service.get_train_status(train_number)

        if result.get("success"):
            data = result.get("data", {})
            train_name = data.get("train_name", "Unknown Train")

            # Format train status
            response_lines = [
                f"*Train Status: {train_number}*\n",
                f"Train: *{train_name}*",
            ]

            # Current status
            current_station = data.get("current_station", {})
            if current_station:
                station_name = current_station.get("name", "Unknown")
                delay = current_station.get("delay", 0)
                eta = current_station.get("eta", "")

                response_lines.append(f"\n*Current Location:*")
                response_lines.append(f"Station: {station_name}")

                if delay > 0:
                    response_lines.append(f"Running Late: *{delay} minutes*")
                elif delay < 0:
                    response_lines.append(f"Running Early: *{abs(delay)} minutes*")
                else:
                    response_lines.append("Running On Time")

                if eta:
                    response_lines.append(f"ETA: {eta}")

            # Recent stops
            recent_stops = data.get("recent_stops", [])
            if recent_stops:
                response_lines.append(f"\n*Recent Stops:*")
                for stop in recent_stops[:3]:
                    stop_name = stop.get("name", "Unknown")
                    arrival = stop.get("actual_arrival", stop.get("scheduled_arrival", ""))
                    response_lines.append(f"• {stop_name}: {arrival}")

            logger.info(f"Successfully retrieved train status for {train_number}")
            return {
                "tool_result": result,
                "response_text": "\n".join(response_lines),
                "response_type": "text",
                "should_fallback": False,
                "intent": TRAIN_INTENT,
            }
        else:
            error = result.get("error", "Unable to fetch train status")
            logger.warning(f"Train status lookup failed for {train_number}: {error}")
            return {
                "tool_result": result,
                "response_text": (
                    f"*Train Status: {train_number}*\n\n"
                    "Could not fetch train status.\n\n"
                    "*Possible reasons:*\n"
                    "- Train number may be incorrect\n"
                    "- Train may not be running today\n"
                    "- Railway server temporarily down\n\n"
                    "_Please verify the train number and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": TRAIN_INTENT,
            }

    except Exception as e:
        logger.error(f"Train status handler error: {e}")
        return {
            "response_text": (
                "*Train Status*\n\n"
                "An error occurred while checking train status.\n\n"
                "_Please try again later._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": TRAIN_INTENT,
            "error": str(e),
        }
