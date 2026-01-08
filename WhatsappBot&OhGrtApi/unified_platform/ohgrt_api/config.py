"""
OhGrt API Configuration.

Extends the base configuration with API-specific settings.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator, model_validator

from common.config.base import BaseSettings


class APISettings(BaseSettings):
    """
    OhGrt API specific settings.

    Extends BaseSettings with API-specific configuration.
    """

    # API Identity
    api_name: str = Field(default="OhGrt API", description="API display name")
    api_version: str = Field(default="2.1.0", description="API version")

    # CORS
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed origins"
    )

    # JWT Settings
    jwt_secret_key: str = Field(default="", description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=15)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # Firebase
    firebase_credentials_path: str = Field(
        default="firebase-credentials.json",
        description="Path to Firebase service account"
    )

    # Security
    request_timestamp_tolerance_seconds: int = Field(default=300)
    nonce_expiry_hours: int = Field(default=24)
    encryption_key: str = Field(default="", description="Fernet encryption key")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_minute: int = Field(default=60)
    rate_limit_requests_per_hour: int = Field(default=1000)

    # OAuth - Gmail
    google_oauth_client_id: str = Field(default="")
    google_oauth_client_secret: str = Field(default="")
    google_oauth_redirect_uri: str = Field(
        default="http://localhost:3000/settings/gmail/callback"
    )
    google_gmail_scopes: str = Field(
        default="https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send"
    )
    google_drive_scopes: str = Field(
        default="https://www.googleapis.com/auth/drive.readonly"
    )

    # OAuth - GitHub
    github_client_id: str = Field(default="")
    github_client_secret: str = Field(default="")
    github_redirect_uri: str = Field(
        default="http://localhost:3000/settings/github/callback"
    )

    # OAuth - Slack
    slack_client_id: str = Field(default="")
    slack_client_secret: str = Field(default="")
    slack_redirect_uri: str = Field(
        default="http://localhost:3000/settings/slack/callback"
    )
    slack_token: str = Field(default="")

    # OAuth - Jira/Atlassian
    atlassian_client_id: str = Field(default="")
    atlassian_client_secret: str = Field(default="")
    atlassian_redirect_uri: str = Field(
        default="http://localhost:3000/settings/jira/callback"
    )

    # OAuth - Uber
    uber_client_id: str = Field(default="")
    uber_client_secret: str = Field(default="")
    uber_redirect_uri: str = Field(
        default="http://localhost:3000/settings/uber/callback"
    )

    # Confluence
    confluence_base_url: str = Field(default="")
    confluence_user: str = Field(default="")
    confluence_api_token: str = Field(default="")

    # pgvector for RAG
    pgvector_table: str = Field(default="pdf_vectors")
    embedding_dimension: int = Field(default=1536)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v and os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise ValueError("JWT_SECRET_KEY must be set in production")
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "APISettings":
        """Validate production settings."""
        if self.environment != "production":
            return self

        errors = []

        if self.postgres_password == "postgres":
            errors.append("POSTGRES_PASSWORD must not use default in production")

        if not self.encryption_key:
            errors.append("ENCRYPTION_KEY must be set in production")

        if self.cors_origins == "*":
            errors.append("CORS_ORIGINS must not be '*' in production")

        if errors:
            raise ValueError("Production errors:\n- " + "\n- ".join(errors))

        return self

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_api_settings() -> APISettings:
    """Get cached API settings instance."""
    return APISettings()


# Convenience aliases
Settings = APISettings
settings = get_api_settings()
get_settings = get_api_settings  # Alias for MCP and other modules
