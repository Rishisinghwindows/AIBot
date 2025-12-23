from __future__ import annotations

import base64
from typing import List, Optional, Dict, Any, Union

import httpx

from app.interfaces import JiraSettingsProtocol
from app.logger import logger
from app.utils.errors import ServiceError


class JiraService:
    """
    Jira REST API client for searching, creating, and managing issues.

    Supports two authentication modes:
    1. OAuth 2.0 (preferred): Uses access_token and cloud_id from IntegrationCredential
    2. Basic Auth (legacy): Uses email + API token from settings

    Accepts any settings object that implements JiraSettingsProtocol,
    allowing both app-level Settings and user-specific UserToolSettings.
    """

    def __init__(
        self,
        settings: JiraSettingsProtocol = None,
        *,
        access_token: str = None,
        cloud_id: str = None,
        site_url: str = None,
        refresh_token: str = None,
    ):
        """
        Initialize JiraService with either OAuth credentials or legacy Basic Auth.

        OAuth mode (preferred):
            JiraService(access_token="...", cloud_id="...", site_url="...")

        Legacy Basic Auth mode:
            JiraService(settings=user_settings)
        """
        # OAuth mode
        self.access_token = access_token
        self.cloud_id = cloud_id
        self.site_url = site_url
        self.refresh_token = refresh_token
        self.use_oauth = bool(access_token and cloud_id)

        # Legacy Basic Auth mode
        self.base_url = ""
        self.email = ""
        self.api_token = ""
        self.project_key = ""

        if settings:
            self.base_url = getattr(settings, "jira_base_url", "").rstrip("/")
            self.email = getattr(settings, "jira_email", "")
            self.api_token = getattr(settings, "jira_api_token", "")
            self.project_key = getattr(settings, "jira_project_key", "")

        # Determine availability
        self.available = self.use_oauth or bool(self.base_url and self.email and self.api_token)

    def _get_api_base(self) -> str:
        """Get the base URL for API calls."""
        if self.use_oauth:
            return f"https://api.atlassian.com/ex/jira/{self.cloud_id}"
        return self.base_url

    def _get_auth_header(self) -> Dict[str, str]:
        """Create auth header for Jira API."""
        if self.use_oauth:
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        # Legacy Basic Auth
        credentials = f"{self.email}:{self.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_browse_url(self, issue_key: str) -> str:
        """Get the browse URL for an issue."""
        if self.use_oauth and self.site_url:
            return f"{self.site_url}/browse/{issue_key}"
        return f"{self.base_url}/browse/{issue_key}"

    async def search(self, jql: str, max_results: int = 10) -> str:
        """Search Jira issues using JQL."""
        if not self.available:
            return "Jira is not configured. Please connect Jira in Settings > Integrations."

        try:
            api_base = self._get_api_base()
            async with httpx.AsyncClient(timeout=30) as client:
                # Use the new /search/jql endpoint (POST with JSON body)
                # The old /search endpoint was deprecated
                resp = await client.post(
                    f"{api_base}/rest/api/3/search/jql",
                    headers=self._get_auth_header(),
                    json={
                        "jql": jql,
                        "maxResults": max_results,
                        "fields": ["summary", "status", "assignee", "priority", "created", "updated", "issuetype"],
                    },
                )

                if resp.status_code != 200:
                    error_msg = resp.json().get("errorMessages", [resp.text])
                    return f"Jira search failed: {error_msg}"

                data = resp.json()
                issues = data.get("issues", [])

                if not issues:
                    return f"No issues found for JQL: {jql}"

                results = []
                for issue in issues:
                    key = issue.get("key")
                    fields = issue.get("fields", {})
                    summary = fields.get("summary", "No summary")
                    status = fields.get("status", {}).get("name", "Unknown")
                    issue_type = fields.get("issuetype", {}).get("name", "Unknown")
                    assignee = fields.get("assignee", {})
                    assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
                    priority = fields.get("priority", {})
                    priority_name = priority.get("name", "None") if priority else "None"

                    results.append(
                        f"- [{key}] {summary}\n"
                        f"  Type: {issue_type} | Status: {status} | Priority: {priority_name} | Assignee: {assignee_name}"
                    )

                return f"Found {len(issues)} issues:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("jira_search_error", error=str(exc))
            return f"Jira search error: {exc}"

    async def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        assignee_email: Optional[str] = None,
        project_key: Optional[str] = None,
    ) -> str:
        """Create a new Jira issue."""
        if not self.available:
            return "Jira is not configured. Please connect Jira in Settings > Integrations."

        # Use provided project_key or fallback to configured one
        proj_key = project_key or self.project_key
        if not proj_key:
            return "Jira project key not provided. Please specify a project key."

        try:
            api_base = self._get_api_base()
            # Build issue payload
            issue_data: Dict[str, Any] = {
                "fields": {
                    "project": {"key": proj_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}],
                            }
                        ],
                    },
                    "issuetype": {"name": issue_type},
                }
            }

            if priority:
                issue_data["fields"]["priority"] = {"name": priority}

            if assignee_email:
                # Get account ID for assignee
                account_id = await self._get_account_id(assignee_email)
                if account_id:
                    issue_data["fields"]["assignee"] = {"accountId": account_id}

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{api_base}/rest/api/3/issue",
                    headers=self._get_auth_header(),
                    json=issue_data,
                )

                if resp.status_code not in (200, 201):
                    error_data = resp.json()
                    errors = error_data.get("errors", {})
                    error_messages = error_data.get("errorMessages", [])
                    return f"Failed to create issue: {errors or error_messages}"

                created = resp.json()
                issue_key = created.get("key")
                issue_url = self._get_browse_url(issue_key)

                return f"Created issue: [{issue_key}] {summary}\nURL: {issue_url}"

        except Exception as exc:
            logger.error("jira_create_error", error=str(exc))
            return f"Jira create error: {exc}"

    async def get_issue(self, issue_key: str) -> str:
        """Get details of a specific Jira issue."""
        if not self.available:
            return "Jira is not configured. Please connect Jira in Settings > Integrations."

        try:
            api_base = self._get_api_base()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{api_base}/rest/api/3/issue/{issue_key}",
                    headers=self._get_auth_header(),
                )

                if resp.status_code != 200:
                    return f"Issue {issue_key} not found."

                data = resp.json()
                fields = data.get("fields", {})

                summary = fields.get("summary", "No summary")
                description = fields.get("description")
                desc_text = self._extract_description_text(description) if description else "No description"
                status = fields.get("status", {}).get("name", "Unknown")
                issue_type = fields.get("issuetype", {}).get("name", "Unknown")
                assignee = fields.get("assignee", {})
                assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
                reporter = fields.get("reporter", {})
                reporter_name = reporter.get("displayName", "Unknown") if reporter else "Unknown"
                priority = fields.get("priority", {})
                priority_name = priority.get("name", "None") if priority else "None"
                created = fields.get("created", "")[:10]
                updated = fields.get("updated", "")[:10]

                return (
                    f"Issue: [{issue_key}] {summary}\n"
                    f"Type: {issue_type} | Status: {status} | Priority: {priority_name}\n"
                    f"Assignee: {assignee_name} | Reporter: {reporter_name}\n"
                    f"Created: {created} | Updated: {updated}\n\n"
                    f"Description:\n{desc_text}"
                )

        except Exception as exc:
            logger.error("jira_get_error", error=str(exc))
            return f"Jira get error: {exc}"

    async def add_watchers(self, issue_key: str, emails: List[str]) -> str:
        """Add watchers to a Jira issue."""
        if not self.available:
            return "Jira is not configured. Please connect Jira in Settings > Integrations."

        api_base = self._get_api_base()
        results = []
        for email in emails:
            account_id = await self._get_account_id(email)
            if not account_id:
                results.append(f"Could not find user: {email}")
                continue

            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        f"{api_base}/rest/api/3/issue/{issue_key}/watchers",
                        headers=self._get_auth_header(),
                        json=account_id,
                    )

                    if resp.status_code in (200, 204):
                        results.append(f"Added watcher: {email}")
                    else:
                        results.append(f"Failed to add {email}: {resp.text}")

            except Exception as exc:
                results.append(f"Error adding {email}: {exc}")

        return "\n".join(results)

    async def remove_watcher(self, issue_key: str, email: str) -> str:
        """Remove a watcher from a Jira issue."""
        if not self.available:
            return "Jira is not configured. Please connect Jira in Settings > Integrations."

        account_id = await self._get_account_id(email)
        if not account_id:
            return f"Could not find user: {email}"

        try:
            api_base = self._get_api_base()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.delete(
                    f"{api_base}/rest/api/3/issue/{issue_key}/watchers",
                    headers=self._get_auth_header(),
                    params={"accountId": account_id},
                )

                if resp.status_code in (200, 204):
                    return f"Removed watcher: {email} from {issue_key}"
                else:
                    return f"Failed to remove watcher: {resp.text}"

        except Exception as exc:
            logger.error("jira_remove_watcher_error", error=str(exc))
            return f"Error removing watcher: {exc}"

    async def _get_account_id(self, email: str) -> Optional[str]:
        """Get Jira account ID by email."""
        try:
            api_base = self._get_api_base()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{api_base}/rest/api/3/user/search",
                    headers=self._get_auth_header(),
                    params={"query": email},
                )

                if resp.status_code == 200:
                    users = resp.json()
                    if users:
                        return users[0].get("accountId")
        except Exception as exc:
            logger.error("jira_user_search_error", error=str(exc))

        return None

    async def list_projects(self) -> str:
        """List all accessible Jira projects."""
        if not self.available:
            return "Jira is not configured. Please connect Jira in Settings > Integrations."

        try:
            api_base = self._get_api_base()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{api_base}/rest/api/3/project",
                    headers=self._get_auth_header(),
                )

                if resp.status_code != 200:
                    return f"Failed to list projects: {resp.text}"

                projects = resp.json()
                if not projects:
                    return "No projects found."

                results = []
                for proj in projects:
                    key = proj.get("key")
                    name = proj.get("name")
                    results.append(f"- [{key}] {name}")

                return f"Found {len(projects)} projects:\n\n" + "\n".join(results)

        except Exception as exc:
            logger.error("jira_list_projects_error", error=str(exc))
            return f"Jira list projects error: {exc}"

    def _extract_description_text(self, description: Dict) -> str:
        """Extract plain text from Jira's Atlassian Document Format."""
        if not description:
            return ""

        text_parts = []
        content = description.get("content", [])

        for block in content:
            if block.get("type") == "paragraph":
                for item in block.get("content", []):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))

        return " ".join(text_parts)
