from __future__ import annotations

from app.logger import logger
from app.services.weather_service import WeatherService


class WeatherAgent:
    def __init__(self, service: WeatherService):
        self.service = service

    async def run(self, message: str) -> str:
        # Expect city name within message; naive extraction.
        city = message.replace("weather", "").strip() or "London"
        weather = await self.service.get_weather(city)
        logger.info(f"weather_agent_response: city={city}")
        return (
            f"Weather for {weather.city}: {weather.temperature_c}°C, "
            f"humidity {weather.humidity}%, condition {weather.condition}."
        )
