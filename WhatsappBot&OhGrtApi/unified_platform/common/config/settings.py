"""
Configuration Management

Loads environment variables and provides settings object.
Compatible with both d23apiv1 and OhGrt API patterns.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(PydanticBaseSettings):
    """Application settings loaded from environment."""

    # Lite Mode (no database required)
    LITE_MODE: bool = Field(default=False, alias="lite_mode")

    # Environment
    ENVIRONMENT: str = Field(default="development", alias="environment")

    # OpenAI
    OPENAI_API_KEY: str = Field(default="", alias="openai_api_key")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", alias="openai_model")

    # WhatsApp Cloud API
    WHATSAPP_ACCESS_TOKEN: str = Field(default="", alias="whatsapp_access_token")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(default="", alias="whatsapp_phone_number_id")
    WHATSAPP_VERIFY_TOKEN: str = Field(default="", alias="whatsapp_verify_token")
    WHATSAPP_APP_SECRET: Optional[str] = Field(default=None, alias="whatsapp_app_secret")

    # fal.ai
    FAL_KEY: str = Field(default="", alias="fal_key")

    # Tavily
    TAVILY_API_KEY: str = Field(default="", alias="tavily_api_key")

    # Serper (Google Search API)
    SERPER_API_KEY: str = Field(default="", alias="serper_api_key")

    # Railway API (RapidAPI)
    RAILWAY_API_KEY: str = Field(default="", alias="railway_api_key")

    # News API
    NEWS_API_KEY: str = Field(default="", alias="news_api_key")

    # OpenWeather API
    OPENWEATHER_API_KEY: str = Field(default="", alias="openweather_api_key")

    # Astrology API
    ASTROLOGY_API_KEY: str = Field(default="", alias="astrology_api_key")

    # LangSmith
    LANGSMITH_TRACING: str = Field(default="false", alias="langsmith_tracing")
    LANGSMITH_API_KEY: Optional[str] = Field(default=None, alias="langsmith_api_key")
    LANGSMITH_PROJECT: str = Field(default="unified-platform", alias="langsmith_project")
    LANGSMITH_ENDPOINT: str = Field(default="https://api.smith.langchain.com", alias="langsmith_endpoint")

    # Database
    POSTGRES_USER: str = Field(default="postgres", alias="postgres_user")
    POSTGRES_PASSWORD: str = Field(default="postgres", alias="postgres_password")
    POSTGRES_HOST: str = Field(default="localhost", alias="postgres_host")
    POSTGRES_PORT: int = Field(default=5432, alias="postgres_port")
    POSTGRES_DB: str = Field(default="postgres", alias="postgres_db")
    POSTGRES_SCHEMA: str = Field(default="agentic", alias="postgres_schema")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", alias="redis_url")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", alias="log_level")

    # Language Settings
    DEFAULT_LANGUAGE: str = Field(default="en", alias="default_language")
    AUTO_DETECT_LANGUAGE: bool = Field(default=True, alias="auto_detect_language")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }

    @property
    def database_url(self) -> str:
        """Get the database connection URL."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

# Aliases for compatibility
get_base_settings = get_settings


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
