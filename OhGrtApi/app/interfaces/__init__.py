"""Interfaces and protocols for D23 API services."""

from app.interfaces.tool_settings import (
    JiraSettingsProtocol,
    GitHubSettingsProtocol,
    LinearSettingsProtocol,
    NotionSettingsProtocol,
    SlackSettingsProtocol,
    ConfluenceSettingsProtocol,
    PostgresSettingsProtocol,
    GmailSettingsProtocol,
    WeatherSettingsProtocol,
    OpenAISettingsProtocol,
    AllToolSettingsProtocol,
)

__all__ = [
    "JiraSettingsProtocol",
    "GitHubSettingsProtocol",
    "LinearSettingsProtocol",
    "NotionSettingsProtocol",
    "SlackSettingsProtocol",
    "ConfluenceSettingsProtocol",
    "PostgresSettingsProtocol",
    "GmailSettingsProtocol",
    "WeatherSettingsProtocol",
    "OpenAISettingsProtocol",
    "AllToolSettingsProtocol",
]
