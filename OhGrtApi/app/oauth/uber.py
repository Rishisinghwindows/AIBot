"""Uber OAuth router."""

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


router = APIRouter(prefix="/uber", tags=["uber-oauth"])

UBER_AUTH_URL = "https://login.uber.com/oauth/v2/authorize"
UBER_TOKEN_URL = "https://login.uber.com/oauth/v2/token"
UBER_PROFILE_URL = "https://api.uber.com/v1.2/me"


@router.get("/status")
async def uber_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check Uber connection status."""
    credential = get_credential(db, current_user.id, "uber")
    if credential:
        return {
            "connected": True,
            "first_name": credential.config.get("first_name"),
            "email": credential.config.get("email"),
        }
    return {"connected": False}


@router.get("/oauth-url")
async def uber_oauth_url(
    current_user: User = Depends(get_current_user),
):
    """Get Uber OAuth authorization URL."""
    settings = get_settings()

    if not settings.uber_client_id:
        raise HTTPException(
            status_code=503,
            detail="Uber OAuth not configured. Set UBER_CLIENT_ID in environment.",
        )

    state = generate_state()

    # Uber OAuth scopes
    scopes = "profile history request"

    params = {
        "client_id": settings.uber_client_id,
        "response_type": "code",
        "scope": scopes,
        "redirect_uri": settings.uber_redirect_uri,
        "state": state,
    }

    auth_url = f"{UBER_AUTH_URL}?{urlencode(params)}"
    logger.info("uber_oauth_url_generated", user_id=str(current_user.id))

    return {"auth_url": auth_url, "state": state}


@router.post("/callback")
async def uber_callback(
    code: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Handle Uber OAuth callback and exchange code for tokens."""
    settings = get_settings()

    if not settings.uber_client_id or not settings.uber_client_secret:
        raise HTTPException(status_code=503, detail="Uber OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            UBER_TOKEN_URL,
            data={
                "client_id": settings.uber_client_id,
                "client_secret": settings.uber_client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": settings.uber_redirect_uri,
                "code": code,
            },
        )

        if token_response.status_code != 200:
            logger.error("uber_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        # Get user profile
        profile_response = await client.get(
            UBER_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        first_name = None
        email = None

        if profile_response.status_code == 200:
            profile = profile_response.json()
            first_name = profile.get("first_name")
            email = profile.get("email")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="uber",
        access_token=access_token,
        refresh_token=refresh_token,
        extra_config={
            "first_name": first_name,
            "email": email,
        },
    )

    logger.info("uber_oauth_connected", user_id=str(current_user.id), first_name=first_name)

    return {"success": True, "first_name": first_name, "email": email}


@router.post("/exchange")
async def uber_exchange(
    request: OAuthExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exchange OAuth code for Uber access tokens (called by frontend callback page)."""
    settings = get_settings()

    if not settings.uber_client_id or not settings.uber_client_secret:
        raise HTTPException(status_code=503, detail="Uber OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            UBER_TOKEN_URL,
            data={
                "client_id": settings.uber_client_id,
                "client_secret": settings.uber_client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": settings.uber_redirect_uri,
                "code": request.code,
            },
        )

        if token_response.status_code != 200:
            logger.error("uber_token_exchange_failed", error=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received from Uber")

        # Get user profile
        profile_response = await client.get(
            UBER_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        first_name = None
        email = None

        if profile_response.status_code == 200:
            profile = profile_response.json()
            first_name = profile.get("first_name")
            email = profile.get("email")

    # Store credentials
    get_or_create_credential(
        db=db,
        user_id=current_user.id,
        provider="uber",
        access_token=access_token,
        refresh_token=refresh_token,
        extra_config={
            "first_name": first_name,
            "email": email,
        },
    )

    logger.info("uber_oauth_exchanged", user_id=str(current_user.id), first_name=first_name)

    return {"success": True, "first_name": first_name, "email": email, "connected": True}


@router.delete("/disconnect")
async def uber_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Uber integration."""
    deleted = delete_credential(db, current_user.id, "uber")
    if deleted:
        return {"success": True, "message": "Uber disconnected"}
    raise HTTPException(status_code=404, detail="Uber not connected")
