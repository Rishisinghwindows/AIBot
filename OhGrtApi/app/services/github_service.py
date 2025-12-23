from __future__ import annotations

from typing import Optional

import httpx

from app.logger import logger


class GitHubService:
    """
    Minimal GitHub client for issues.

    Requires:
      - token: GitHub PAT with repo scope
      - owner: repo owner/org
      - repo: repository name
    """

    def __init__(self, token: Optional[str], owner: Optional[str], repo: Optional[str]) -> None:
        self.token = token or ""
        self.owner = owner or ""
        self.repo = repo or ""
        self.available = all([self.token, self.owner, self.repo])

    @property
    def _base(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"

    async def search_issues(self, query: str) -> str:
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."
        # Search limited to given repo
        q = f"repo:{self.owner}/{self.repo} {query}"
        url = "https://api.github.com/search/issues"
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url, params={"q": q, "per_page": 5})
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", [])
                if not items:
                    return "No matching GitHub issues."
                parts = []
                for item in items:
                    number = item.get("number")
                    title = item.get("title", "")
                    state = item.get("state", "")
                    parts.append(f"#{number} [{state}] {title}")
                return "; ".join(parts)
        except Exception as exc:  # noqa: BLE001
            logger.error("github_search_error", error=_format_error(exc))
            return f"GitHub search failed: {_format_error(exc)}"

    async def create_issue(self, title: str, body: str) -> str:
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."
        url = f"{self._base}/issues"
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.post(url, json={"title": title, "body": body})
                resp.raise_for_status()
                data = resp.json()
                number = data.get("number")
                html_url = data.get("html_url", "")
                return f"Created issue #{number} {html_url}"
        except Exception as exc:  # noqa: BLE001
            logger.error("github_create_error", error=_format_error(exc))
            return f"GitHub create failed: {_format_error(exc)}"

    def _headers(self) -> dict:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        body = exc.response.text[:500]
        return f"HTTP {status}: {body}"
    return str(exc)
