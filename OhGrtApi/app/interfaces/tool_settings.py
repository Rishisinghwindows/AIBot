"""
Tool Settings Interface/Protocol

Defines the interface that both app-level Settings and user-specific
UserToolSettings must implement for tool services to work with either.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class JiraSettingsProtocol(Protocol):
    """Protocol for Jira configuration."""
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str


@runtime_checkable
class GitHubSettingsProtocol(Protocol):
    """Protocol for GitHub configuration."""
    github_token: str
    github_default_repo: str


@runtime_checkable
class LinearSettingsProtocol(Protocol):
    """Protocol for Linear configuration."""
    linear_api_key: str


@runtime_checkable
class NotionSettingsProtocol(Protocol):
    """Protocol for Notion configuration."""
    notion_api_key: str


@runtime_checkable
class SlackSettingsProtocol(Protocol):
    """Protocol for Slack configuration."""
    slack_token: str


@runtime_checkable
class ConfluenceSettingsProtocol(Protocol):
    """Protocol for Confluence configuration."""
    confluence_base_url: str
    confluence_user: str
    confluence_api_token: str


@runtime_checkable
class PostgresSettingsProtocol(Protocol):
    """Protocol for PostgreSQL configuration (user's custom DB)."""
    user_postgres_host: str
    user_postgres_port: int
    user_postgres_user: str
    user_postgres_password: str
    user_postgres_db: str
    user_postgres_schema: str


@runtime_checkable
class GmailSettingsProtocol(Protocol):
    """Protocol for Gmail configuration."""
    gmail_mcp_endpoint: str
    gmail_mcp_api_key: str
    gmail_credentials_file: str
    gmail_token_file: str


@runtime_checkable
class WeatherSettingsProtocol(Protocol):
    """Protocol for Weather API configuration."""
    openweather_api_key: str
    openweather_base_url: str


@runtime_checkable
class OpenAISettingsProtocol(Protocol):
    """Protocol for OpenAI configuration."""
    openai_api_key: str
    openai_model: str


# Combined protocol for services that need multiple configs
@runtime_checkable
class AllToolSettingsProtocol(
    JiraSettingsProtocol,
    GitHubSettingsProtocol,
    LinearSettingsProtocol,
    NotionSettingsProtocol,
    SlackSettingsProtocol,
    ConfluenceSettingsProtocol,
    Protocol
):
    """Combined protocol for all user-configurable tools."""
    pass
