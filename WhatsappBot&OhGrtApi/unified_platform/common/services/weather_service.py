"""
Weather Service.

Provides weather information using OpenWeatherMap API.
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from common.models.base import WeatherData

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openweathermap.org/data/2.5/weather",
    ):
        """
        Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key
            base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_weather(self, city: str) -> WeatherData:
        """
        Get current weather for a city.

        Args:
            city: City name

        Returns:
            WeatherData object

        Raises:
            Exception: If API request fails
        """
        if not self.api_key:
            raise ValueError("OpenWeather API key not configured")

        client = await self._get_client()

        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
        }

        try:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            return WeatherData(
                city=data["name"],
                country=data.get("sys", {}).get("country", ""),
                temperature=data["main"]["temp"],
                feels_like=data["main"].get("feels_like", data["main"]["temp"]),
                humidity=data["main"].get("humidity", 0),
                description=data["weather"][0].get("description", ""),
                icon=data["weather"][0].get("icon", ""),
                wind_speed=data.get("wind", {}).get("speed", 0.0),
                timestamp=datetime.now(),
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"City '{city}' not found")
            logger.error(f"Weather API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Weather service error: {e}")
            raise

    async def get_forecast(
        self,
        city: str,
        days: int = 5,
    ) -> list[WeatherData]:
        """
        Get weather forecast for a city.

        Args:
            city: City name
            days: Number of days (max 5 for free tier)

        Returns:
            List of WeatherData objects
        """
        if not self.api_key:
            raise ValueError("OpenWeather API key not configured")

        client = await self._get_client()
        forecast_url = self.base_url.replace("/weather", "/forecast")

        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "cnt": days * 8,  # 3-hour intervals
        }

        try:
            response = await client.get(forecast_url, params=params)
            response.raise_for_status()
            data = response.json()

            forecasts = []
            city_info = data.get("city", {})

            for item in data.get("list", []):
                forecasts.append(
                    WeatherData(
                        city=city_info.get("name", city),
                        country=city_info.get("country", ""),
                        temperature=item["main"]["temp"],
                        feels_like=item["main"].get("feels_like", item["main"]["temp"]),
                        humidity=item["main"].get("humidity", 0),
                        description=item["weather"][0].get("description", ""),
                        icon=item["weather"][0].get("icon", ""),
                        wind_speed=item.get("wind", {}).get("speed", 0.0),
                        timestamp=datetime.fromisoformat(item["dt_txt"]),
                    )
                )

            return forecasts
        except Exception as e:
            logger.error(f"Forecast service error: {e}")
            raise

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Module-level service instance
_weather_service: Optional[WeatherService] = None


def get_weather_service(api_key: Optional[str] = None) -> WeatherService:
    """
    Get or create weather service instance.

    Args:
        api_key: OpenWeather API key

    Returns:
        WeatherService instance
    """
    global _weather_service
    if _weather_service is None and api_key:
        _weather_service = WeatherService(api_key=api_key)
    elif _weather_service is None:
        raise ValueError("Weather service not initialized. Provide api_key.")
    return _weather_service
