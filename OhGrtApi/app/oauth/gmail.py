"""Gmail OAuth router."""

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

router = APIRouter(prefix="/gmail", tags=["gmail-oauth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/status")
async def gmail_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check Gmail connection status."""
    credential = get_credential(db, current_user.id, "gmail")
    if credential:
        return {
            "connected": True,
            "email": credential.config.get("email"),
            "scope": credential.config.get("scope"),
        }
    return {"connected": False}


@router.get("/oauth-url")
async def gmail_oauth_url(
    current_user: User = Depends(get_current_user),
):
    """Get Gmail OAuth authorization URL."""
    settings = get_settings()

    if not settings.google_oauth_client_id:
        raise HTTPException(
            status_code=503,
            detail="Gmail OAuth not configured. Set GOOGLE_OAUTH_CLIENT_ID in environment.",
        )

    state = generate_state()

    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": f"openid email profile {settings.google_gmail_scopes}",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    logger.info("gmail_oauth_url_generated", user_id=str(current_user.id))

    return {"auth_url": auth_url, "state": state}


@router.post("/callback")
async def gmail_callback(
    code: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle Gmail OAuth callback and exchange code for tokens."""
    settings = get_settings()

    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=503, detail="Gmail OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_oauth_redirect_uri,
            },
        )

        if token_response.status_code != 200:
            logger.error("gmail_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        # Get user info
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        email = None
        if userinfo_response.status_code == 200:
            userinfo = userinfo_response.json()
            email = userinfo.get("email")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="gmail",
        access_token=access_token,
        refresh_token=refresh_token,
        scope=settings.google_gmail_scopes,
        extra_config={"email": email},
    )

    logger.info("gmail_oauth_connected", user_id=str(current_user.id), email=email)

    return {"success": True, "email": email}


@router.post("/exchange")
async def gmail_exchange(
    request: OAuthExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange OAuth code for Gmail access tokens (called by frontend callback page)."""
    settings = get_settings()

    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=503, detail="Gmail OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "code": request.code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_oauth_redirect_uri,
            },
        )

        if token_response.status_code != 200:
            logger.error("gmail_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received from Google")

        # Get user info
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        email = None
        if userinfo_response.status_code == 200:
            userinfo = userinfo_response.json()
            email = userinfo.get("email")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="gmail",
        access_token=access_token,
        refresh_token=refresh_token,
        scope=settings.google_gmail_scopes,
        extra_config={"email": email},
    )

    logger.info("gmail_oauth_exchanged", user_id=str(current_user.id), email=email)

    return {"success": True, "email": email, "connected": True}


@router.delete("/disconnect")
async def gmail_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Gmail integration."""
    deleted = delete_credential(db, current_user.id, "gmail")
    if deleted:
        return {"success": True, "message": "Gmail disconnected"}
    raise HTTPException(status_code=404, detail="Gmail not connected")
