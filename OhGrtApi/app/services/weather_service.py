from __future__ import annotations

from typing import Optional
import httpx

from app.config import Settings
from app.exceptions import ExternalServiceError, ServiceUnavailableError, ValidationError
from app.logger import logger
from app.utils.circuit_breaker import CircuitBreakerError, weather_circuit
from app.utils.models import WeatherResponse


class WeatherService:
    """Service for fetching weather data from OpenWeather API with circuit breaker."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self._client

    async def get_weather(self, city: str) -> WeatherResponse:
        """
        Get current weather for a city with circuit breaker protection.

        Args:
            city: City name to get weather for

        Returns:
            WeatherResponse with current weather data

        Raises:
            ValidationError: If city is empty
            ExternalServiceError: If weather API request fails
            ServiceUnavailableError: If circuit breaker is open
        """
        if not city or not city.strip():
            raise ValidationError("City name cannot be empty", field="city")

        city = city.strip()

        if not self.settings.openweather_api_key:
            raise ExternalServiceError(
                service_name="OpenWeather",
                message="API key not configured",
            )

        try:
            # Use circuit breaker to protect against cascading failures
            async with weather_circuit:
                return await self._fetch_weather(city)
        except CircuitBreakerError as exc:
            logger.warning(
                "weather_circuit_open",
                city=city,
                retry_after=exc.retry_after,
            )
            raise ServiceUnavailableError(
                service_name="OpenWeather",
                message="Weather service temporarily unavailable",
                retry_after=int(exc.retry_after),
            ) from exc

    async def _fetch_weather(self, city: str) -> WeatherResponse:
        """Internal method to fetch weather data."""
        params = {
            "q": city,
            "appid": self.settings.openweather_api_key,
            "units": "metric",
        }

        logger.info("weather_request", city=city)

        try:
            client = await self._get_client()
            resp = await client.get(self.settings.openweather_base_url, params=params)

            if resp.status_code == 404:
                # City not found is a validation error, not a service error
                # Don't trigger circuit breaker for this
                raise ValidationError(f"City '{city}' not found", field="city")

            resp.raise_for_status()

        except ValidationError:
            raise
        except httpx.TimeoutException as exc:
            logger.error("weather_timeout", city=city, error=str(exc))
            raise ExternalServiceError(
                service_name="OpenWeather",
                message="Request timed out",
                original_error=str(exc),
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error("weather_http_error", city=city, status=exc.response.status_code)
            raise ExternalServiceError(
                service_name="OpenWeather",
                message=f"HTTP error: {exc.response.status_code}",
                original_error=str(exc),
            ) from exc
        except Exception as exc:
            logger.error("weather_error", city=city, error=str(exc))
            raise ExternalServiceError(
                service_name="OpenWeather",
                message="Request failed",
                original_error=str(exc),
            ) from exc

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

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
