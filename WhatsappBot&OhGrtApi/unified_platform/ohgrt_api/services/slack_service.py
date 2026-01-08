from __future__ import annotations

from typing import Optional

import httpx

from ohgrt_api.config import Settings
from ohgrt_api.logger import logger
from ohgrt_api.utils.errors import ServiceError


class SlackService:
    """
    Placeholder Slack MCP/REST client.
    If you have a Slack MCP server or REST token, set it in .env and flip available=True.
    """

    def __init__(self, settings: Settings, token_override: Optional[str] = None):
        self.settings = settings
        self.token = token_override or getattr(settings, "slack_token", "") or ""
        self.available = bool(self.token)

    async def post_message(self, channel: str, text: str) -> str:
        if not self.available:
            return "Slack is not configured. Set SLACK_TOKEN and endpoint to enable."
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {self.token}"},
                    data={"channel": channel, "text": text},
                )
                data = resp.json()
                if not data.get("ok"):
                    error = data.get("error") or "unknown_error"
                    raise ServiceError(f"Slack error: {error}")
                return f"Posted to {channel}"
        except Exception as exc:  # noqa: BLE001
            logger.error("slack_post_error", error=_format_error(exc))
            return f"Slack unavailable: {_format_error(exc)}"


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"
    return str(exc)
