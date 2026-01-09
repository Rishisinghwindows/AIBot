from __future__ import annotations

import httpx

from ohgrt_api.config import Settings
from ohgrt_api.logger import logger
from ohgrt_api.utils.errors import ServiceError


class ConfluenceService:
    """
    Placeholder Confluence MCP/REST client.
    Set CONFLUENCE_BASE_URL and CONFLUENCE_API_TOKEN/USER in .env to enable.
    """

    def __init__(
        self,
        settings: Settings,
        base_url_override: str | None = None,
        user_override: str | None = None,
        token_override: str | None = None,
    ):
        self.settings = settings
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
            logger.error("confluence_query_error", error=_format_error(exc))
            return f"Confluence unavailable: {_format_error(exc)}"


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        body = exc.response.text[:500]
        return f"HTTP {status}: {body}"
    return str(exc)
