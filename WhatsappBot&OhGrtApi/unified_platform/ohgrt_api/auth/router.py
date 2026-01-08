"""
Authentication Router.

Provides authentication endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ohgrt_api.auth.firebase import verify_firebase_token
from ohgrt_api.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token_type,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


class GoogleSignInRequest(BaseModel):
    """Request model for Google Sign-In."""

    id_token: str = Field(..., description="Firebase ID token")


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str


@router.post("/google", response_model=TokenResponse)
async def google_sign_in(request: GoogleSignInRequest):
    """
    Sign in with Google via Firebase.

    Args:
        request: GoogleSignInRequest with Firebase ID token

    Returns:
        TokenResponse with access and refresh tokens
    """
    # Verify Firebase token
    firebase_user = await verify_firebase_token(request.id_token)

    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    # Create JWT tokens
    token_data = {
        "sub": firebase_user["uid"],
        "email": firebase_user.get("email"),
        "name": firebase_user.get("name"),
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,  # 15 minutes in seconds
        user={
            "id": firebase_user["uid"],
            "email": firebase_user.get("email"),
            "name": firebase_user.get("name"),
            "picture": firebase_user.get("picture"),
        },
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: RefreshRequest):
    """
    Refresh access token using refresh token.

    Args:
        request: RefreshRequest with refresh token

    Returns:
        TokenResponse with new tokens
    """
    payload = verify_token_type(request.refresh_token, "refresh")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Create new tokens
    token_data = {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,
        user={
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
        },
    )


@router.post("/logout")
async def logout():
    """
    Logout endpoint.

    Client should discard tokens. Server-side token revocation
    can be implemented with a token blacklist if needed.
    """
    return {"message": "Logged out successfully"}
