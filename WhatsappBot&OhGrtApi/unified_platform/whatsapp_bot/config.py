"""
WhatsApp Bot Configuration.

Extends the base configuration with bot-specific settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field

from common.config.base import BaseSettings


class BotSettings(BaseSettings):
    """
    WhatsApp Bot specific settings.

    Extends BaseSettings with bot-specific configuration.
    """

    # Bot Identity
    bot_name: str = Field(default="D23Bot", description="Bot display name")
    bot_version: str = Field(default="2.0.0", description="Bot version")

    # WhatsApp specific (inherited from base)
    # These are already in BaseSettings but we can add validation

    # India-specific APIs
    railway_api_key: str = Field(default="", description="RapidAPI key for railway")
    metro_api_key: str = Field(default="", description="Metro booking API key")

    # Astrology features
    astrology_api_key: str = Field(default="", description="Astrology API key")
    enable_horoscope: bool = Field(default=True, description="Enable horoscope feature")
    enable_kundli: bool = Field(default=True, description="Enable Kundli matching")
    enable_transit_alerts: bool = Field(default=True, description="Enable transit alerts")

    # Subscription settings
    horoscope_send_time: str = Field(
        default="06:00",
        description="Time to send daily horoscope (HH:MM)"
    )
    max_subscriptions_per_user: int = Field(
        default=5,
        description="Maximum subscriptions per user"
    )

    # Rate limiting for WhatsApp
    whatsapp_rate_limit_per_minute: int = Field(
        default=30,
        description="Max messages per minute per user"
    )

    # TTS/STT settings
    enable_voice_messages: bool = Field(
        default=True,
        description="Enable voice message handling"
    )
    tts_provider: str = Field(
        default="google",
        description="TTS provider (google, azure)"
    )

    # Features toggles
    enable_image_generation: bool = Field(default=True)
    enable_word_games: bool = Field(default=True)
    enable_reminders: bool = Field(default=True)
    enable_fact_check: bool = Field(default=True)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "env_prefix": "",  # No prefix, use same env vars
    }


@lru_cache(maxsize=1)
def get_bot_settings() -> BotSettings:
    """Get cached bot settings instance."""
    return BotSettings()


# Convenience alias
settings = get_bot_settings()
