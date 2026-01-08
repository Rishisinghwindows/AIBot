"""Jira (Atlassian) OAuth router."""

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


router = APIRouter(prefix="/jira", tags=["jira-oauth"])

# Atlassian OAuth 2.0 (3LO)
ATLASSIAN_AUTH_URL = "https://auth.atlassian.com/authorize"
ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
ATLASSIAN_ME_URL = "https://api.atlassian.com/me"


@router.get("/status")
async def jira_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check Jira connection status."""
    credential = get_credential(db, current_user.id, "jira")
    if credential:
        return {
            "connected": True,
            "site_url": credential.config.get("site_url"),
            "site_name": credential.config.get("site_name"),
        }
    return {"connected": False}


@router.get("/oauth-url")
async def jira_oauth_url(
    current_user: User = Depends(get_current_user),
):
    """Get Jira OAuth authorization URL."""
    settings = get_settings()

    if not settings.atlassian_client_id:
        raise HTTPException(
            status_code=503,
            detail="Jira OAuth not configured. Set ATLASSIAN_CLIENT_ID in environment.",
        )

    state = generate_state()

    # Atlassian OAuth scopes for Jira
    scopes = "read:jira-work read:jira-user write:jira-work offline_access"

    params = {
        "audience": "api.atlassian.com",
        "client_id": settings.atlassian_client_id,
        "scope": scopes,
        "redirect_uri": settings.atlassian_redirect_uri,
        "state": state,
        "response_type": "code",
        "prompt": "consent",
    }

    auth_url = f"{ATLASSIAN_AUTH_URL}?{urlencode(params)}"
    logger.info("jira_oauth_url_generated", user_id=str(current_user.id))

    return {"auth_url": auth_url, "state": state}


@router.post("/callback")
async def jira_callback(
    code: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle Jira OAuth callback and exchange code for tokens."""
    settings = get_settings()

    if not settings.atlassian_client_id or not settings.atlassian_client_secret:
        raise HTTPException(status_code=503, detail="Jira OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            ATLASSIAN_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": settings.atlassian_client_id,
                "client_secret": settings.atlassian_client_secret,
                "code": code,
                "redirect_uri": settings.atlassian_redirect_uri,
            },
            headers={"Content-Type": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error("jira_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        # Get accessible resources (Jira sites)
        resources_response = await client.get(
            ATLASSIAN_RESOURCES_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        site_url = None
        site_name = None
        cloud_id = None

        if resources_response.status_code == 200:
            resources = resources_response.json()
            if resources:
                # Use the first accessible site
                site = resources[0]
                site_url = site.get("url")
                site_name = site.get("name")
                cloud_id = site.get("id")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="jira",
        access_token=access_token,
        refresh_token=refresh_token,
        extra_config={
            "site_url": site_url,
            "site_name": site_name,
            "cloud_id": cloud_id,
        },
    )

    logger.info("jira_oauth_connected", user_id=str(current_user.id), site_name=site_name)

    return {"success": True, "site_url": site_url, "site_name": site_name}


@router.post("/exchange")
async def jira_exchange(
    request: OAuthExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange OAuth code for Jira access tokens (called by frontend callback page)."""
    settings = get_settings()

    if not settings.atlassian_client_id or not settings.atlassian_client_secret:
        raise HTTPException(status_code=503, detail="Jira OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            ATLASSIAN_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": settings.atlassian_client_id,
                "client_secret": settings.atlassian_client_secret,
                "code": request.code,
                "redirect_uri": settings.atlassian_redirect_uri,
            },
            headers={"Content-Type": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error("jira_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received from Atlassian")

        # Get accessible resources (Jira sites)
        resources_response = await client.get(
            ATLASSIAN_RESOURCES_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        site_url = None
        site_name = None
        cloud_id = None

        if resources_response.status_code == 200:
            resources = resources_response.json()
            if resources:
                # Use the first accessible site
                site = resources[0]
                site_url = site.get("url")
                site_name = site.get("name")
                cloud_id = site.get("id")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="jira",
        access_token=access_token,
        refresh_token=refresh_token,
        extra_config={
            "site_url": site_url,
            "site_name": site_name,
            "cloud_id": cloud_id,
        },
    )

    logger.info("jira_oauth_exchanged", user_id=str(current_user.id), site_name=site_name)

    return {"success": True, "site_url": site_url, "site_name": site_name, "connected": True}


@router.delete("/disconnect")
async def jira_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Jira integration."""
    deleted = delete_credential(db, current_user.id, "jira")
    if deleted:
        return {"success": True, "message": "Jira disconnected"}
    raise HTTPException(status_code=404, detail="Jira not connected")
