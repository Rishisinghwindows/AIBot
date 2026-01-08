from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GoogleAuthRequest(BaseModel):
    """Request to exchange Firebase ID token for JWT."""

    firebase_id_token: str = Field(None, description="Firebase ID token from client")
    id_token: str = Field(None, description="Firebase ID token (alias)")

    device_info: Optional[str] = Field(None, description="Device identifier for token management")

    @property
    def token(self) -> str:
        """Get the ID token from either field."""
        return self.id_token or self.firebase_id_token or ""


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str = Field(..., description="Refresh token")


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds until access token expires


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile."""

    display_name: Optional[str] = Field(None, max_length=255, description="Display name")
    bio: Optional[str] = Field(None, max_length=500, description="Short bio")
    photo_url: Optional[str] = Field(None, description="Avatar/photo URL")
    preferences: Optional[dict] = Field(None, description="User preferences (language, theme, etc.)")


class ProviderInfo(BaseModel):
    """External provider with connection status."""

    name: str
    display_name: str
    auth_type: str = "api_key"
    connected: bool


class ProviderConnectRequest(BaseModel):
    """Connect to an external provider with an API key/token."""

    provider: str
    secret: str = Field(..., min_length=1, description="API key or access token")
    display_name: str | None = None
    config: dict | None = None


class OAuthStartResponse(BaseModel):
    """Response for OAuth start containing the authorization URL and state."""

    auth_url: str
    state: str


class OAuthExchangeRequest(BaseModel):
    """Request to exchange an OAuth code for tokens."""

    code: str
    state: str


class BirthDetailsRequest(BaseModel):
    """Request to save user birth details for astrology features."""

    full_name: Optional[str] = Field(None, description="User's full name")
    birth_date: Optional[str] = Field(None, description="Birth date in DD-MM-YYYY format")
    birth_time: Optional[str] = Field(None, description="Birth time in HH:MM format (24-hour)")
    birth_place: Optional[str] = Field(None, description="Birth place/city")
    zodiac_sign: Optional[str] = Field(None, description="Zodiac sign (auto-calculated if not provided)")


class BirthDetailsResponse(BaseModel):
    """Birth details response."""

    id: str
    user_id: str
    full_name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None
    zodiac_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    nakshatra: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
