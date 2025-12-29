"""
Weather API Tool

Wrapper for OpenWeather API.
- Current Weather: https://openweathermap.org/current
- Geocoding: https://openweathermap.org/api/geocoding-api
"""

import httpx
import logging
from bot.state import ToolResult
from bot.config import settings

logger = logging.getLogger(__name__)

# OpenWeather API URLs
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
OPENWEATHER_REVERSE_GEO_URL = "http://api.openweathermap.org/geo/1.0/reverse"

# Nominatim for better local names
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


def _get_local_area_name(latitude: float, longitude: float, client: httpx.Client) -> str:
    """
    Get local area/village name using Nominatim reverse geocoding.

    Returns location string like "Dwarka, South West Delhi, Delhi" or
    falls back to empty string if geocoding fails.
    """
    try:
        response = client.get(
            NOMINATIM_REVERSE_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
                "zoom": 14,  # Get local area level detail
            },
            headers={
                "User-Agent": "D23Bot/1.0 (WhatsApp Weather Bot)",
            },
        )
        response.raise_for_status()
        data = response.json()

        address = data.get("address", {})

        # Build location name from most specific to general
        parts = []

        # Try to get most local name first (village/suburb/neighbourhood)
        local_name = (
            address.get("village") or
            address.get("suburb") or
            address.get("neighbourhood") or
            address.get("hamlet") or
            address.get("town") or
            address.get("city_district")
        )
        if local_name:
            parts.append(local_name)

        # Add district/city
        district = (
            address.get("state_district") or
            address.get("district") or
            address.get("county")
        )
        city = address.get("city")

        if district and district not in parts:
            parts.append(district)
        elif city and city not in parts:
            parts.append(city)

        # Add state
        state = address.get("state")
        if state and state not in parts:
            parts.append(state)

        if parts:
            return ", ".join(parts)

        # Fallback to display_name if structured parsing fails
        display_name = data.get("display_name", "")
        if display_name:
            # Take first 3 parts of display name
            name_parts = display_name.split(",")[:3]
            return ", ".join(p.strip() for p in name_parts)

        return ""

    except Exception as e:
        logger.warning(f"Nominatim reverse geocoding failed: {e}")
        return ""


def _get_weather_description(weather_id: int) -> tuple[str, str]:
    """
    Get weather description and emoji based on OpenWeather condition code.

    Returns:
        Tuple of (description, emoji)
    """
    # Thunderstorm
    if 200 <= weather_id < 300:
        return "Thunderstorm", "⛈️"
    # Drizzle
    elif 300 <= weather_id < 400:
        return "Drizzle", "🌧️"
    # Rain
    elif 500 <= weather_id < 600:
        if weather_id == 500:
            return "Light Rain", "🌦️"
        elif weather_id == 501:
            return "Moderate Rain", "🌧️"
        else:
            return "Heavy Rain", "🌧️"
    # Snow
    elif 600 <= weather_id < 700:
        return "Snow", "❄️"
    # Atmosphere (fog, mist, etc.)
    elif 700 <= weather_id < 800:
        return "Foggy", "🌫️"
    # Clear
    elif weather_id == 800:
        return "Clear Sky", "☀️"
    # Clouds
    elif 801 <= weather_id < 810:
        if weather_id == 801:
            return "Few Clouds", "🌤️"
        elif weather_id == 802:
            return "Scattered Clouds", "⛅"
        else:
            return "Cloudy", "☁️"
    else:
        return "Unknown", ""


def get_weather_by_coordinates(latitude: float, longitude: float) -> ToolResult:
    """
    Get the current weather using coordinates with OpenWeather API.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        ToolResult with weather data or error.
    """
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return ToolResult(
            success=False,
            data=None,
            error="OpenWeather API key not configured.",
            tool_name="weather",
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            # Get weather data
            response = client.get(
                OPENWEATHER_URL,
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": api_key,
                    "units": "metric",  # Celsius
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract weather info
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})

            weather_id = weather.get("id", 0)
            description, emoji = _get_weather_description(weather_id)

            # Get local area name using Nominatim for better village/area names
            location_name = _get_local_area_name(latitude, longitude, client)

            # Fallback to OpenWeather name if Nominatim fails
            if not location_name:
                location_name = data.get("name", "Unknown")
                country = data.get("sys", {}).get("country", "")
                if country:
                    location_name = f"{location_name}, {country}"

            return ToolResult(
                success=True,
                data={
                    "location": location_name,
                    "temperature": f"{main.get('temp', 'N/A')}°C",
                    "feels_like": f"{main.get('feels_like', 'N/A')}°C",
                    "humidity": f"{main.get('humidity', 'N/A')}%",
                    "description": weather.get("description", description).title(),
                    "emoji": emoji,
                    "wind_speed": f"{wind.get('speed', 'N/A')} m/s",
                    "pressure": f"{main.get('pressure', 'N/A')} hPa",
                    "visibility": f"{data.get('visibility', 0) / 1000:.1f} km",
                    "weather_id": weather_id,
                    "latitude": latitude,
                    "longitude": longitude,
                },
                error=None,
                tool_name="weather",
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenWeather API error: {e.response.status_code}")
        if e.response.status_code == 401:
            return ToolResult(
                success=False,
                data=None,
                error="Invalid API key. Please check your OpenWeather API key.",
                tool_name="weather",
            )
        return ToolResult(
            success=False,
            data=None,
            error=f"API request failed with status {e.response.status_code}",
            tool_name="weather",
        )
    except httpx.TimeoutException:
        return ToolResult(
            success=False,
            data=None,
            error="Request timed out. Please try again.",
            tool_name="weather",
        )
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="weather",
        )


def get_weather(city: str) -> ToolResult:
    """
    Get the current weather for a city using OpenWeather API.

    Args:
        city: The name of the city.

    Returns:
        ToolResult with weather data or error.
    """
    if not city:
        return ToolResult(
            success=False,
            data=None,
            error="City name is required.",
            tool_name="weather",
        )

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return ToolResult(
            success=False,
            data=None,
            error="OpenWeather API key not configured.",
            tool_name="weather",
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            # Get weather by city name directly
            response = client.get(
                OPENWEATHER_URL,
                params={
                    "q": city,
                    "appid": api_key,
                    "units": "metric",  # Celsius
                },
            )

            if response.status_code == 404:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Could not find city '{city}'. Please check the spelling.",
                    tool_name="weather",
                )

            response.raise_for_status()
            data = response.json()

            # Extract weather info
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})

            weather_id = weather.get("id", 0)
            description, emoji = _get_weather_description(weather_id)

            # Get location name
            location_name = data.get("name", city)
            country = data.get("sys", {}).get("country", "")
            if country:
                location_name = f"{location_name}, {country}"

            return ToolResult(
                success=True,
                data={
                    "location": location_name,
                    "temperature": f"{main.get('temp', 'N/A')}°C",
                    "feels_like": f"{main.get('feels_like', 'N/A')}°C",
                    "humidity": f"{main.get('humidity', 'N/A')}%",
                    "description": weather.get("description", description).title(),
                    "emoji": emoji,
                    "wind_speed": f"{wind.get('speed', 'N/A')} m/s",
                    "pressure": f"{main.get('pressure', 'N/A')} hPa",
                    "visibility": f"{data.get('visibility', 0) / 1000:.1f} km",
                    "weather_id": weather_id,
                },
                error=None,
                tool_name="weather",
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"OpenWeather API error: {e.response.status_code}")
        if e.response.status_code == 401:
            return ToolResult(
                success=False,
                data=None,
                error="Invalid API key. Please check your OpenWeather API key.",
                tool_name="weather",
            )
        return ToolResult(
            success=False,
            data=None,
            error=f"API request failed with status {e.response.status_code}",
            tool_name="weather",
        )
    except httpx.TimeoutException:
        return ToolResult(
            success=False,
            data=None,
            error="Request timed out. Please try again.",
            tool_name="weather",
        )
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="weather",
        )
