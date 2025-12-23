from __future__ import annotations

from typing import List, Optional, Dict, Any

import httpx

from app.interfaces import GitHubSettingsProtocol
from app.logger import logger


class GitHubService:
    """
    GitHub REST API client for managing issues, PRs, and repositories.

    Supports two authentication modes:
    1. OAuth 2.0 (preferred): Uses access_token from IntegrationCredential
    2. Personal Access Token (legacy): Uses github_token from settings

    Accepts any settings object that implements GitHubSettingsProtocol,
    allowing both app-level Settings and user-specific UserToolSettings.
    """

    def __init__(
        self,
        settings: GitHubSettingsProtocol = None,
        *,
        access_token: str = None,
        owner: str = None,
    ):
        """
        Initialize GitHubService with either OAuth credentials or legacy PAT.

        OAuth mode (preferred):
            GitHubService(access_token="...", owner="...")

        Legacy PAT mode:
            GitHubService(settings=user_settings)
        """
        # OAuth mode
        self.access_token = access_token
        self.owner = owner
        self.use_oauth = bool(access_token)

        # Legacy PAT mode
        self.token = ""
        self.default_repo = ""

        if settings:
            self.token = getattr(settings, "github_token", "")
            self.default_repo = getattr(settings, "github_default_repo", "")

        # Use OAuth token or legacy PAT
        self._auth_token = self.access_token if self.use_oauth else self.token
        self.base_url = "https://api.github.com"
        self.available = bool(self._auth_token)

    def _get_headers(self) -> Dict[str, str]:
        """Create auth headers for GitHub API."""
        return {
            "Authorization": f"Bearer {self._auth_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _parse_repo(self, repo: Optional[str] = None) -> tuple[str, str]:
        """Parse owner/repo from repo string or use default."""
        repo_str = repo or self.default_repo
        if "/" not in repo_str:
            raise ValueError(f"Invalid repo format: {repo_str}. Expected 'owner/repo'")
        parts = repo_str.split("/")
        return parts[0], parts[1]

    async def list_issues(
        self,
        repo: Optional[str] = None,
        state: str = "open",
        labels: Optional[str] = None,
        max_results: int = 10,
    ) -> str:
        """List issues in a repository."""
        if not self.available:
            return "GitHub is not configured. Please add your GitHub token in Settings > Integrations."

        try:
            owner, repo_name = self._parse_repo(repo)
        except ValueError as e:
            return str(e)

        try:
            params: Dict[str, Any] = {
                "state": state,
                "per_page": max_results,
                "sort": "updated",
                "direction": "desc",
            }
            if labels:
                params["labels"] = labels

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo_name}/issues",
                    headers=self._get_headers(),
                    params=params,
                )

                if resp.status_code != 200:
                    return f"GitHub API error: {resp.status_code} - {resp.text}"

                issues = resp.json()

                if not issues:
                    return f"No {state} issues found in {owner}/{repo_name}"

                results = []
                for issue in issues:
                    # Skip pull requests (they appear in issues endpoint too)
                    if "pull_request" in issue:
                        continue

                    number = issue.get("number")
                    title = issue.get("title", "No title")
                    state_val = issue.get("state", "unknown")
                    user = issue.get("user", {}).get("login", "Unknown")
                    labels_list = [l.get("name") for l in issue.get("labels", [])]
                    labels_str = ", ".join(labels_list) if labels_list else "None"

                    results.append(
                        f"- #{number}: {title}\n"
                        f"  State: {state_val} | Author: {user} | Labels: {labels_str}"
                    )

                if not results:
                    return f"No {state} issues found in {owner}/{repo_name}"

                return f"Found {len(results)} issues in {owner}/{repo_name}:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("github_list_issues_error", error=str(exc))
            return f"GitHub error: {exc}"

    async def create_issue(
        self,
        title: str,
        body: str,
        repo: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> str:
        """Create a new issue in a repository."""
        if not self.available:
            return "GitHub is not configured. Please add your GitHub token in Settings > Integrations."

        try:
            owner, repo_name = self._parse_repo(repo)
        except ValueError as e:
            return str(e)

        try:
            issue_data: Dict[str, Any] = {
                "title": title,
                "body": body,
            }
            if labels:
                issue_data["labels"] = labels
            if assignees:
                issue_data["assignees"] = assignees

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/repos/{owner}/{repo_name}/issues",
                    headers=self._get_headers(),
                    json=issue_data,
                )

                if resp.status_code != 201:
                    return f"Failed to create issue: {resp.status_code} - {resp.text}"

                created = resp.json()
                issue_number = created.get("number")
                issue_url = created.get("html_url")

                return f"Created issue #{issue_number}: {title}\nURL: {issue_url}"

        except Exception as exc:
            logger.error("github_create_issue_error", error=str(exc))
            return f"GitHub error: {exc}"

    async def get_issue(self, issue_number: int, repo: Optional[str] = None) -> str:
        """Get details of a specific issue."""
        if not self.available:
            return "GitHub is not configured."

        try:
            owner, repo_name = self._parse_repo(repo)
        except ValueError as e:
            return str(e)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo_name}/issues/{issue_number}",
                    headers=self._get_headers(),
                )

                if resp.status_code != 200:
                    return f"Issue #{issue_number} not found."

                issue = resp.json()
                title = issue.get("title", "No title")
                body = issue.get("body", "No description")
                state = issue.get("state", "unknown")
                user = issue.get("user", {}).get("login", "Unknown")
                assignees = [a.get("login") for a in issue.get("assignees", [])]
                assignees_str = ", ".join(assignees) if assignees else "None"
                labels_list = [l.get("name") for l in issue.get("labels", [])]
                labels_str = ", ".join(labels_list) if labels_list else "None"
                created = issue.get("created_at", "")[:10]
                updated = issue.get("updated_at", "")[:10]

                return (
                    f"Issue #{issue_number}: {title}\n"
                    f"State: {state} | Author: {user}\n"
                    f"Assignees: {assignees_str} | Labels: {labels_str}\n"
                    f"Created: {created} | Updated: {updated}\n\n"
                    f"Description:\n{body[:1000]}"
                )

        except Exception as exc:
            logger.error("github_get_issue_error", error=str(exc))
            return f"GitHub error: {exc}"

    async def list_pull_requests(
        self,
        repo: Optional[str] = None,
        state: str = "open",
        max_results: int = 10,
    ) -> str:
        """List pull requests in a repository."""
        if not self.available:
            return "GitHub is not configured."

        try:
            owner, repo_name = self._parse_repo(repo)
        except ValueError as e:
            return str(e)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo_name}/pulls",
                    headers=self._get_headers(),
                    params={
                        "state": state,
                        "per_page": max_results,
                        "sort": "updated",
                        "direction": "desc",
                    },
                )

                if resp.status_code != 200:
                    return f"GitHub API error: {resp.status_code} - {resp.text}"

                prs = resp.json()

                if not prs:
                    return f"No {state} pull requests found in {owner}/{repo_name}"

                results = []
                for pr in prs:
                    number = pr.get("number")
                    title = pr.get("title", "No title")
                    state_val = pr.get("state", "unknown")
                    user = pr.get("user", {}).get("login", "Unknown")
                    draft = " [DRAFT]" if pr.get("draft") else ""

                    results.append(
                        f"- PR #{number}: {title}{draft}\n"
                        f"  State: {state_val} | Author: {user}"
                    )

                return f"Found {len(results)} PRs in {owner}/{repo_name}:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("github_list_prs_error", error=str(exc))
            return f"GitHub error: {exc}"

    async def search_issues(
        self,
        query: str,
        repo: Optional[str] = None,
        max_results: int = 10,
    ) -> str:
        """Search issues across GitHub or in a specific repository."""
        if not self.available:
            return "GitHub is not configured. Please add your GitHub token in Settings > Integrations."

        try:
            search_query = query
            if repo:
                owner, repo_name = self._parse_repo(repo)
                search_query = f"{query} repo:{owner}/{repo_name}"
            elif self.default_repo:
                owner, repo_name = self._parse_repo(self.default_repo)
                search_query = f"{query} repo:{owner}/{repo_name}"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/search/issues",
                    headers=self._get_headers(),
                    params={
                        "q": search_query,
                        "per_page": max_results,
                        "sort": "updated",
                        "order": "desc",
                    },
                )

                if resp.status_code != 200:
                    return f"GitHub search error: {resp.status_code} - {resp.text}"

                data = resp.json()
                items = data.get("items", [])

                if not items:
                    return f"No issues found for: {query}"

                results = []
                for item in items:
                    number = item.get("number")
                    title = item.get("title", "No title")
                    state = item.get("state", "unknown")
                    user = item.get("user", {}).get("login", "Unknown")
                    repo_url = item.get("repository_url", "")
                    repo_name = repo_url.split("/")[-2] + "/" + repo_url.split("/")[-1] if repo_url else "Unknown"
                    labels_list = [l.get("name") for l in item.get("labels", [])]
                    labels_str = ", ".join(labels_list) if labels_list else "None"

                    results.append(
                        f"- #{number}: {title}\n"
                        f"  Repo: {repo_name} | State: {state} | Author: {user} | Labels: {labels_str}"
                    )

                return f"Found {len(items)} issues:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("github_search_issues_error", error=str(exc))
            return f"GitHub error: {exc}"

    async def search_code(
        self,
        query: str,
        repo: Optional[str] = None,
        max_results: int = 10,
    ) -> str:
        """Search code in a repository or across GitHub."""
        if not self.available:
            return "GitHub is not configured."

        try:
            search_query = query
            if repo:
                owner, repo_name = self._parse_repo(repo)
                search_query = f"{query} repo:{owner}/{repo_name}"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/search/code",
                    headers=self._get_headers(),
                    params={
                        "q": search_query,
                        "per_page": max_results,
                    },
                )

                if resp.status_code != 200:
                    return f"GitHub search error: {resp.status_code} - {resp.text}"

                data = resp.json()
                items = data.get("items", [])

                if not items:
                    return f"No code matches found for: {query}"

                results = []
                for item in items:
                    name = item.get("name", "Unknown")
                    path = item.get("path", "")
                    repo_info = item.get("repository", {})
                    repo_full = repo_info.get("full_name", "Unknown")
                    html_url = item.get("html_url", "")

                    results.append(
                        f"- {path}\n"
                        f"  Repo: {repo_full}\n"
                        f"  URL: {html_url}"
                    )

                return f"Found {len(items)} code matches:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("github_search_code_error", error=str(exc))
            return f"GitHub error: {exc}"

    async def add_comment(
        self,
        issue_number: int,
        body: str,
        repo: Optional[str] = None,
    ) -> str:
        """Add a comment to an issue or pull request."""
        if not self.available:
            return "GitHub is not configured."

        try:
            owner, repo_name = self._parse_repo(repo)
        except ValueError as e:
            return str(e)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/repos/{owner}/{repo_name}/issues/{issue_number}/comments",
                    headers=self._get_headers(),
                    json={"body": body},
                )

                if resp.status_code != 201:
                    return f"Failed to add comment: {resp.status_code} - {resp.text}"

                comment = resp.json()
                comment_url = comment.get("html_url")

                return f"Added comment to #{issue_number}\nURL: {comment_url}"

        except Exception as exc:
            logger.error("github_add_comment_error", error=str(exc))
            return f"GitHub error: {exc}"
