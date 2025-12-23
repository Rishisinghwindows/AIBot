"""
Weather Node

Fetches and displays weather information for a given city.
Uses the OhGrtApi WeatherService.
"""

import re
from app.graph.state import BotState
from app.services.weather_service import WeatherService
from app.config import get_settings
from app.logger import logger

INTENT = "weather"


def _clean_city_name(city: str) -> str:
    """
    Clean up a city name by removing common filler words and time references.

    Examples:
    - "Mumbai today" -> "Mumbai"
    - "the Delhi" -> "Delhi"
    - "New York tomorrow" -> "New York"
    """
    if not city:
        return ""

    # Remove leading articles
    city = re.sub(r"^(the|a|an)\s+", "", city, flags=re.IGNORECASE)

    # Remove trailing time references and filler words
    city = re.sub(
        r"\s+(today|tomorrow|now|please|current|currently|right now|at the moment|ka mausam|ka weather|mein|में).*$",
        "",
        city,
        flags=re.IGNORECASE
    )

    # Remove any remaining punctuation at the end
    city = re.sub(r"[?.!,]+$", "", city)

    return city.strip().title() if city.strip() else ""


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
        r"mausam\s+(?:in|of|for|at)\s+(.+?)(?:\?|$)",
        r"weather\s+(.+?)(?:\?|$)",
        r"(.+?)\s+weather",
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            city = match.group(1).strip()
            city = _clean_city_name(city)
            if city and len(city) > 1:
                return city

    # Fallback: look for capitalized words that might be city names
    words = query.split()
    for word in words:
        if word and word[0].isupper() and word.lower() not in [
            "weather", "temperature", "what", "tell", "me", "the", "in", "of", "mausam"
        ]:
            return word

    return ""


def _get_weather_emoji(condition: str) -> str:
    """
    Returns an emoji corresponding to the weather condition.
    """
    condition_lower = condition.lower()

    if "clear" in condition_lower or "sunny" in condition_lower:
        return "☀️"
    if "cloud" in condition_lower:
        return "☁️"
    if "rain" in condition_lower or "drizzle" in condition_lower:
        return "🌧️"
    if "thunder" in condition_lower or "storm" in condition_lower:
        return "⛈️"
    if "snow" in condition_lower:
        return "❄️"
    if "fog" in condition_lower or "mist" in condition_lower or "haze" in condition_lower:
        return "🌫️"
    if "smoke" in condition_lower:
        return "💨"

    return "🌤️"


async def handle_weather(state: BotState) -> dict:
    """
    Node function: Get current weather for a city.

    Args:
        state: Current bot state with query containing city name.

    Returns:
        Updated state with weather information or an error message.
    """
    # Try to get city from entities first, then extract from query
    entities = state.get("extracted_entities", {})
    city = entities.get("city", "")

    # Always clean the city name to remove filler words like "today", "tomorrow"
    if city:
        city = _clean_city_name(city)

    if not city:
        # Extract city from the query
        query = state.get("current_query", "")
        city = _extract_city_from_query(query)

    if not city:
        return {
            "response_text": (
                "*Weather*\n\n"
                "Please specify a city to get the weather.\n\n"
                "*Examples:*\n"
                "- Weather in Delhi\n"
                "- Mumbai weather\n"
                "- Temperature in Bangalore"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    try:
        settings = get_settings()
        weather_service = WeatherService(settings)

        result = await weather_service.get_weather(city)

        weather_emoji = _get_weather_emoji(result.condition)

        response_text = (
            f"*Weather in {result.city}*\n\n"
            f"{weather_emoji} Temperature: *{result.temperature_c}°C*\n"
            f"💧 Humidity: *{result.humidity}%*\n"
            f"Condition: {result.condition.title()}"
        )

        return {
            "tool_result": {
                "success": True,
                "data": {
                    "city": result.city,
                    "temperature": result.temperature_c,
                    "humidity": result.humidity,
                    "condition": result.condition,
                },
                "tool_name": "weather",
            },
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Weather handler error: {e}")
        return {
            "response_text": (
                "*Weather*\n\n"
                f"Could not get weather for *{city}*.\n\n"
                "_Please check the city name and try again._\n\n"
                "*Example:* Weather in Mumbai"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
