from __future__ import annotations

import httpx

from app.config import Settings
from app.logger import logger
from app.utils.errors import ExternalServiceUnavailable
from app.utils.models import WeatherResponse


class WeatherService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def get_weather(self, city: str) -> WeatherResponse:
        params = {
            "q": city,
            "appid": self.settings.openweather_api_key,
            "units": "metric",
        }
        logger.info("weather_request", city=city)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.settings.openweather_base_url, params=params)
                resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.error("weather_error", error=str(exc))
            raise ExternalServiceUnavailable("Weather API request failed") from exc

        data = resp.json()
        main = data.get("main", {})
        weather_desc = data.get("weather", [{}])[0].get("description", "unknown")

        payload = WeatherResponse(
            city=city,
            temperature_c=main.get("temp", 0.0),
            humidity=main.get("humidity", 0.0),
            condition=weather_desc,
            raw=data,
        )
        logger.info("weather_response", city=city, temp=payload.temperature_c)
        return payload
