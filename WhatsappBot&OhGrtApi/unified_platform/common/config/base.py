"""
Base Configuration Settings.

This module provides the base configuration class with settings
common to both WhatsApp Bot and OhGrt API applications.
"""

import os
from functools import lru_cache
from typing import Optional, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class BaseSettings(PydanticBaseSettings):
    """
    Base settings shared across all applications.

    Applications should extend this class to add their specific settings.
    """

    # Environment
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Lite Mode - run without database
    lite_mode: bool = Field(
        default=False,
        description="Run in lite mode (no database required)"
    )

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model")

    # Ollama (optional local LLM)
    ollama_server: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL"
    )
    ollama_model: str = Field(
        default="qwen3-vl:8b",
        description="Default Ollama model"
    )

    # Database
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="postgres", description="PostgreSQL password")
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="postgres", description="PostgreSQL database name")
    postgres_schema: str = Field(default="agentic", description="PostgreSQL schema")

    # Redis (for caching and rate limiting)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # WhatsApp Cloud API
    whatsapp_access_token: str = Field(
        default="",
        description="WhatsApp Cloud API access token"
    )
    whatsapp_phone_number_id: str = Field(
        default="",
        description="WhatsApp phone number ID"
    )
    whatsapp_verify_token: str = Field(
        default="verify-token",
        description="Webhook verification token"
    )
    whatsapp_app_secret: Optional[str] = Field(
        default=None,
        description="WhatsApp app secret for signature verification"
    )

    # External APIs
    openweather_api_key: str = Field(default="", description="OpenWeather API key")
    openweather_base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5/weather",
        description="OpenWeather endpoint"
    )

    # Image Generation (fal.ai)
    fal_key: str = Field(default="", description="fal.ai API key")

    # Search APIs
    tavily_api_key: str = Field(default="", description="Tavily API key")
    serper_api_key: str = Field(default="", description="Serper API key")

    # News API
    news_api_key: str = Field(default="", description="News API key")

    # Astrology API
    astrology_api_key: str = Field(default="", description="Astrology API key")

    # Railway/Travel APIs
    railway_api_key: str = Field(default="", description="RapidAPI key for railway APIs")

    # LangSmith Tracing
    langsmith_tracing: str = Field(default="false", description="Enable LangSmith tracing")
    langsmith_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langsmith_project: str = Field(default="unified-platform", description="LangSmith project")
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith endpoint"
    )

    # Language Settings
    default_language: str = Field(default="en", description="Default language")
    auto_detect_language: bool = Field(
        default=True,
        description="Auto-detect user's language"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def database_url(self) -> str:
        """Get the database connection URL."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def configure_langsmith(self) -> None:
        """Configure LangSmith tracing if enabled."""
        if self.langsmith_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = self.langsmith_tracing
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
            os.environ["LANGCHAIN_ENDPOINT"] = self.langsmith_endpoint

    def configure_fal(self) -> None:
        """Configure fal.ai client."""
        if self.fal_key:
            os.environ["FAL_KEY"] = self.fal_key


@lru_cache(maxsize=1)
def get_base_settings() -> BaseSettings:
    """Get cached base settings instance."""
    return BaseSettings()
