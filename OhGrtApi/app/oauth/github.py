"""GitHub OAuth router."""

from __future__ import annotations

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_db
from app.config import get_settings
from app.db.models import User
from app.logger import logger
from app.oauth.base import (
    delete_credential,
    generate_state,
    get_credential,
    get_or_create_credential,
)


class OAuthExchangeRequest(BaseModel):
    """Request to exchange OAuth code for tokens."""
    code: str
    state: str | None = None


router = APIRouter(prefix="/github", tags=["github-oauth"])

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/status")
async def github_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check GitHub connection status."""
    credential = get_credential(db, current_user.id, "github")
    if credential:
        return {
            "connected": True,
            "username": credential.config.get("username"),
            "name": credential.config.get("name"),
        }
    return {"connected": False}


@router.get("/oauth-url")
async def github_oauth_url(
    current_user: User = Depends(get_current_user),
):
    """Get GitHub OAuth authorization URL."""
    settings = get_settings()

    if not settings.github_client_id:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID in environment.",
        )

    state = generate_state()

    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "user repo read:org",
        "state": state,
    }

    auth_url = f"{GITHUB_AUTH_URL}?{urlencode(params)}"
    logger.info("github_oauth_url_generated", user_id=str(current_user.id))

    return {"auth_url": auth_url, "state": state}


@router.post("/callback")
async def github_callback(
    code: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle GitHub OAuth callback and exchange code for tokens."""
    settings = get_settings()

    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error("github_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        if not access_token:
            error = tokens.get("error_description", tokens.get("error", "Unknown error"))
            logger.error("github_token_missing", error=error)
            raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {error}")

        # Get user info
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        username = None
        name = None
        if user_response.status_code == 200:
            user_data = user_response.json()
            username = user_data.get("login")
            name = user_data.get("name")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="github",
        access_token=access_token,
        scope="user repo read:org",
        extra_config={"username": username, "name": name},
    )

    logger.info("github_oauth_connected", user_id=str(current_user.id), username=username)

    return {"success": True, "username": username, "name": name}


@router.post("/exchange")
async def github_exchange(
    request: OAuthExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange OAuth code for GitHub access tokens (called by frontend callback page)."""
    settings = get_settings()

    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": request.code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            logger.error("github_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        if not access_token:
            error = tokens.get("error_description", tokens.get("error", "Unknown error"))
            logger.error("github_token_missing", error=error)
            raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {error}")

        # Get user info
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )

        username = None
        name = None
        if user_response.status_code == 200:
            user_data = user_response.json()
            username = user_data.get("login")
            name = user_data.get("name")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="github",
        access_token=access_token,
        scope="user repo read:org",
        extra_config={"username": username, "name": name},
    )

    logger.info("github_oauth_exchanged", user_id=str(current_user.id), username=username)

    return {"success": True, "username": username, "name": name, "connected": True}


@router.delete("/disconnect")
async def github_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect GitHub integration."""
    deleted = delete_credential(db, current_user.id, "github")
    if deleted:
        return {"success": True, "message": "GitHub disconnected"}
    raise HTTPException(status_code=404, detail="GitHub not connected")
