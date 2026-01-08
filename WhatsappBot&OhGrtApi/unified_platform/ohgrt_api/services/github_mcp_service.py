"""
GitHub MCP Service

Provides GitHub functionality using the official MCP server.
Manages per-user connections with OAuth tokens.
"""

from __future__ import annotations

import shutil
from typing import Any, Dict, List, Optional

from ohgrt_api.logger import logger
from ohgrt_api.mcp.stdio_client import StdioMCPClient
from ohgrt_api.mcp.types import MCPTool


class GitHubMCPService:
    """
    GitHub integration using the official MCP server.

    Uses @modelcontextprotocol/server-github via stdio transport.
    Each instance is created with a user's OAuth token.

    Available tools from GitHub MCP:
    - search_repositories: Search for repositories
    - create_repository: Create a new repository
    - get_file_contents: Get contents of a file
    - create_or_update_file: Create or update a file
    - push_files: Push multiple files in one commit
    - create_issue: Create an issue
    - create_pull_request: Create a pull request
    - fork_repository: Fork a repository
    - create_branch: Create a new branch
    - list_commits: List commits in a repository
    - list_issues: List issues in a repository
    - update_issue: Update an existing issue
    - add_issue_comment: Add a comment to an issue
    - search_code: Search for code
    - search_issues: Search for issues
    - search_users: Search for users
    - get_issue: Get a specific issue
    - get_pull_request: Get a specific pull request
    - list_pull_requests: List pull requests
    - create_pull_request_review: Create a pull request review
    - merge_pull_request: Merge a pull request
    - get_pull_request_files: Get files changed in a PR
    - get_pull_request_status: Get PR status/checks
    - update_pull_request_branch: Update PR branch
    - get_pull_request_comments: Get PR comments
    - get_pull_request_reviews: Get PR reviews
    - watch_repository: Watch/unwatch a repository
    - list_branches: List branches in a repository
    - list_tags: List tags in a repository
    """

    # Path to the GitHub MCP server binary
    MCP_SERVER_COMMAND = "mcp-server-github"

    def __init__(self, token: Optional[str] = None) -> None:
        """
        Initialize GitHub MCP service.

        Args:
            token: GitHub OAuth access token
        """
        self.token = token or ""
        self._client: Optional[StdioMCPClient] = None
        self._tools: Optional[List[MCPTool]] = None

    @property
    def available(self) -> bool:
        """Check if GitHub MCP is available."""
        # Check if token exists and server binary is installed
        if not self.token:
            return False
        return shutil.which(self.MCP_SERVER_COMMAND) is not None

    async def _get_client(self) -> StdioMCPClient:
        """Get or create the MCP client."""
        if self._client is None:
            self._client = StdioMCPClient(
                command=self.MCP_SERVER_COMMAND,
                env={"GITHUB_PERSONAL_ACCESS_TOKEN": self.token},
                timeout=30.0,
            )
            await self._client.connect()
        return self._client

    async def close(self) -> None:
        """Close the MCP client connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def list_tools(self) -> List[MCPTool]:
        """List available GitHub tools."""
        if not self.available:
            return []

        if self._tools is not None:
            return self._tools

        try:
            client = await self._get_client()
            self._tools = await client.list_tools()
            return self._tools
        except Exception as e:
            logger.error("github_mcp_list_tools_failed", error=str(e))
            return []

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Call a GitHub MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Text result from the tool
        """
        if not self.available:
            return "GitHub not connected. Please connect GitHub from Settings first."

        try:
            client = await self._get_client()
            result = await client.call_tool(tool_name, arguments)

            if result.isError:
                error_text = " ".join(
                    c.text for c in result.content if hasattr(c, "text")
                )
                return f"GitHub error: {error_text}"

            # Extract text from result
            texts = []
            for content in result.content:
                if hasattr(content, "text"):
                    texts.append(content.text)
            raw_result = "\n".join(texts) if texts else "Operation completed."

            # Try to format JSON responses nicely
            return self._format_response(tool_name, raw_result)

        except Exception as e:
            logger.error("github_mcp_call_failed", tool=tool_name, error=str(e))
            return f"GitHub MCP error: {str(e)}"

    def _format_response(self, tool_name: str, raw_result: str) -> str:
        """Format raw JSON responses into human-readable text."""
        import json

        try:
            data = json.loads(raw_result)
        except json.JSONDecodeError:
            return raw_result  # Not JSON, return as-is

        # Format based on tool type
        if tool_name == "search_repositories" and "items" in data:
            return self._format_repos(data)
        elif tool_name == "list_commits" and isinstance(data, list):
            return self._format_commits(data)
        elif tool_name == "list_issues" and isinstance(data, list):
            return self._format_issues(data)
        elif tool_name == "list_pull_requests" and isinstance(data, list):
            return self._format_prs(data)
        elif tool_name == "list_branches" and isinstance(data, list):
            return self._format_branches(data)

        # Default: return raw for other types
        return raw_result

    def _format_repos(self, data: Dict[str, Any]) -> str:
        """Format repository search results."""
        items = data.get("items", [])
        total = data.get("total_count", len(items))

        if not items:
            return "No repositories found."

        lines = [f"**Your GitHub Repositories** ({total} total):\n"]
        for repo in items:
            name = repo.get("full_name", repo.get("name", "Unknown"))
            desc = repo.get("description") or "No description"
            private = "🔒 Private" if repo.get("private") else "📂 Public"
            stars = repo.get("stargazers_count", 0)
            lang = repo.get("language") or "N/A"
            url = repo.get("html_url", "")

            lines.append(f"• **{name}** ({private})")
            lines.append(f"  {desc[:80]}{'...' if len(desc) > 80 else ''}")
            lines.append(f"  ⭐ {stars} | 💻 {lang} | [View]({url})")
            lines.append("")

        return "\n".join(lines)

    def _format_commits(self, commits: List[Dict[str, Any]]) -> str:
        """Format commit list."""
        if not commits:
            return "No commits found."

        lines = ["**Recent Commits**:\n"]
        for commit in commits[:10]:
            sha = commit.get("sha", "")[:7]
            msg = commit.get("commit", {}).get("message", "").split("\n")[0][:60]
            author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
            date = commit.get("commit", {}).get("author", {}).get("date", "")[:10]
            lines.append(f"• `{sha}` {msg}")
            lines.append(f"  by {author} on {date}")
            lines.append("")

        return "\n".join(lines)

    def _format_issues(self, issues: List[Dict[str, Any]]) -> str:
        """Format issues list."""
        if not issues:
            return "No issues found."

        lines = ["**Issues**:\n"]
        for issue in issues[:10]:
            number = issue.get("number")
            title = issue.get("title", "")[:50]
            state = "🟢" if issue.get("state") == "open" else "🔴"
            user = issue.get("user", {}).get("login", "Unknown")
            lines.append(f"• {state} #{number}: {title}")
            lines.append(f"  by {user}")
            lines.append("")

        return "\n".join(lines)

    def _format_prs(self, prs: List[Dict[str, Any]]) -> str:
        """Format pull requests list with clickable links."""
        if not prs:
            return "No pull requests found."

        # Separate open and closed/merged PRs
        open_prs = [pr for pr in prs if pr.get("state") == "open"]
        other_prs = [pr for pr in prs if pr.get("state") != "open"]

        lines = []

        if open_prs:
            lines.append(f"**Open Pull Requests** ({len(open_prs)}):\n")
            for pr in open_prs[:10]:
                number = pr.get("number")
                title = pr.get("title", "")[:60]
                user = pr.get("user", {}).get("login", "Unknown")
                url = pr.get("html_url", "")
                created = pr.get("created_at", "")[:10]
                draft = "📝 Draft" if pr.get("draft") else ""

                lines.append(f"• 🟢 **#{number}**: {title} {draft}")
                lines.append(f"  by {user} on {created}")
                if url:
                    lines.append(f"  🔗 [View PR]({url})")
                lines.append("")

        if other_prs:
            lines.append(f"**Closed/Merged Pull Requests** ({len(other_prs)}):\n")
            for pr in other_prs[:5]:
                number = pr.get("number")
                title = pr.get("title", "")[:60]
                user = pr.get("user", {}).get("login", "Unknown")
                url = pr.get("html_url", "")
                merged = "✅ Merged" if pr.get("merged_at") else "❌ Closed"

                lines.append(f"• {merged} **#{number}**: {title}")
                lines.append(f"  by {user}")
                if url:
                    lines.append(f"  🔗 [View PR]({url})")
                lines.append("")

        return "\n".join(lines) if lines else "No pull requests found."

    def _format_branches(self, branches: List[Dict[str, Any]]) -> str:
        """Format branches list."""
        if not branches:
            return "No branches found."

        lines = ["**Branches**:\n"]
        for branch in branches:
            name = branch.get("name", "Unknown")
            protected = "🔒" if branch.get("protected") else ""
            lines.append(f"• {name} {protected}")

        return "\n".join(lines)

    # =========================================================================
    # Convenience methods that wrap common MCP tools
    # =========================================================================

    async def list_repos(self, limit: int = 20) -> str:
        """List user's repositories."""
        # GitHub MCP uses search_repositories
        return await self.call_tool("search_repositories", {
            "query": "user:@me",
            "page": 1,
            "perPage": limit,
        })

    async def search_repos(self, query: str) -> str:
        """Search for repositories."""
        return await self.call_tool("search_repositories", {
            "query": query,
            "page": 1,
            "perPage": 10,
        })

    async def get_repo_info(self, owner: str, repo: str) -> str:
        """Get repository information."""
        return await self.call_tool("get_file_contents", {
            "owner": owner,
            "repo": repo,
            "path": "",
        })

    async def list_commits(self, owner: str, repo: str, limit: int = 10) -> str:
        """List recent commits."""
        return await self.call_tool("list_commits", {
            "owner": owner,
            "repo": repo,
            "perPage": limit,
        })

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> str:
        """List issues in a repository."""
        return await self.call_tool("list_issues", {
            "owner": owner,
            "repo": repo,
            "state": state,
        })

    async def create_issue(self, owner: str, repo: str, title: str, body: str) -> str:
        """Create an issue."""
        return await self.call_tool("create_issue", {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body,
        })

    async def list_pull_requests(
        self, owner: str, repo: str, state: str = "open"
    ) -> str:
        """List pull requests."""
        return await self.call_tool("list_pull_requests", {
            "owner": owner,
            "repo": repo,
            "state": state,
        })

    async def get_file_contents(
        self, owner: str, repo: str, path: str, branch: str = ""
    ) -> str:
        """Get file contents."""
        args = {
            "owner": owner,
            "repo": repo,
            "path": path,
        }
        if branch:
            args["branch"] = branch
        return await self.call_tool("get_file_contents", args)

    async def list_branches(self, owner: str, repo: str) -> str:
        """List branches in a repository."""
        return await self.call_tool("list_branches", {
            "owner": owner,
            "repo": repo,
        })

    async def search_code(self, query: str) -> str:
        """Search for code."""
        return await self.call_tool("search_code", {
            "q": query,
        })

    async def search_issues(self, query: str) -> str:
        """Search for issues."""
        return await self.call_tool("search_issues", {
            "q": query,
        })

    async def fork_repository(self, owner: str, repo: str) -> str:
        """Fork a repository."""
        return await self.call_tool("fork_repository", {
            "owner": owner,
            "repo": repo,
        })

    async def create_branch(
        self, owner: str, repo: str, branch: str, from_branch: str = "main"
    ) -> str:
        """Create a new branch."""
        return await self.call_tool("create_branch", {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "from_branch": from_branch,
        })

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
    ) -> str:
        """Create a pull request."""
        return await self.call_tool("create_pull_request", {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        })

    async def search_my_open_prs(self) -> str:
        """Search for user's open pull requests across all repos."""
        # GitHub search syntax: is:pr is:open author:@me
        result = await self.call_tool("search_issues", {
            "q": "is:pr is:open author:@me",
        })
        return self._format_search_prs(result)

    async def get_priority_issues(
        self,
        owner: str,
        repo: str,
        priority: str = "P0",
        state: str = "open",
        limit: int = 20,
    ) -> str:
        """
        Get issues by priority level (P0, P1, P2, etc.) using GitHub search.

        Common priority labels:
        - P0 / critical / urgent / high-priority
        - P1 / high / important
        - P2 / medium / normal
        - P3 / low

        Args:
            owner: Repository owner
            repo: Repository name
            priority: Priority level (P0, P1, P2, P3, critical, high, medium, low)
            state: Issue state - "open", "closed", or "all"
            limit: Max number of issues to return

        Returns:
            Formatted string with matching priority issues
        """
        # Map common priority names to possible label variations
        priority_label_map = {
            "P0": ["P0", "p0", "priority:P0", "priority/P0", "critical", "urgent", "high-priority", "severity/critical"],
            "P1": ["P1", "p1", "priority:P1", "priority/P1", "high", "important", "severity/high"],
            "P2": ["P2", "p2", "priority:P2", "priority/P2", "medium", "normal", "severity/medium"],
            "P3": ["P3", "p3", "priority:P3", "priority/P3", "low", "minor", "severity/low"],
            "critical": ["critical", "P0", "urgent", "severity/critical"],
            "high": ["high", "P1", "important", "severity/high"],
            "medium": ["medium", "P2", "normal", "severity/medium"],
            "low": ["low", "P3", "minor", "severity/low"],
        }

        # Get the list of possible labels for this priority
        priority_upper = priority.upper()
        priority_lower = priority.lower()
        labels_to_try = priority_label_map.get(priority_upper) or priority_label_map.get(priority_lower) or [priority]

        # Build search query with label OR conditions
        # GitHub search: repo:owner/repo is:issue is:open label:P0 OR label:critical
        label_query = " ".join([f"label:{label}" for label in labels_to_try[:3]])  # Limit to avoid too long query
        state_filter = f"is:{state}" if state != "all" else ""
        q = f"repo:{owner}/{repo} is:issue {state_filter} {label_query}".strip()

        result = await self.call_tool("search_issues", {"q": q})
        return self._format_priority_issues(result, priority, owner, repo)

    def _format_search_prs(self, raw_result: str) -> str:
        """Format PR search results with clickable links."""
        import json

        try:
            data = json.loads(raw_result)
        except json.JSONDecodeError:
            return raw_result

        items = data.get("items", [])
        total = data.get("total_count", len(items))

        if not items:
            return "You have no open pull requests."

        lines = [f"**Your Open Pull Requests** ({total} total):\n"]

        for pr in items[:15]:
            number = pr.get("number")
            title = pr.get("title", "")[:60]
            repo_url = pr.get("repository_url", "")
            repo_name = repo_url.split("/")[-2] + "/" + repo_url.split("/")[-1] if repo_url else "Unknown"
            url = pr.get("html_url", "")
            created = pr.get("created_at", "")[:10]
            user = pr.get("user", {}).get("login", "Unknown")
            draft = "📝 Draft " if pr.get("draft") else ""

            lines.append(f"• 🟢 **#{number}**: {title} {draft}")
            lines.append(f"  📁 {repo_name} | by {user} on {created}")
            if url:
                lines.append(f"  🔗 [View PR]({url})")
            lines.append("")

        return "\n".join(lines)

    def _format_priority_issues(self, raw_result: str, priority: str, owner: str, repo: str) -> str:
        """Format priority issues search results."""
        import json

        try:
            data = json.loads(raw_result)
        except json.JSONDecodeError:
            return raw_result

        items = data.get("items", [])
        total = data.get("total_count", len(items))

        if not items:
            return f"No {priority} issues found in {owner}/{repo}."

        lines = [f"**{priority.upper()} Issues in {owner}/{repo}** ({total} found):\n"]

        for issue in items[:15]:
            number = issue.get("number")
            title = issue.get("title", "")[:60]
            state = "🟢" if issue.get("state") == "open" else "🔴"
            user = issue.get("user", {}).get("login", "Unknown")
            assignee = issue.get("assignee", {})
            assignee_name = assignee.get("login", "Unassigned") if assignee else "Unassigned"
            labels = [l.get("name") for l in issue.get("labels", [])]
            label_str = ", ".join(labels[:3])
            url = issue.get("html_url", "")
            created = issue.get("created_at", "")[:10]

            lines.append(f"• {state} **#{number}**: {title}")
            lines.append(f"  Labels: {label_str} | Assignee: {assignee_name}")
            lines.append(f"  Created: {created} by {user}")
            if url:
                lines.append(f"  🔗 [View Issue]({url})")
            lines.append("")

        return "\n".join(lines)
