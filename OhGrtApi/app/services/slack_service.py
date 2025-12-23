from __future__ import annotations

from typing import Optional

import httpx

from app.interfaces import SlackSettingsProtocol
from app.logger import logger
from app.utils.errors import ServiceError


class SlackService:
    """
    Slack REST API client for posting messages and reading channels.

    Supports two authentication modes:
    1. OAuth 2.0 (preferred): Uses access_token from IntegrationCredential
    2. Legacy Bot Token: Uses slack_token from settings

    Accepts any settings object that implements SlackSettingsProtocol,
    allowing both app-level Settings and user-specific UserToolSettings.
    """

    def __init__(
        self,
        settings: SlackSettingsProtocol = None,
        *,
        access_token: str = None,
        team_name: str = None,
    ):
        """
        Initialize SlackService with either OAuth credentials or legacy bot token.

        OAuth mode (preferred):
            SlackService(access_token="...", team_name="...")

        Legacy bot token mode:
            SlackService(settings=user_settings)
        """
        # OAuth mode
        self.access_token = access_token
        self.team_name = team_name
        self.use_oauth = bool(access_token)

        # Legacy bot token mode
        self.token = ""

        if settings:
            self.token = getattr(settings, "slack_token", "") or ""

        # Use OAuth token or legacy bot token
        self._auth_token = self.access_token if self.use_oauth else self.token
        self.available = bool(self._auth_token)

    async def post_message(self, channel: str, text: str) -> str:
        if not self.available:
            return "Slack is not configured. Please connect Slack in Settings > Integrations."
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {self._auth_token}"},
                    data={"channel": channel, "text": text},
                )
                data = resp.json()
                if not data.get("ok"):
                    raise ServiceError(f"Slack error: {data.get('error')}")
                return f"Posted to {channel}"
        except Exception as exc:  # noqa: BLE001
            logger.error("slack_post_error", error=str(exc))
            return f"Slack unavailable: {exc}"
