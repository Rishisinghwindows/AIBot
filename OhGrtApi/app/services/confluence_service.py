from __future__ import annotations

import httpx

from app.interfaces import ConfluenceSettingsProtocol
from app.logger import logger
from app.utils.errors import ServiceError


class ConfluenceService:
    """
    Confluence REST API client for searching and reading pages.

    Accepts any settings object that implements ConfluenceSettingsProtocol,
    allowing both app-level Settings and user-specific UserToolSettings.
    """

    def __init__(
        self,
        settings: ConfluenceSettingsProtocol,
        base_url_override: str | None = None,
        user_override: str | None = None,
        token_override: str | None = None,
    ):
        self.base_url = base_url_override or getattr(settings, "confluence_base_url", "")
        self.user = user_override or getattr(settings, "confluence_user", "")
        self.api_token = token_override or getattr(settings, "confluence_api_token", "")
        self.available = all([self.base_url, self.user, self.api_token])

    async def search(self, query: str) -> str:
        if not self.available:
            return "Confluence is not configured. Set base URL, user, and API token."
        url = f"{self.base_url}/rest/api/content/search"
        params = {"cql": query, "limit": 5}
        try:
            async with httpx.AsyncClient(timeout=10, auth=(self.user, self.api_token)) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    return "No Confluence pages found."
                formatted = []
                for r in results:
                    title = r.get("title", "")
                    links = r.get("_links", {}) if isinstance(r, dict) else {}
                    webui = links.get("webui", "")
                    url = f"{self.base_url}{webui}" if webui else ""
                    if url:
                        formatted.append(f"{title} -> {url}")
                    else:
                        formatted.append(title)
                return "Confluence results: " + "; ".join(formatted)
        except Exception as exc:  # noqa: BLE001
            logger.error("confluence_query_error", error=str(exc))
            return f"Confluence unavailable: {exc}"
