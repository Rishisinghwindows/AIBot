from __future__ import annotations

from typing import Optional, List

import httpx

from app.logger import logger


class GitHubService:
    """
    GitHub client for repository operations.

    Supports:
      - Issues: search, create
      - Commits: list recent, view details
      - Pull Requests: list, view details
      - Repository: info, branches, contributors

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

    # =========================================================================
    # COMMITS API
    # =========================================================================

    async def list_commits(self, limit: int = 10, branch: str = "") -> str:
        """List recent commits in the repository."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        url = f"{self._base}/commits"
        params = {"per_page": min(limit, 30)}
        if branch:
            params["sha"] = branch

        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                commits = resp.json()

                if not commits:
                    return "No commits found."

                parts = []
                for commit in commits:
                    sha = commit.get("sha", "")[:7]
                    message = commit.get("commit", {}).get("message", "").split("\n")[0][:60]
                    author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
                    date = commit.get("commit", {}).get("author", {}).get("date", "")[:10]
                    parts.append(f"• {sha} - {message} ({author}, {date})")

                return f"Recent commits in {self.owner}/{self.repo}:\n" + "\n".join(parts)
        except Exception as exc:
            logger.error("github_commits_error", error=_format_error(exc))
            return f"GitHub commits failed: {_format_error(exc)}"

    async def get_commit(self, sha: str) -> str:
        """Get details of a specific commit."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        url = f"{self._base}/commits/{sha}"
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                commit = resp.json()

                sha_short = commit.get("sha", "")[:7]
                message = commit.get("commit", {}).get("message", "")
                author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
                date = commit.get("commit", {}).get("author", {}).get("date", "")
                stats = commit.get("stats", {})
                files = commit.get("files", [])

                result = f"Commit {sha_short}\n"
                result += f"Author: {author}\n"
                result += f"Date: {date}\n"
                result += f"Message: {message}\n"
                result += f"Stats: +{stats.get('additions', 0)} -{stats.get('deletions', 0)} in {len(files)} files"

                return result
        except Exception as exc:
            logger.error("github_commit_error", error=_format_error(exc))
            return f"GitHub commit failed: {_format_error(exc)}"

    # =========================================================================
    # PULL REQUESTS API
    # =========================================================================

    async def list_pull_requests(self, state: str = "open", limit: int = 10) -> str:
        """List pull requests in the repository."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        url = f"{self._base}/pulls"
        params = {"state": state, "per_page": min(limit, 30)}

        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                prs = resp.json()

                if not prs:
                    return f"No {state} pull requests found."

                parts = []
                for pr in prs:
                    number = pr.get("number")
                    title = pr.get("title", "")[:50]
                    state_pr = pr.get("state", "")
                    user = pr.get("user", {}).get("login", "Unknown")
                    parts.append(f"• #{number} [{state_pr}] {title} (by {user})")

                return f"Pull requests ({state}) in {self.owner}/{self.repo}:\n" + "\n".join(parts)
        except Exception as exc:
            logger.error("github_prs_error", error=_format_error(exc))
            return f"GitHub PRs failed: {_format_error(exc)}"

    async def get_pull_request(self, pr_number: int) -> str:
        """Get details of a specific pull request."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        url = f"{self._base}/pulls/{pr_number}"
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                pr = resp.json()

                result = f"PR #{pr.get('number')} - {pr.get('title')}\n"
                result += f"State: {pr.get('state')} | Mergeable: {pr.get('mergeable', 'unknown')}\n"
                result += f"Author: {pr.get('user', {}).get('login', 'Unknown')}\n"
                result += f"Branch: {pr.get('head', {}).get('ref', '')} → {pr.get('base', {}).get('ref', '')}\n"
                result += f"Changes: +{pr.get('additions', 0)} -{pr.get('deletions', 0)} in {pr.get('changed_files', 0)} files\n"
                result += f"Description: {(pr.get('body') or 'No description')[:200]}"

                return result
        except Exception as exc:
            logger.error("github_pr_error", error=_format_error(exc))
            return f"GitHub PR failed: {_format_error(exc)}"

    # =========================================================================
    # REPOSITORY INFO API
    # =========================================================================

    async def get_repo_info(self) -> str:
        """Get repository information."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(self._base)
                resp.raise_for_status()
                repo = resp.json()

                result = f"Repository: {repo.get('full_name')}\n"
                result += f"Description: {repo.get('description') or 'No description'}\n"
                result += f"Language: {repo.get('language', 'Unknown')}\n"
                result += f"Stars: {repo.get('stargazers_count', 0)} | Forks: {repo.get('forks_count', 0)}\n"
                result += f"Open Issues: {repo.get('open_issues_count', 0)}\n"
                result += f"Default Branch: {repo.get('default_branch', 'main')}\n"
                result += f"Created: {repo.get('created_at', '')[:10]} | Updated: {repo.get('updated_at', '')[:10]}"

                return result
        except Exception as exc:
            logger.error("github_repo_error", error=_format_error(exc))
            return f"GitHub repo info failed: {_format_error(exc)}"

    async def list_branches(self, limit: int = 10) -> str:
        """List branches in the repository."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        url = f"{self._base}/branches"
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url, params={"per_page": min(limit, 30)})
                resp.raise_for_status()
                branches = resp.json()

                if not branches:
                    return "No branches found."

                parts = []
                for branch in branches:
                    name = branch.get("name", "")
                    protected = "🔒" if branch.get("protected") else ""
                    parts.append(f"• {name} {protected}")

                return f"Branches in {self.owner}/{self.repo}:\n" + "\n".join(parts)
        except Exception as exc:
            logger.error("github_branches_error", error=_format_error(exc))
            return f"GitHub branches failed: {_format_error(exc)}"

    async def list_contributors(self, limit: int = 10) -> str:
        """List top contributors to the repository."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        url = f"{self._base}/contributors"
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url, params={"per_page": min(limit, 30)})
                resp.raise_for_status()
                contributors = resp.json()

                if not contributors:
                    return "No contributors found."

                parts = []
                for i, contrib in enumerate(contributors, 1):
                    login = contrib.get("login", "Unknown")
                    contributions = contrib.get("contributions", 0)
                    parts.append(f"{i}. {login} ({contributions} commits)")

                return f"Top contributors to {self.owner}/{self.repo}:\n" + "\n".join(parts)
        except Exception as exc:
            logger.error("github_contributors_error", error=_format_error(exc))
            return f"GitHub contributors failed: {_format_error(exc)}"

    async def get_file_content(self, path: str, branch: str = "") -> str:
        """Get content of a file from the repository."""
        if not self.available:
            return "GitHub not configured. Provide token, owner, and repo."

        url = f"{self._base}/contents/{path}"
        params = {}
        if branch:
            params["ref"] = branch

        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                if data.get("type") == "dir":
                    # It's a directory, list contents
                    items = [f"• {item.get('name')} ({item.get('type')})" for item in data] if isinstance(data, list) else []
                    return f"Directory {path}:\n" + "\n".join(items) if items else "Empty directory"

                # It's a file
                import base64
                content = data.get("content", "")
                if content:
                    try:
                        decoded = base64.b64decode(content).decode("utf-8")
                        # Limit output
                        if len(decoded) > 2000:
                            decoded = decoded[:2000] + "\n... (truncated)"
                        return f"File: {path}\n\n{decoded}"
                    except Exception:
                        return f"File {path} exists but couldn't decode content (binary file?)"

                return f"File {path} exists but has no content"
        except Exception as exc:
            logger.error("github_file_error", error=_format_error(exc))
            return f"GitHub file failed: {_format_error(exc)}"


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        body = exc.response.text[:500]
        return f"HTTP {status}: {body}"
    return str(exc)
