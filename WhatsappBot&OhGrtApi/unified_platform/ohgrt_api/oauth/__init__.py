"""OAuth routers for external provider authentication."""

from ohgrt_api.oauth.gmail import router as gmail_router
from ohgrt_api.oauth.github import router as github_router
from ohgrt_api.oauth.slack import router as slack_router
from ohgrt_api.oauth.jira import router as jira_router
from ohgrt_api.oauth.uber import router as uber_router

__all__ = [
    "gmail_router",
    "github_router",
    "slack_router",
    "jira_router",
    "uber_router",
]
