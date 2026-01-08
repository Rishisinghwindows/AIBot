from __future__ import annotations

from typing import List, Optional

import httpx

from ohgrt_api.config import Settings
from ohgrt_api.logger import logger
from ohgrt_api.utils.errors import ServiceError


class JiraService:
    """
    Placeholder JIRA MCP service.
    Replace with a real MCP client or REST client when available.
    """

    def __init__(
        self,
        settings: Settings,
        base_url: str | None = None,
        email: str | None = None,
        token: str | None = None,
        project_key: str | None = None,
    ):
        self.settings = settings
        self.base_url = base_url
        self.email = email
        self.token = token
        self.project_key = project_key
        self.available = all([self.base_url, self.email, self.token])

    async def search(self, jql: str) -> str:
        if not self.available:
            return "JIRA MCP not configured. Provide a client to enable search."
        url = f"{self.base_url}/rest/api/3/search"
        params = {"jql": jql, "maxResults": 5}
        try:
            async with httpx.AsyncClient(timeout=10, auth=(self.email, self.token)) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                issues = data.get("issues", [])
                if not issues:
                    return "No issues found."
                summaries = []
                for issue in issues:
                    key = issue.get("key", "")
                    fields = issue.get("fields", {}) if isinstance(issue, dict) else {}
                    summary = fields.get("summary", "")
                    summaries.append(f"{key}: {summary}")
                return "Jira results: " + "; ".join(summaries)
        except Exception as exc:  # noqa: BLE001
            logger.error("jira_search_error", error=_format_error(exc))
            return f"Jira search failed: {_format_error(exc)}"

    async def create_issue(self, summary: str, description: str) -> str:
        if not self.available:
            return "JIRA MCP not configured. Provide a client to enable issue creation."
        if not self.project_key:
            return "JIRA project key not set. Add project_key in provider config."
        url = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Task"},
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10, auth=(self.email, self.token)) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return f"Created issue {data.get('key', 'unknown')}"
        except Exception as exc:  # noqa: BLE001
            logger.error("jira_create_error", error=_format_error(exc))
            return f"Jira create failed: {_format_error(exc)}"

    async def add_watchers(self, issue_key: str, emails: List[str]) -> str:
        if not self.available:
            return "JIRA MCP not configured. Provide a client to enable watcher updates."
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/watchers"
        try:
            async with httpx.AsyncClient(timeout=10, auth=(self.email, self.token)) as client:
                for email in emails:
                    resp = await client.post(url, json=email)
                    resp.raise_for_status()
            return f"Added {len(emails)} watchers to {issue_key}"
        except Exception as exc:  # noqa: BLE001
            logger.error("jira_watchers_add_error", error=_format_error(exc))
            return f"Jira watchers add failed: {_format_error(exc)}"

    async def remove_watcher(self, issue_key: str, email: str) -> str:
        if not self.available:
            return "JIRA MCP not configured. Provide a client to enable watcher updates."
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/watchers"
        try:
            async with httpx.AsyncClient(timeout=10, auth=(self.email, self.token)) as client:
                resp = await client.request("DELETE", url, json=email)
                resp.raise_for_status()
            return f"Removed watcher {email} from {issue_key}"
        except Exception as exc:  # noqa: BLE001
            logger.error("jira_watchers_remove_error", error=_format_error(exc))
            return f"Jira remove watcher failed: {_format_error(exc)}"


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        body = exc.response.text[:500]
        return f"HTTP {status}: {body}"
    return str(exc)
