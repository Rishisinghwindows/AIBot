"""
User Tool Configuration Service

This module provides a way to load user-specific tool configurations
from the mcp_tools database table and create service instances with
those credentials.

The UserToolSettings class implements all tool-specific protocols defined
in app.interfaces, allowing it to be used interchangeably with the main
Settings class when creating service instances.

For OAuth-based integrations (like Jira, Gmail), credentials are loaded
from the IntegrationCredential table instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.config import Settings
from app.db.base import get_db
from app.db.models import IntegrationCredential
from app.services.mcp_tool_service import McpToolService
from app.services.github_service import GitHubService
from app.services.jira_service import JiraService
from app.services.linear_service import LinearService
from app.services.notion_service import NotionService
from app.services.slack_service import SlackService
from app.services.confluence_service import ConfluenceService
from app.interfaces import (
    JiraSettingsProtocol,
    GitHubSettingsProtocol,
    LinearSettingsProtocol,
    NotionSettingsProtocol,
    SlackSettingsProtocol,
    ConfluenceSettingsProtocol,
    PostgresSettingsProtocol,
)
from app.logger import logger


@dataclass
class UserToolSettings:
    """
    A settings object that holds user-specific tool configurations.

    Implements all tool-specific protocols so it can be used with any
    service that accepts those protocols. This allows the same service
    classes to work with both app-level Settings and user-specific
    UserToolSettings.

    Protocols implemented:
    - JiraSettingsProtocol
    - GitHubSettingsProtocol
    - LinearSettingsProtocol
    - NotionSettingsProtocol
    - SlackSettingsProtocol
    - ConfluenceSettingsProtocol
    - PostgresSettingsProtocol
    """
    # Jira (implements JiraSettingsProtocol)
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""

    # GitHub (implements GitHubSettingsProtocol)
    github_token: str = ""
    github_default_repo: str = ""

    # Linear (implements LinearSettingsProtocol)
    linear_api_key: str = ""

    # Notion (implements NotionSettingsProtocol)
    notion_api_key: str = ""

    # Slack (implements SlackSettingsProtocol)
    slack_token: str = ""

    # Confluence (implements ConfluenceSettingsProtocol)
    confluence_base_url: str = ""
    confluence_user: str = ""
    confluence_api_token: str = ""

    # PostgreSQL - user's custom DB (implements PostgresSettingsProtocol)
    user_postgres_host: str = ""
    user_postgres_port: int = 5432
    user_postgres_user: str = ""
    user_postgres_password: str = ""
    user_postgres_db: str = ""
    user_postgres_schema: str = ""

    def is_jira_configured(self) -> bool:
        """Check if Jira credentials are configured."""
        return bool(self.jira_base_url and self.jira_email and self.jira_api_token)

    def is_github_configured(self) -> bool:
        """Check if GitHub credentials are configured."""
        return bool(self.github_token)

    def is_linear_configured(self) -> bool:
        """Check if Linear credentials are configured."""
        return bool(self.linear_api_key)

    def is_notion_configured(self) -> bool:
        """Check if Notion credentials are configured."""
        return bool(self.notion_api_key)

    def is_slack_configured(self) -> bool:
        """Check if Slack credentials are configured."""
        return bool(self.slack_token)

    def is_confluence_configured(self) -> bool:
        """Check if Confluence credentials are configured."""
        return bool(self.confluence_base_url and self.confluence_user and self.confluence_api_token)

    def is_postgres_configured(self) -> bool:
        """Check if user PostgreSQL credentials are configured."""
        return bool(self.user_postgres_host and self.user_postgres_user and self.user_postgres_db)


class UserToolConfigService:
    """
    Service to load user-specific tool configurations and create
    appropriately configured service instances.
    """

    # Mapping of tool names to their config field mappings
    TOOL_CONFIG_MAPPINGS = {
        "jira": {
            "base_url": "jira_base_url",
            "email": "jira_email",
            "api_token": "jira_api_token",
            "project_key": "jira_project_key",
        },
        "github": {
            "token": "github_token",
            "default_repo": "github_default_repo",
        },
        "linear": {
            "api_key": "linear_api_key",
        },
        "notion": {
            "api_key": "notion_api_key",
        },
        "slack": {
            "token": "slack_token",
        },
        "confluence": {
            "base_url": "confluence_base_url",
            "user": "confluence_user",
            "api_token": "confluence_api_token",
        },
        "postgresql": {
            "host": "user_postgres_host",
            "port": "user_postgres_port",
            "user": "user_postgres_user",
            "password": "user_postgres_password",
            "db": "user_postgres_db",
            "schema": "user_postgres_schema",
        },
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.mcp_tool_service = McpToolService(settings)

    def get_user_tool_settings(self, user_id: UUID) -> UserToolSettings:
        """
        Load all user's tool configurations from DB and return
        a UserToolSettings object with the values populated.
        """
        user_settings = UserToolSettings()

        try:
            user_tools = self.mcp_tool_service.get_mcp_tools_by_user(user_id)

            for tool in user_tools:
                if not tool.enabled:
                    continue

                tool_name = tool.name.lower()
                config = tool.config or {}

                # Get the mapping for this tool type
                mapping = self.TOOL_CONFIG_MAPPINGS.get(tool_name)
                if not mapping:
                    logger.debug("unknown_tool_config", tool_name=tool_name)
                    continue

                # Apply config values to user_settings
                for config_key, settings_attr in mapping.items():
                    if config_key in config:
                        value = config[config_key]
                        # Handle type conversion for port
                        if settings_attr == "user_postgres_port":
                            value = int(value) if value else 5432
                        setattr(user_settings, settings_attr, value)

        except Exception as exc:
            logger.error("load_user_tool_config_error", user_id=str(user_id), error=str(exc))

        return user_settings

    def get_enabled_tools(self, user_id: UUID) -> List[str]:
        """Return list of enabled tool names for a user."""
        try:
            user_tools = self.mcp_tool_service.get_mcp_tools_by_user(user_id)
            return [tool.name.lower() for tool in user_tools if tool.enabled]
        except Exception as exc:
            logger.error("get_enabled_tools_error", user_id=str(user_id), error=str(exc))
            return []

    def create_jira_service(self, user_settings: UserToolSettings) -> JiraService:
        """Create JiraService with user-specific credentials."""
        return JiraService(user_settings)

    def create_github_service(self, user_settings: UserToolSettings) -> GitHubService:
        """Create GitHubService with user-specific credentials."""
        return GitHubService(user_settings)

    def create_linear_service(self, user_settings: UserToolSettings) -> LinearService:
        """Create LinearService with user-specific credentials."""
        return LinearService(user_settings)

    def create_notion_service(self, user_settings: UserToolSettings) -> NotionService:
        """Create NotionService with user-specific credentials."""
        return NotionService(user_settings)

    def create_slack_service(self, user_settings: UserToolSettings) -> SlackService:
        """Create SlackService with user-specific credentials."""
        return SlackService(user_settings)

    def create_confluence_service(self, user_settings: UserToolSettings) -> ConfluenceService:
        """Create ConfluenceService with user-specific credentials."""
        return ConfluenceService(user_settings)


def _get_oauth_credential(user_id: UUID, provider: str) -> Optional[IntegrationCredential]:
    """Get OAuth credential from IntegrationCredential table for a user and provider."""
    try:
        db = next(get_db())
        cred = (
            db.query(IntegrationCredential)
            .filter(
                IntegrationCredential.user_id == user_id,
                IntegrationCredential.provider == provider,
            )
            .first()
        )
        return cred
    except Exception as exc:
        logger.error("get_oauth_credential_error", user_id=str(user_id), provider=provider, error=str(exc))
        return None


def build_user_services(settings: Settings, user_id: UUID) -> Dict[str, Any]:
    """
    Build all user-specific service instances based on their
    configured and enabled tools.

    Returns a dict of service name -> service instance.

    For OAuth-based integrations (Jira, Gmail, etc.), credentials are loaded
    from the IntegrationCredential table. For legacy API-key integrations,
    credentials are loaded from the mcp_tools table.
    """
    config_service = UserToolConfigService(settings)
    user_settings = config_service.get_user_tool_settings(user_id)
    enabled_tools = config_service.get_enabled_tools(user_id)

    services = {}

    # Jira - Check OAuth credentials first, then fall back to legacy API key
    jira_oauth = _get_oauth_credential(user_id, "jira")
    if jira_oauth and jira_oauth.access_token:
        config = jira_oauth.config or {}
        services["jira"] = JiraService(
            access_token=jira_oauth.access_token,
            cloud_id=config.get("cloud_id"),
            site_url=config.get("site_url"),
            refresh_token=config.get("refresh_token"),
        )
        logger.debug("jira_oauth_service_created", user_id=str(user_id))
    elif "jira" in enabled_tools:
        services["jira"] = config_service.create_jira_service(user_settings)
    else:
        # Create with empty settings so it reports "not configured"
        services["jira"] = JiraService()

    # GitHub - Check OAuth credentials first, then fall back to legacy PAT
    github_oauth = _get_oauth_credential(user_id, "github")
    if github_oauth and github_oauth.access_token:
        config = github_oauth.config or {}
        services["github"] = GitHubService(
            access_token=github_oauth.access_token,
            owner=config.get("owner"),
        )
        logger.debug("github_oauth_service_created", user_id=str(user_id))
    elif "github" in enabled_tools:
        services["github"] = config_service.create_github_service(user_settings)
    else:
        # Create with empty settings so it reports "not configured"
        services["github"] = GitHubService()

    if "linear" in enabled_tools:
        services["linear"] = config_service.create_linear_service(user_settings)
    else:
        services["linear"] = LinearService(UserToolSettings())

    if "notion" in enabled_tools:
        services["notion"] = config_service.create_notion_service(user_settings)
    else:
        services["notion"] = NotionService(UserToolSettings())

    # Slack - Check OAuth credentials first, then fall back to legacy bot token
    slack_oauth = _get_oauth_credential(user_id, "slack")
    if slack_oauth and slack_oauth.access_token:
        config = slack_oauth.config or {}
        team = config.get("team") or {}
        services["slack"] = SlackService(
            access_token=slack_oauth.access_token,
            team_name=team.get("name") if team else None,
        )
        logger.debug("slack_oauth_service_created", user_id=str(user_id))
    elif "slack" in enabled_tools:
        services["slack"] = config_service.create_slack_service(user_settings)
    else:
        # Create with empty settings so it reports "not configured"
        services["slack"] = SlackService()

    if "confluence" in enabled_tools:
        services["confluence"] = config_service.create_confluence_service(user_settings)
    else:
        services["confluence"] = ConfluenceService(UserToolSettings())

    return services
