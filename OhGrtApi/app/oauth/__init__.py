"""OAuth routers for external provider authentication."""

from app.oauth.gmail import router as gmail_router
from app.oauth.github import router as github_router
from app.oauth.slack import router as slack_router
from app.oauth.jira import router as jira_router
from app.oauth.uber import router as uber_router

__all__ = [
    "gmail_router",
    "github_router",
    "slack_router",
    "jira_router",
    "uber_router",
]
