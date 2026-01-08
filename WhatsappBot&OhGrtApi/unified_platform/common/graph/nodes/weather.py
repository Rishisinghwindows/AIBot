"""
Weather Node

Fetches and displays weather information for a given city or location.
Supports location-based weather when user shares their GPS location.
"""

import logging
import re
from common.graph.state import BotState
from common.tools.weather_api import get_weather, get_weather_by_coordinates
from common.utils.response_formatter import sanitize_error, create_service_error_response
from whatsapp_bot.stores.pending_location_store import get_pending_location_store
from common.whatsapp.client import get_whatsapp_client

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "weather"

# Response type for location request
RESPONSE_TYPE_LOCATION_REQUEST = "location_request"


def _extract_city_from_query(query: str) -> str:
    """
    Extract city name from weather query.

    Examples:
    - "weather in Delhi" -> "Delhi"
    - "tell me weather of Mumbai" -> "Mumbai"
    - "what's the temperature in New York" -> "New York"
    """
    query_lower = query.lower()

    # Common patterns for city extraction
    patterns = [
        r"weather\s+(?:in|of|for|at)\s+(.+?)(?:\?|$)",
        r"(?:in|of|for|at)\s+(.+?)\s+weather",
        r"temperature\s+(?:in|of|for|at)\s+(.+?)(?:\?|$)",
        r"(?:in|of|for|at)\s+(.+?)\s+temperature",
        r"weather\s+(.+?)(?:\?|$)",
        r"(.+?)\s+weather",
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            city = match.group(1).strip()
            # Clean up common filler words
            city = re.sub(r"^(the|a|an)\s+", "", city)
            city = re.sub(r"\s+(today|tomorrow|now|please).*$", "", city)
            city = re.sub(r"\b(ka|ki|ke|का|की|के)\b$", "", city).strip()
            # Remove "near me", "here" etc as they're not city names
            if city.lower() in ["me", "here", "my location", "today", "tomorrow", "now",
                                "near me", "nearby", "around me", "for my location", "at my location"]:
                return ""
            if city and len(city) > 1:
                return city.title()

    # Fallback: look for capitalized words that might be city names
    words = query.split()
    for word in words:
        if len(word) > 1 and word[0].isupper() and word.lower() not in [
            "weather", "temperature", "what", "tell", "me", "the", "in", "of",
            "today", "tomorrow", "how", "is", "whats", "what's", "near", "here",
            "nearby", "around", "my", "location", "for", "at"
        ]:
            return word

    return ""


def _normalize_city_name(city: str) -> str:
    """Normalize city names and strip trailing Hindi postpositions."""
    if not city:
        return ""
    city_clean = city.strip()
    city_clean = re.sub(r"\b(ka|ki|ke|का|की|के)\b$", "", city_clean).strip()
    if not city_clean:
        return ""
    return " ".join(word.capitalize() for word in city_clean.split())


def _is_location_request_query(query: str) -> bool:
    """Check if user is asking for weather without specifying a city."""
    query_lower = query.lower().strip()

    # Simple weather queries without city (should request location)
    simple_patterns = [
        r"^weather\s*$",
        r"^weather\s+today\s*$",
        r"^weather\s+now\s*$",
        r"^weather\s+(near\s+me|here|for\s+my\s+location|at\s+my\s+location)\s*\??$",  # Location-based
        r"^weather\s+(nearby|around\s+me)\s*\??$",  # Location-based
        r"^what('?s| is)\s+(the\s+)?weather\s*(today|now|near\s+me|here)?\s*\??$",
        r"^how('?s| is)\s+(the\s+)?weather\s*(today|now|near\s+me|here)?\s*\??$",
        r"^today('?s)?\s+weather\s*$",
        r"^current\s+weather\s*$",
        r"^temperature\s*(today|now|near\s+me|here)?\s*$",
        r"^what('?s| is)\s+(the\s+)?temperature\s*(today|now|near\s+me|here)?\s*\??$",
        r"^aaj\s+ka\s+mausam\s*$",  # Hindi: today's weather
        r"^mausam\s*$",  # Hindi: weather
        r"^mausam\s+kaisa\s+hai\s*\??$",  # Hindi: how's the weather
        r"^mere\s+paas\s+(ka\s+)?mausam\s*$",  # Hindi: weather near me
        r"^yahan\s+ka\s+mausam\s*$",  # Hindi: weather here
    ]

    for pattern in simple_patterns:
        if re.match(pattern, query_lower):
            return True

    return False


def _format_weather_response(data: dict) -> str:
    """Format weather data into a nice WhatsApp message."""
    emoji = data.get("emoji", "")
    description = data.get("description", "")

    response_lines = [
        f"*Weather in {data['location']}*\n",
        f"{emoji} *{description}*\n",
        f"🌡️ Temperature: *{data['temperature']}*",
        f"🤔 Feels like: *{data['feels_like']}*",
        f"💧 Humidity: *{data['humidity']}*",
        f"💨 Wind: *{data['wind_speed']}*",
    ]

    # Add visibility if available
    visibility = data.get("visibility", "")
    if visibility and visibility != "0.0 km":
        response_lines.append(f"👁️ Visibility: *{visibility}*")

    return "\n".join(response_lines)


async def handle_weather(state: BotState) -> dict:
    """
    Node function: Get current weather for a city or location.

    Supports two flows:
    1. Direct weather with city (e.g., "weather in Delhi")
    2. Weather without city - asks for location, then shows weather

    Args:
        state: Current bot state with query containing city name.

    Returns:
        Updated state with weather information or location request.
    """
    entities = state.get("extracted_entities", {})
    whatsapp_message = state.get("whatsapp_message", {})
    phone = whatsapp_message.get("from_number", "")
    location_data = whatsapp_message.get("location")
    message_type = whatsapp_message.get("message_type", "text")

    # Check if this is a web request (no valid phone number)
    metadata = state.get("metadata", {})
    is_web_request = metadata.get("platform") == "web" or not phone or len(phone) < 10

    logger.info(f"handle_weather called: phone={phone}, message_type={message_type}, location_data={location_data}, is_web={is_web_request}")

    # For WhatsApp, use pending location store
    pending_store = None
    if not is_web_request:
        try:
            pending_store = get_pending_location_store()
        except Exception as e:
            logger.warning(f"Failed to get pending location store: {e}")

    # Check if user sent a location (responding to our location request for weather)
    if location_data and message_type == "location":
        lat = location_data.get("latitude")
        lon = location_data.get("longitude")

        if lat and lon:
            logger.info(f"Processing weather with location: {lat},{lon}")
            return _execute_weather_with_coordinates(lat, lon)

    # Try to get city from entities first, then extract from query
    city = _normalize_city_name(entities.get("city", ""))
    query = state.get("current_query", "")

    # FIRST check if this is a simple weather query without city - ask for location
    # This must come BEFORE trying to extract city to avoid false extractions
    if not city and _is_location_request_query(query):
        # Save pending weather request (WhatsApp only)
        if pending_store and phone:
            try:
                await pending_store.save_pending_search(
                    phone=phone,
                    search_query="__weather__",  # Special marker for weather
                    original_message=query,
                )
            except Exception as e:
                logger.warning(f"Failed to save pending search: {e}")

        # Request location from user
        return {
            "response_text": (
                "To show you the current weather, please share your location.\n\n"
                "Or specify a city like \"Weather in Delhi\""
            ),
            "response_type": RESPONSE_TYPE_LOCATION_REQUEST,
            "should_fallback": False,
            "intent": INTENT,
        }

    # If city not in entities, try to extract from query
    if not city:
        city = _normalize_city_name(_extract_city_from_query(query))

    if not city:
        # No city found - save pending and show location request
        if pending_store and phone:
            try:
                await pending_store.save_pending_search(
                    phone=phone,
                    search_query="__weather__",
                    original_message=query,
                )
            except Exception as e:
                logger.warning(f"Failed to save pending search: {e}")

        return {
            "response_text": (
                "🌤️ To show you the weather, please share your location.\n\n"
                "Or specify a city like \"Weather in Delhi\""
            ),
            "response_type": RESPONSE_TYPE_LOCATION_REQUEST,
            "should_fallback": False,
            "intent": INTENT,
        }

    try:
        result = get_weather(city)

        if result["success"]:
            data = result["data"]
            response_text = _format_weather_response(data)
            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "weather")
            return {
                "tool_result": result,
                "response_text": (
                    "*Weather*\n\n"
                    f"Could not get weather for *{city}*.\n\n"
                    f"{user_message}\n\n"
                    "_Check the city name spelling and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Weather handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="Weather",
            raw_error=str(e)
        )


def _execute_weather_with_coordinates(latitude: float, longitude: float) -> dict:
    """
    Execute weather lookup using coordinates.

    Args:
        latitude: User's latitude
        longitude: User's longitude

    Returns:
        Response dict with weather data
    """
    try:
        result = get_weather_by_coordinates(latitude, longitude)

        if result["success"]:
            data = result["data"]
            response_text = _format_weather_response(data)
            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "weather")
            return {
                "tool_result": result,
                "response_text": (
                    "*Weather*\n\n"
                    f"Could not get weather for your location.\n\n"
                    f"{user_message}\n\n"
                    "_Please try again or specify a city name._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Weather with coordinates error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="Weather",
            raw_error=str(e)
        )
