"""Slack OAuth router."""

from __future__ import annotations

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ohgrt_api.auth.dependencies import get_current_user, get_db
from ohgrt_api.config import get_settings
from ohgrt_api.db.models import User
from ohgrt_api.logger import logger
from ohgrt_api.oauth.base import (
    delete_credential,
    generate_state,
    get_credential,
    get_or_create_credential,
)


class OAuthExchangeRequest(BaseModel):
    """Request to exchange OAuth code for tokens."""
    code: str
    state: str | None = None


router = APIRouter(prefix="/slack", tags=["slack-oauth"])

SLACK_AUTH_URL = "https://slack.com/oauth/v2/authorize"
SLACK_TOKEN_URL = "https://slack.com/api/oauth.v2.access"
SLACK_USER_INFO_URL = "https://slack.com/api/users.identity"


@router.get("/status")
async def slack_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check Slack connection status."""
    credential = get_credential(db, current_user.id, "slack")
    if credential:
        return {
            "connected": True,
            "team_name": credential.config.get("team_name"),
            "user_name": credential.config.get("user_name"),
        }
    return {"connected": False}


@router.get("/oauth-url")
async def slack_oauth_url(
    current_user: User = Depends(get_current_user),
):
    """Get Slack OAuth authorization URL."""
    settings = get_settings()

    if not settings.slack_client_id:
        raise HTTPException(
            status_code=503,
            detail="Slack OAuth not configured. Set SLACK_CLIENT_ID in environment.",
        )

    state = generate_state()

    # Slack OAuth scopes for reading messages and posting
    scopes = "channels:read,chat:write,users:read,team:read"

    params = {
        "client_id": settings.slack_client_id,
        "redirect_uri": settings.slack_redirect_uri,
        "scope": scopes,
        "user_scope": "identity.basic,identity.email",
        "state": state,
    }

    auth_url = f"{SLACK_AUTH_URL}?{urlencode(params)}"
    logger.info("slack_oauth_url_generated", user_id=str(current_user.id))

    return {"auth_url": auth_url, "state": state}


@router.post("/callback")
async def slack_callback(
    code: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle Slack OAuth callback and exchange code for tokens."""
    settings = get_settings()

    if not settings.slack_client_id or not settings.slack_client_secret:
        raise HTTPException(status_code=503, detail="Slack OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            SLACK_TOKEN_URL,
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": settings.slack_redirect_uri,
            },
        )

        if token_response.status_code != 200:
            logger.error("slack_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        data = token_response.json()

        if not data.get("ok"):
            error = data.get("error", "Unknown error")
            logger.error("slack_oauth_error", error=error)
            raise HTTPException(status_code=400, detail=f"Slack OAuth failed: {error}")

        access_token = data.get("access_token")
        team_name = data.get("team", {}).get("name")
        team_id = data.get("team", {}).get("id")

        # Get user identity if available
        authed_user = data.get("authed_user", {})
        user_id = authed_user.get("id")
        user_token = authed_user.get("access_token")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="slack",
        access_token=access_token,
        extra_config={
            "team_name": team_name,
            "team_id": team_id,
            "slack_user_id": user_id,
            "user_token": user_token,
        },
    )

    logger.info("slack_oauth_connected", user_id=str(current_user.id), team_name=team_name)

    return {"success": True, "team_name": team_name}


@router.post("/exchange")
async def slack_exchange(
    request: OAuthExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange OAuth code for Slack access tokens (called by frontend callback page)."""
    settings = get_settings()

    if not settings.slack_client_id or not settings.slack_client_secret:
        raise HTTPException(status_code=503, detail="Slack OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            SLACK_TOKEN_URL,
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": request.code,
                "redirect_uri": settings.slack_redirect_uri,
            },
        )

        if token_response.status_code != 200:
            logger.error("slack_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        data = token_response.json()

        if not data.get("ok"):
            error = data.get("error", "Unknown error")
            logger.error("slack_oauth_error", error=error)
            raise HTTPException(status_code=400, detail=f"Slack OAuth failed: {error}")

        access_token = data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received from Slack")

        team_name = data.get("team", {}).get("name")
        team_id = data.get("team", {}).get("id")

        # Get user identity if available
        authed_user = data.get("authed_user", {})
        user_id = authed_user.get("id")
        user_token = authed_user.get("access_token")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="slack",
        access_token=access_token,
        extra_config={
            "team_name": team_name,
            "team_id": team_id,
            "slack_user_id": user_id,
            "user_token": user_token,
        },
    )

    logger.info("slack_oauth_exchanged", user_id=str(current_user.id), team_name=team_name)

    return {"success": True, "team_name": team_name, "connected": True}


@router.delete("/disconnect")
async def slack_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Slack integration."""
    deleted = delete_credential(db, current_user.id, "slack")
    if deleted:
        return {"success": True, "message": "Slack disconnected"}
    raise HTTPException(status_code=404, detail="Slack not connected")
