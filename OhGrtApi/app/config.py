from functools import lru_cache
import os
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with validation.

    All sensitive values should be provided via environment variables.
    """

    # Environment
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )

    # CORS - comma-separated origins or * for development
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed origins, or * for all (dev only)"
    )

    # Ollama - no hardcoded IPs, must be configured
    ollama_server: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL"
    )
    ollama_model: str = Field(default="qwen3-vl:8b", description="Default LLM model id")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model")

    # External APIs
    openweather_api_key: str = Field(default="", description="OpenWeather API key")
    openweather_base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5/weather",
        description="OpenWeather endpoint",
    )

    # Database - defaults are for development only
    postgres_user: str = Field(
        default="postgres",
        description="PostgreSQL username (must be set in production)"
    )
    postgres_password: str = Field(
        default="postgres",
        description="PostgreSQL password (must be set in production)"
    )
    postgres_host: str = Field(
        default="localhost",
        description="PostgreSQL host (must be set in production)"
    )
    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port"
    )
    postgres_db: str = Field(
        default="postgres",
        description="PostgreSQL database name (must be set in production)"
    )
    postgres_schema: str = Field(
        default="agentic",
        description="PostgreSQL schema"
    )
    pgvector_table: str = Field(
        default="pdf_vectors",
        description="pgvector table name"
    )
    embedding_dimension: int = Field(
        default=1536,
        description="Embedding dimension for vectors"
    )

    # Gmail MCP
    gmail_mcp_endpoint: str = "http://localhost:8001"
    gmail_mcp_api_key: str = ""
    gmail_credentials_file: str = "credentials.json"
    gmail_token_file: str = "token.json"
    slack_token: str = ""
    slack_client_id: str = ""
    slack_client_secret: str = ""
    slack_redirect_uri: str = "ohgrt://oauth/slack"
    confluence_base_url: str = ""
    confluence_user: str = ""
    confluence_api_token: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "ohgrt://oauth/github"
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "ohgrt://oauth/google"
    google_gmail_scopes: str = "https://www.googleapis.com/auth/gmail.readonly"
    google_drive_scopes: str = "https://www.googleapis.com/auth/drive.readonly"

    # Jira/Atlassian OAuth
    atlassian_client_id: str = ""
    atlassian_client_secret: str = ""
    atlassian_redirect_uri: str = "ohgrt://oauth/jira"

    # Uber OAuth
    uber_client_id: str = ""
    uber_client_secret: str = ""
    uber_redirect_uri: str = "ohgrt://oauth/uber"

    # JWT Settings
    jwt_secret_key: str = Field(default="", description="Secret key for JWT signing")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=15, description="Access token expiry in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiry in days"
    )

    # Firebase Settings
    firebase_credentials_path: str = Field(
        default="firebase-credentials.json", description="Path to Firebase service account"
    )

    # Security Settings
    request_timestamp_tolerance_seconds: int = Field(
        default=300, description="Max age of request timestamp (5 minutes)"
    )
    nonce_expiry_hours: int = Field(
        default=24, description="How long to keep nonces for replay prevention"
    )
    encryption_key: str = Field(
        default="", description="Fernet encryption key for storing credentials (32 bytes base64)"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True, description="Enable rate limiting"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60, description="Max requests per minute per user"
    )
    rate_limit_requests_per_hour: int = Field(
        default=1000, description="Max requests per hour per user"
    )

    # Redis (for rate limiting and caching)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # WhatsApp Cloud API Settings
    whatsapp_access_token: str = Field(
        default="", description="WhatsApp Cloud API access token"
    )
    whatsapp_phone_number_id: str = Field(
        default="", description="WhatsApp phone number ID"
    )
    whatsapp_verify_token: str = Field(
        default="ohgrt-verify-token", description="Webhook verification token"
    )
    whatsapp_app_secret: Optional[str] = Field(
        default=None, description="WhatsApp app secret for signature verification"
    )

    # Image Generation (fal.ai)
    fal_key: str = Field(default="", description="fal.ai API key for image generation")

    # Tavily Search
    tavily_api_key: str = Field(default="", description="Tavily API key for web search")

    # Railway/Travel APIs
    railway_api_key: str = Field(default="", description="RapidAPI key for railway APIs")

    # News API
    news_api_key: str = Field(default="", description="News API key")

    # Astrology API
    astrology_api_key: str = Field(default="", description="Astrology API key")

    # LangSmith Tracing
    langsmith_tracing: str = Field(default="false", description="Enable LangSmith tracing")
    langsmith_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langsmith_project: str = Field(default="ohgrt-api", description="LangSmith project name")

    # Misc
    log_level: str = "INFO"
    debug: bool = False
    lite_mode: bool = Field(
        default=False, description="Run in lite mode (no database checkpointing)"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v.lower()

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        # In production, JWT secret must be set
        if not v:
            if os.getenv("ENVIRONMENT", "development").lower() == "production":
                raise ValueError("JWT_SECRET_KEY must be set in production")
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate that required settings are properly configured in production."""
        if self.environment != "production":
            return self

        errors = []

        # Database credentials must not use defaults in production
        if self.postgres_password == "postgres":
            errors.append("POSTGRES_PASSWORD must not use default value in production")

        if self.postgres_user == "postgres" and self.postgres_host != "localhost":
            # Using default user on non-localhost is suspicious
            errors.append("POSTGRES_USER should not use default 'postgres' in production")

        if self.postgres_host == "localhost":
            errors.append("POSTGRES_HOST should not be 'localhost' in production")

        # Encryption key must be set for credential storage
        if not self.encryption_key:
            errors.append("ENCRYPTION_KEY must be set in production for secure credential storage")

        # CORS should not be wildcard in production
        if self.cors_origins == "*":
            errors.append("CORS_ORIGINS must not be '*' in production")

        # WhatsApp app secret should be set for webhook verification
        if self.whatsapp_access_token and not self.whatsapp_app_secret:
            errors.append("WHATSAPP_APP_SECRET should be set for webhook signature verification")

        if errors:
            raise ValueError(
                "Production configuration errors:\n- " + "\n- ".join(errors)
            )

        return self

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

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
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
