from __future__ import annotations

from typing import Optional

import httpx

from app.logger import logger


class CustomMCPService:
    """
    Lightweight client for a user-specified MCP-like HTTP endpoint.

    Expects the user to provide:
      - base_url: root URL of the MCP endpoint
      - access token (optional): sent as Bearer auth

    It POSTs {prompt: "..."} to `${base_url}/query` and expects JSON with either
    `reply` or `response`. Falls back to raw text.
    """

    def __init__(self, base_url: Optional[str], token: Optional[str]) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.token = token or ""
        self.available = bool(self.base_url)

    async def query(self, prompt: str) -> str:
        if not self.available:
            return "Custom MCP not configured. Provide a base URL (and optional token)."

        url = f"{self.base_url}/query"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json={"prompt": prompt}, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                # Accept a few common shapes
                if isinstance(data, dict):
                    if "reply" in data:
                        return str(data["reply"])
                    if "response" in data:
                        return str(data["response"])
                # Fallback to text
                return resp.text
        except Exception as exc:  # noqa: BLE001
            logger.error("custom_mcp_error", error=_format_error(exc))
            return f"Custom MCP unavailable: {_format_error(exc)}"


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        body = exc.response.text[:500]
        return f"HTTP {status}: {body}"
    return str(exc)
