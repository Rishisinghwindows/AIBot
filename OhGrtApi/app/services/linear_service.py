from __future__ import annotations

from typing import List, Optional, Dict, Any

import httpx

from app.interfaces import LinearSettingsProtocol
from app.logger import logger


class LinearService:
    """
    Linear GraphQL API client for managing issues and projects.
    Uses API key for authentication.

    Accepts any settings object that implements LinearSettingsProtocol,
    allowing both app-level Settings and user-specific UserToolSettings.
    """

    def __init__(self, settings: LinearSettingsProtocol):
        self.api_key = getattr(settings, "linear_api_key", "")
        self.base_url = "https://api.linear.app/graphql"
        self.available = bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Create auth headers for Linear API."""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    async def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                self.base_url,
                headers=self._get_headers(),
                json={"query": query, "variables": variables or {}},
            )
            return resp.json()

    async def search_issues(
        self,
        query: Optional[str] = None,
        team: Optional[str] = None,
        state: Optional[str] = None,
        max_results: int = 10,
    ) -> str:
        """Search for issues in Linear."""
        if not self.available:
            return "Linear is not configured. Please add your Linear API key in Settings > Integrations."

        try:
            # Build filter
            filter_parts = []
            if query:
                filter_parts.append(f'title: {{ containsIgnoreCase: "{query}" }}')
            if team:
                filter_parts.append(f'team: {{ name: {{ eq: "{team}" }} }}')
            if state:
                filter_parts.append(f'state: {{ name: {{ eq: "{state}" }} }}')

            filter_str = ", ".join(filter_parts) if filter_parts else ""
            filter_arg = f"filter: {{ {filter_str} }}" if filter_str else ""

            gql = f"""
            query {{
                issues(first: {max_results}, {filter_arg}) {{
                    nodes {{
                        id
                        identifier
                        title
                        state {{
                            name
                        }}
                        priority
                        assignee {{
                            name
                        }}
                        team {{
                            name
                        }}
                        createdAt
                        updatedAt
                    }}
                }}
            }}
            """

            data = await self._execute_query(gql)

            if "errors" in data:
                return f"Linear API error: {data['errors']}"

            issues = data.get("data", {}).get("issues", {}).get("nodes", [])

            if not issues:
                return "No issues found matching your criteria."

            results = []
            for issue in issues:
                identifier = issue.get("identifier", "???")
                title = issue.get("title", "No title")
                state_name = issue.get("state", {}).get("name", "Unknown")
                priority = issue.get("priority", 0)
                priority_map = {0: "None", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}
                priority_str = priority_map.get(priority, "None")
                assignee = issue.get("assignee", {})
                assignee_name = assignee.get("name", "Unassigned") if assignee else "Unassigned"
                team_name = issue.get("team", {}).get("name", "Unknown")

                results.append(
                    f"- [{identifier}] {title}\n"
                    f"  Team: {team_name} | State: {state_name} | Priority: {priority_str} | Assignee: {assignee_name}"
                )

            return f"Found {len(issues)} issues:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("linear_search_error", error=str(exc))
            return f"Linear error: {exc}"

    async def create_issue(
        self,
        title: str,
        description: str,
        team_id: Optional[str] = None,
        priority: Optional[int] = None,
        assignee_id: Optional[str] = None,
    ) -> str:
        """Create a new issue in Linear."""
        if not self.available:
            return "Linear is not configured. Please add your Linear API key in Settings > Integrations."

        try:
            # If no team_id provided, get the first team
            if not team_id:
                teams_query = """
                query {
                    teams(first: 1) {
                        nodes {
                            id
                            name
                        }
                    }
                }
                """
                teams_data = await self._execute_query(teams_query)
                teams = teams_data.get("data", {}).get("teams", {}).get("nodes", [])
                if not teams:
                    return "No teams found in your Linear workspace."
                team_id = teams[0]["id"]

            # Build input
            input_parts = [
                f'title: "{title}"',
                f'description: "{description}"',
                f'teamId: "{team_id}"',
            ]
            if priority is not None:
                input_parts.append(f"priority: {priority}")
            if assignee_id:
                input_parts.append(f'assigneeId: "{assignee_id}"')

            input_str = ", ".join(input_parts)

            gql = f"""
            mutation {{
                issueCreate(input: {{ {input_str} }}) {{
                    success
                    issue {{
                        id
                        identifier
                        title
                        url
                    }}
                }}
            }}
            """

            data = await self._execute_query(gql)

            if "errors" in data:
                return f"Linear API error: {data['errors']}"

            result = data.get("data", {}).get("issueCreate", {})
            if not result.get("success"):
                return "Failed to create issue."

            issue = result.get("issue", {})
            identifier = issue.get("identifier", "???")
            url = issue.get("url", "")

            return f"Created issue: [{identifier}] {title}\nURL: {url}"

        except Exception as exc:
            logger.error("linear_create_error", error=str(exc))
            return f"Linear error: {exc}"

    async def get_issue(self, issue_id: str) -> str:
        """Get details of a specific issue by identifier (e.g., ENG-123)."""
        if not self.available:
            return "Linear is not configured."

        try:
            gql = f"""
            query {{
                issue(id: "{issue_id}") {{
                    id
                    identifier
                    title
                    description
                    state {{
                        name
                    }}
                    priority
                    assignee {{
                        name
                    }}
                    team {{
                        name
                    }}
                    labels {{
                        nodes {{
                            name
                        }}
                    }}
                    createdAt
                    updatedAt
                    url
                }}
            }}
            """

            data = await self._execute_query(gql)

            if "errors" in data:
                # Try searching by identifier instead
                return await self._get_issue_by_identifier(issue_id)

            issue = data.get("data", {}).get("issue")
            if not issue:
                return await self._get_issue_by_identifier(issue_id)

            return self._format_issue(issue)

        except Exception as exc:
            logger.error("linear_get_error", error=str(exc))
            return f"Linear error: {exc}"

    async def _get_issue_by_identifier(self, identifier: str) -> str:
        """Search for issue by identifier (e.g., ENG-123)."""
        gql = f"""
        query {{
            issues(filter: {{ identifier: {{ eq: "{identifier}" }} }}) {{
                nodes {{
                    id
                    identifier
                    title
                    description
                    state {{
                        name
                    }}
                    priority
                    assignee {{
                        name
                    }}
                    team {{
                        name
                    }}
                    labels {{
                        nodes {{
                            name
                        }}
                    }}
                    createdAt
                    updatedAt
                    url
                }}
            }}
        }}
        """

        data = await self._execute_query(gql)

        if "errors" in data:
            return f"Linear API error: {data['errors']}"

        issues = data.get("data", {}).get("issues", {}).get("nodes", [])
        if not issues:
            return f"Issue {identifier} not found."

        return self._format_issue(issues[0])

    def _format_issue(self, issue: Dict) -> str:
        """Format issue details for display."""
        identifier = issue.get("identifier", "???")
        title = issue.get("title", "No title")
        description = issue.get("description", "No description") or "No description"
        state_name = issue.get("state", {}).get("name", "Unknown")
        priority = issue.get("priority", 0)
        priority_map = {0: "None", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}
        priority_str = priority_map.get(priority, "None")
        assignee = issue.get("assignee", {})
        assignee_name = assignee.get("name", "Unassigned") if assignee else "Unassigned"
        team_name = issue.get("team", {}).get("name", "Unknown")
        labels = [l.get("name") for l in issue.get("labels", {}).get("nodes", [])]
        labels_str = ", ".join(labels) if labels else "None"
        created = issue.get("createdAt", "")[:10]
        updated = issue.get("updatedAt", "")[:10]
        url = issue.get("url", "")

        return (
            f"Issue: [{identifier}] {title}\n"
            f"Team: {team_name} | State: {state_name} | Priority: {priority_str}\n"
            f"Assignee: {assignee_name} | Labels: {labels_str}\n"
            f"Created: {created} | Updated: {updated}\n"
            f"URL: {url}\n\n"
            f"Description:\n{description[:1000]}"
        )

    async def list_teams(self) -> str:
        """List all teams in the workspace."""
        if not self.available:
            return "Linear is not configured."

        try:
            gql = """
            query {
                teams {
                    nodes {
                        id
                        name
                        key
                        description
                    }
                }
            }
            """

            data = await self._execute_query(gql)

            if "errors" in data:
                return f"Linear API error: {data['errors']}"

            teams = data.get("data", {}).get("teams", {}).get("nodes", [])

            if not teams:
                return "No teams found."

            results = []
            for team in teams:
                name = team.get("name", "Unknown")
                key = team.get("key", "???")
                desc = team.get("description", "")
                results.append(f"- {name} ({key})" + (f": {desc}" if desc else ""))

            return f"Found {len(teams)} teams:\n\n" + "\n".join(results)

        except Exception as exc:
            logger.error("linear_list_teams_error", error=str(exc))
            return f"Linear error: {exc}"

    async def add_comment(self, issue_id: str, body: str) -> str:
        """Add a comment to an issue."""
        if not self.available:
            return "Linear is not configured."

        try:
            # First try to get the issue to get its internal ID
            gql_search = f"""
            query {{
                issues(filter: {{ identifier: {{ eq: "{issue_id}" }} }}) {{
                    nodes {{
                        id
                    }}
                }}
            }}
            """

            search_data = await self._execute_query(gql_search)
            issues = search_data.get("data", {}).get("issues", {}).get("nodes", [])

            if not issues:
                return f"Issue {issue_id} not found."

            internal_id = issues[0]["id"]

            gql = f"""
            mutation {{
                commentCreate(input: {{ issueId: "{internal_id}", body: "{body}" }}) {{
                    success
                    comment {{
                        id
                        url
                    }}
                }}
            }}
            """

            data = await self._execute_query(gql)

            if "errors" in data:
                return f"Linear API error: {data['errors']}"

            result = data.get("data", {}).get("commentCreate", {})
            if not result.get("success"):
                return "Failed to add comment."

            comment = result.get("comment", {})
            url = comment.get("url", "")

            return f"Added comment to {issue_id}\nURL: {url}"

        except Exception as exc:
            logger.error("linear_add_comment_error", error=str(exc))
            return f"Linear error: {exc}"
