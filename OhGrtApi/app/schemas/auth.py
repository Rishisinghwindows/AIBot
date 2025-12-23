"""
Authentication schemas for request/response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    display_name: Optional[str] = None
    firebase_uid: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: Optional[str] = None
    photo_url: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # user_id
    email: str
    exp: datetime
    iat: datetime
    type: str = "access"


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str = Field(..., min_length=1)


class GoogleAuthRequest(BaseModel):
    """Schema for Google/Firebase authentication request."""

    firebase_id_token: str = Field(..., min_length=1)
    device_info: Optional[str] = None


class LogoutRequest(BaseModel):
    """Schema for logout request."""

    refresh_token: str = Field(..., min_length=1)
