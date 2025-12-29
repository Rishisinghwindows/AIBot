"""
Configuration Management

Loads environment variables and provides settings object.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Lite Mode (no database required)
    LITE_MODE: bool = False  # Set to True for in-memory only storage

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # WhatsApp Cloud API
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: Optional[str] = None

    # fal.ai
    FAL_KEY: str = ""

    # Tavily
    TAVILY_API_KEY: str = ""

    # Serper (Google Search API)
    SERPER_API_KEY: str = ""

    # Railway API (RapidAPI)
    # Same key works for both PNR and Train Status APIs
    RAILWAY_API_KEY: str = ""

    # News API
    NEWS_API_KEY: str = ""

    # OpenWeather API
    OPENWEATHER_API_KEY: str = ""

    # Astrology API
    ASTROLOGY_API_KEY: str = ""

    # LangSmith
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "whatsapp-ai-assistant"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # Database (existing)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"
    POSTGRES_SCHEMA: str = "agentic" # Added postgres schema

    # Logging
    LOG_LEVEL: str = "INFO"

    # Language Settings
    DEFAULT_LANGUAGE: str = "en"  # Default language for responses
    AUTO_DETECT_LANGUAGE: bool = True  # Auto-detect user's language from message
    TRANSLATION_API: str = ""  # Google Translate API key (optional)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()


def configure_langsmith():
    """Configure LangSmith tracing if enabled."""
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGSMITH_TRACING
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT


def configure_fal():
    """Configure fal.ai client."""
    if settings.FAL_KEY:
        os.environ["FAL_KEY"] = settings.FAL_KEY
