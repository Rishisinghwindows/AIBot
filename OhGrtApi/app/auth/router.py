from __future__ import annotations

from datetime import datetime, timezone, timedelta
import uuid
import urllib.parse
from typing import Dict, Any
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.firebase import FirebaseService
from app.auth.jwt_handler import JWTHandler
from app.auth.models import (
    BirthDetailsRequest,
    BirthDetailsResponse,
    GoogleAuthRequest,
    OAuthExchangeRequest,
    OAuthStartResponse,
    ProfileUpdateRequest,
    ProviderConnectRequest,
    ProviderInfo,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import RefreshToken, User, IntegrationCredential, UsedNonce, UserBirthDetails
from app.logger import logger
from app.utils.crypto import encrypt_credential, decrypt_credential, encrypt_if_needed
from app.services.astrology_service import calculate_moon_sign, calculate_nakshatra, get_sun_sign_from_date
from app.utils.validators import validate_date_string, validate_time_string, ValidationError

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Authenticate with Google via Firebase",
    description="""
Exchange a Firebase ID token for JWT access and refresh tokens.

## Flow
1. Client authenticates with Google Sign-In via Firebase SDK
2. Client sends Firebase ID token to this endpoint
3. Backend verifies token, creates/updates user record
4. Returns JWT access token (short-lived) and refresh token (long-lived)

## Response
- `access_token`: Short-lived JWT for API authentication (default: 60 minutes)
- `refresh_token`: Long-lived token for obtaining new access tokens (default: 30 days)
- `expires_in`: Access token expiration time in seconds
    """,
    responses={
        200: {
            "description": "Authentication successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIs...",
                        "refresh_token": "c7f4e2a8b5d6...",
                        "expires_in": 3600
                    }
                }
            }
        },
        401: {
            "description": "Invalid Firebase token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid Firebase token"}
                }
            }
        },
        400: {
            "description": "Email not available from Google account",
            "content": {
                "application/json": {
                    "example": {"detail": "Email not available from Google account"}
                }
            }
        },
        409: {
            "description": "Email already registered with different account",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered with different account"}
                }
            }
        }
    }
)
async def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """
    Exchange a Firebase ID token for JWT access and refresh tokens.

    This endpoint is called after the client authenticates with Google via Firebase.
    It verifies the Firebase token, creates or updates the user, and returns JWTs.
    """
    firebase_service = FirebaseService(settings)
    jwt_handler = JWTHandler(settings)

    # Verify Firebase token
    try:
        token = request.token
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="id_token or firebase_id_token is required",
            )
        firebase_user = firebase_service.verify_id_token(token)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("google_auth_firebase_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        )

    if not firebase_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not available from Google account",
        )

    # Get or create user
    user = db.query(User).filter(User.firebase_uid == firebase_user["uid"]).first()

    if user is None:
        # Check if email already exists (shouldn't happen but handle it)
        existing_email = db.query(User).filter(User.email == firebase_user["email"]).first()
        if existing_email:
            logger.warning(
                "google_auth_email_exists",
                email=firebase_user["email"],
                firebase_uid=firebase_user["uid"],
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered with different account",
            )

        user = User(
            firebase_uid=firebase_user["uid"],
            email=firebase_user["email"],
            display_name=firebase_user.get("name"),
            photo_url=firebase_user.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("google_auth_user_created", user_id=str(user.id))
    else:
        # Update last login and profile info
        user.last_login_at = datetime.now(timezone.utc)
        if firebase_user.get("name"):
            user.display_name = firebase_user["name"]
        if firebase_user.get("picture"):
            user.photo_url = firebase_user["picture"]
        db.commit()
        logger.info("google_auth_user_login", user_id=str(user.id))

    # Create tokens
    access_token = jwt_handler.create_access_token(str(user.id), user.email)
    raw_refresh, token_hash, expires_at = jwt_handler.create_refresh_token()

    # Store refresh token
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_info=request.device_info,
        expires_at=expires_at,
    )
    db.add(refresh_token_record)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
Exchange a refresh token for a new access token.

## Usage
When the access token expires (401 response), use this endpoint to obtain a new one
without requiring the user to re-authenticate with Google.

## Note
The refresh token itself is not rotated - the same refresh token is returned.
    """,
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIs...",
                        "refresh_token": "c7f4e2a8b5d6...",
                        "expires_in": 3600
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired refresh token"}
                }
            }
        }
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """
    Exchange a refresh token for a new access token.

    The refresh token itself is not rotated (same token returned).
    """
    jwt_handler = JWTHandler(settings)
    token_hash = jwt_handler.hash_refresh_token(request.refresh_token)

    # Find valid refresh token
    refresh_record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )

    if refresh_record is None:
        logger.warning("refresh_token_invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == refresh_record.user_id).first()

    if user is None or not user.is_active:
        logger.warning("refresh_token_user_invalid", user_id=str(refresh_record.user_id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new access token
    access_token = jwt_handler.create_access_token(str(user.id), user.email)
    logger.info("refresh_token_success", user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # Return same refresh token
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Revoke a refresh token (logout).
    """
    jwt_handler = JWTHandler(settings)
    token_hash = jwt_handler.hash_refresh_token(request.refresh_token)

    refresh_record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if refresh_record:
        refresh_record.revoked_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("logout_success")

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        bio=user.bio,
        preferences=user.preferences,
        created_at=user.created_at,
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
) -> UserResponse:
    """Update the current user's profile."""
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.bio is not None:
        user.bio = request.bio
    if request.photo_url is not None:
        user.photo_url = request.photo_url
    if request.preferences is not None:
        # Merge preferences with existing
        existing_prefs = user.preferences or {}
        existing_prefs.update(request.preferences)
        user.preferences = existing_prefs

    db.commit()
    db.refresh(user)
    logger.info("profile_updated", user_id=str(user.id))

    return UserResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        bio=user.bio,
        preferences=user.preferences,
        created_at=user.created_at,
    )


# --- Provider connect (API-key and OAuth/one-touch) ---

PROVIDER_CATALOG = [
    {"name": "slack", "display_name": "Slack", "auth_type": "oauth"},
    {"name": "jira", "display_name": "Jira", "auth_type": "api_key"},
    {"name": "confluence", "display_name": "Confluence", "auth_type": "api_key"},
    {"name": "github", "display_name": "GitHub", "auth_type": "oauth"},
    {"name": "gmail", "display_name": "Gmail", "auth_type": "oauth"},
    {"name": "google_drive", "display_name": "Google Drive", "auth_type": "oauth"},
    {"name": "custom_mcp", "display_name": "Custom MCP", "auth_type": "api_key"},
]


def _provider_lookup(provider: str) -> dict | None:
    for p in PROVIDER_CATALOG:
        if p["name"] == provider:
            return p
    return None


def _create_nonce(db: Session, expires_in_minutes: int = 10) -> str:
    nonce = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
    record = UsedNonce(nonce=nonce, expires_at=expires_at)
    db.add(record)
    db.commit()
    return nonce


def _consume_nonce(db: Session, nonce: str) -> bool:
    record = (
        db.query(UsedNonce)
        .filter(
            UsedNonce.nonce == nonce,
            UsedNonce.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def _upsert_credential(
    db: Session,
    user_id: uuid.UUID,
    provider: str,
    display_name: str,
    access_token: str,
    config: Dict[str, Any] | None = None,
    merge_existing_config: bool = False,
) -> None:
    """Upsert integration credential with encryption for sensitive data."""
    existing = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.provider == provider,
        )
        .first()
    )

    # Encrypt the access token before storage
    encrypted_token = encrypt_credential(access_token)

    # Encrypt sensitive config values (like refresh_token)
    encrypted_config = config.copy() if config else {}
    if encrypted_config.get("refresh_token"):
        encrypted_config["refresh_token"] = encrypt_credential(encrypted_config["refresh_token"])

    if existing:
        existing.access_token = encrypted_token
        existing.display_name = display_name
        if merge_existing_config and existing.config:
            merged = dict(existing.config)
            if encrypted_config:
                merged.update(encrypted_config)
            existing.config = merged
        else:
            existing.config = encrypted_config
    else:
        cred = IntegrationCredential(
            user_id=user_id,
            provider=provider,
            display_name=display_name,
            access_token=encrypted_token,
            config=encrypted_config,
        )
        db.add(cred)

    db.commit()


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers(
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
) -> list[ProviderInfo]:
    creds = (
        db.query(IntegrationCredential)
        .filter(IntegrationCredential.user_id == user.id)
        .all()
    )
    connected_map = {c.provider: c for c in creds}
    result: list[ProviderInfo] = []
    for provider in PROVIDER_CATALOG:
        result.append(
            ProviderInfo(
                name=provider["name"],
                display_name=provider["display_name"],
                auth_type=provider.get("auth_type", "api_key"),
                connected=provider["name"] in connected_map,
            )
        )
    return result


@router.post("/providers/connect", response_model=ProviderInfo)
async def connect_provider(
    request: ProviderConnectRequest,
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
) -> ProviderInfo:
    provider = _provider_lookup(request.provider)
    if not provider:
        raise HTTPException(status_code=404, detail="Unknown provider")

    existing = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user.id,
            IntegrationCredential.provider == request.provider,
        )
        .first()
    )

    # Encrypt the secret before storage
    encrypted_secret = encrypt_credential(request.secret)

    if existing:
        existing.access_token = encrypted_secret
        existing.display_name = request.display_name
        existing.config = request.config or {}
    else:
        cred = IntegrationCredential(
            user_id=user.id,
            provider=request.provider,
            display_name=request.display_name,
            access_token=encrypted_secret,
            config=request.config or {},
        )
        db.add(cred)

    db.commit()

    return ProviderInfo(
        name=provider["name"],
        display_name=provider["display_name"],
        auth_type=provider.get("auth_type", "api_key"),
        connected=True,
    )


@router.delete("/providers/{provider}", response_model=dict)
async def disconnect_provider(
    provider: str,
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    deleted = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user.id,
            IntegrationCredential.provider == provider,
        )
        .delete()
    )
    db.commit()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Provider not connected")
    return {"message": "Disconnected"}


# --- GitHub OAuth (one-touch) ---


@router.get("/github/start", response_model=OAuthStartResponse)
async def github_oauth_start(
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OAuthStartResponse:
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    state = _create_nonce(db, expires_in_minutes=10)
    import urllib.parse

    params = urllib.parse.urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "repo",
            "state": state,
        }
    )
    auth_url = f"https://github.com/login/oauth/authorize?{params}"
    return OAuthStartResponse(auth_url=auth_url, state=state)


@router.post("/github/exchange", response_model=ProviderInfo)
async def github_oauth_exchange(
    request: OAuthExchangeRequest,
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProviderInfo:
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    if not _consume_nonce(db, request.state):
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "code": request.code,
        "redirect_uri": settings.github_redirect_uri,
        "state": request.state,
    }
    headers = {"Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token_resp = await client.post(token_url, data=payload, headers=headers)
            token_resp.raise_for_status()
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                logger.error("github_token_missing", body=token_data)
                detail = token_data.get("error_description") or token_data.get("error") or "GitHub token exchange failed"
                raise HTTPException(status_code=400, detail=detail)

            # Fetch user info to set owner default
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
            )
            user_resp.raise_for_status()
            gh_user = user_resp.json()
            owner = gh_user.get("login", "")

    except Exception as exc:  # noqa: BLE001
        logger.error("github_oauth_exchange_error", error=str(exc))
        raise HTTPException(status_code=400, detail="GitHub token exchange failed")

    existing = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user.id,
            IntegrationCredential.provider == "github",
        )
        .first()
    )

    config = {"owner": owner} if owner else {}

    # Encrypt the access token before storage
    encrypted_token = encrypt_credential(access_token)

    if existing:
        existing.access_token = encrypted_token
        existing.display_name = "GitHub"
        existing.config = {**(existing.config or {}), **config}
    else:
        cred = IntegrationCredential(
            user_id=user.id,
            provider="github",
            display_name="GitHub",
            access_token=encrypted_token,
            config=config,
        )
        db.add(cred)

    db.commit()

    return ProviderInfo(
        name="github",
        display_name="GitHub",
        auth_type="oauth",
        connected=True,
    )


# --- Generic provider OAuth (Slack, Gmail, Google Drive, GitHub alias) ---


@router.get("/providers/{provider}/start", response_model=OAuthStartResponse)
async def provider_oauth_start(
    provider: str,
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OAuthStartResponse:
    meta = _provider_lookup(provider)
    if not meta or meta.get("auth_type") != "oauth":
        raise HTTPException(status_code=404, detail="Unknown OAuth provider")

    # Reuse the existing GitHub handler
    if provider == "github":
        return await github_oauth_start(user=user, db=db, settings=settings)

    state = _create_nonce(db, expires_in_minutes=10)

    if provider == "slack":
        if not settings.slack_client_id or not settings.slack_client_secret:
            raise HTTPException(status_code=503, detail="Slack OAuth not configured")
        params = urllib.parse.urlencode(
            {
                "client_id": settings.slack_client_id,
                "redirect_uri": settings.slack_redirect_uri,
                "scope": "chat:write,channels:read,users:read",
                "state": state,
            }
        )
        auth_url = f"https://slack.com/oauth/v2/authorize?{params}"
        return OAuthStartResponse(auth_url=auth_url, state=state)

    if provider in ("gmail", "google_drive"):
        if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
            raise HTTPException(status_code=503, detail="Google OAuth not configured")
        scopes_str = (
            settings.google_gmail_scopes
            if provider == "gmail"
            else settings.google_drive_scopes
        )
        scopes = scopes_str.split()
        params = {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "include_granted_scopes": "true",
        }
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
            params
        )
        return OAuthStartResponse(auth_url=auth_url, state=state)

    raise HTTPException(status_code=404, detail="Provider not supported for OAuth")


@router.post("/providers/{provider}/exchange", response_model=ProviderInfo)
async def provider_oauth_exchange(
    provider: str,
    request: OAuthExchangeRequest,
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProviderInfo:
    meta = _provider_lookup(provider)
    if not meta or meta.get("auth_type") != "oauth":
        raise HTTPException(status_code=404, detail="Unknown OAuth provider")

    if provider == "github":
        return await github_oauth_exchange(request=request, user=user, db=db, settings=settings)

    if not _consume_nonce(db, request.state):
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    if provider == "slack":
        if not settings.slack_client_id or not settings.slack_client_secret:
            raise HTTPException(status_code=503, detail="Slack OAuth not configured")
        token_url = "https://slack.com/api/oauth.v2.access"
        payload = {
            "client_id": settings.slack_client_id,
            "client_secret": settings.slack_client_secret,
            "code": request.code,
            "redirect_uri": settings.slack_redirect_uri,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(token_url, data=payload)
            data = resp.json()
            if not data.get("ok"):
                detail = data.get("error") or "Slack token exchange failed"
                raise HTTPException(status_code=400, detail=detail)
            access_token = data.get("access_token")
            if not access_token:
                raise HTTPException(status_code=400, detail="Slack token missing")
            config = {
                "scope": data.get("scope"),
                "token_type": data.get("token_type"),
                "team": data.get("team"),
                "bot_user_id": data.get("bot_user_id"),
                "app_id": data.get("app_id"),
            }
        _upsert_credential(
            db,
            user_id=user.id,
            provider="slack",
            display_name="Slack",
            access_token=access_token,
            config=config,
        )
        return ProviderInfo(name="slack", display_name="Slack", auth_type="oauth", connected=True)

    if provider in ("gmail", "google_drive"):
        if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
            raise HTTPException(status_code=503, detail="Google OAuth not configured")
        token_url = "https://oauth2.googleapis.com/token"
        redirect_uri = settings.google_oauth_redirect_uri
        payload = {
            "code": request.code,
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            token_resp = await client.post(token_url, data=payload)
            if token_resp.status_code >= 400:
                raise HTTPException(status_code=400, detail="Google token exchange failed")
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                detail = token_data.get("error_description") or token_data.get("error") or "Google token exchange failed"
                raise HTTPException(status_code=400, detail=detail)
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            scope = token_data.get("scope")
            token_type = token_data.get("token_type")
            config: Dict[str, Any] = {
                "scope": scope,
                "token_type": token_type,
                "refresh_token": refresh_token,
            }
            if expires_in:
                try:
                    expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                    config["expires_at"] = expiry_dt.isoformat()
                except Exception:
                    pass
        _upsert_credential(
            db,
            user_id=user.id,
            provider=provider,
            display_name="Gmail" if provider == "gmail" else "Google Drive",
            access_token=access_token,
            config=config,
            merge_existing_config=True,
        )
        return ProviderInfo(
            name=provider,
            display_name="Gmail" if provider == "gmail" else "Google Drive",
            auth_type="oauth",
            connected=True,
        )

    raise HTTPException(status_code=404, detail="Provider not supported for OAuth")


# --- Birth Details for Astrology ---

ZODIAC_SIGNS = [
    ("Aries", (3, 21), (4, 19)),
    ("Taurus", (4, 20), (5, 20)),
    ("Gemini", (5, 21), (6, 20)),
    ("Cancer", (6, 21), (7, 22)),
    ("Leo", (7, 23), (8, 22)),
    ("Virgo", (8, 23), (9, 22)),
    ("Libra", (9, 23), (10, 22)),
    ("Scorpio", (10, 23), (11, 21)),
    ("Sagittarius", (11, 22), (12, 21)),
    ("Capricorn", (12, 22), (1, 19)),
    ("Aquarius", (1, 20), (2, 18)),
    ("Pisces", (2, 19), (3, 20)),
]


def _calculate_zodiac_sign(birth_date: str) -> str | None:
    """Calculate zodiac sign from birth date (DD-MM-YYYY format)."""
    try:
        parts = birth_date.split("-")
        if len(parts) != 3:
            return None
        day, month = int(parts[0]), int(parts[1])

        for sign, (start_month, start_day), (end_month, end_day) in ZODIAC_SIGNS:
            if sign == "Capricorn":
                if (month == 12 and day >= 22) or (month == 1 and day <= 19):
                    return sign
            elif (month == start_month and day >= start_day) or (month == end_month and day <= end_day):
                return sign
        return None
    except Exception:
        return None


@router.get("/birth-details", response_model=BirthDetailsResponse | None)
async def get_birth_details(
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
) -> BirthDetailsResponse | None:
    """Get the current user's birth details."""
    birth_details = (
        db.query(UserBirthDetails)
        .filter(UserBirthDetails.user_id == user.id)
        .first()
    )

    if not birth_details:
        return None

    return BirthDetailsResponse(
        id=str(birth_details.id),
        user_id=str(birth_details.user_id),
        full_name=birth_details.full_name,
        birth_date=birth_details.birth_date,
        birth_time=birth_details.birth_time,
        birth_place=birth_details.birth_place,
        zodiac_sign=birth_details.zodiac_sign,
        moon_sign=birth_details.moon_sign,
        nakshatra=birth_details.nakshatra,
        created_at=birth_details.created_at,
        updated_at=birth_details.updated_at,
    )


@router.post("/birth-details", response_model=BirthDetailsResponse)
async def save_birth_details(
    request: BirthDetailsRequest,
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
) -> BirthDetailsResponse:
    """Save or update the current user's birth details."""
    # Validate input date if provided
    if request.birth_date:
        try:
            day, month, year = validate_date_string(
                request.birth_date, "birth_date", allow_future=False
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.message)

    # Validate input time if provided
    if request.birth_time:
        try:
            validate_time_string(request.birth_time, "birth_time")
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.message)

    existing = (
        db.query(UserBirthDetails)
        .filter(UserBirthDetails.user_id == user.id)
        .first()
    )

    # Auto-calculate zodiac sign if birth_date is provided and zodiac_sign is not
    zodiac_sign = request.zodiac_sign
    if not zodiac_sign and request.birth_date:
        zodiac_sign = _calculate_zodiac_sign(request.birth_date)

    # Calculate moon sign and nakshatra if both birth_date and birth_time are provided
    moon_sign = None
    nakshatra = None

    birth_date = request.birth_date or (existing.birth_date if existing else None)
    birth_time = request.birth_time or (existing.birth_time if existing else None)

    if birth_date and birth_time:
        moon_sign = calculate_moon_sign(birth_date, birth_time)
        nakshatra_result, pada = calculate_nakshatra(birth_date, birth_time)
        if nakshatra_result and pada:
            nakshatra = f"{nakshatra_result} (Pada {pada})"
        elif nakshatra_result:
            nakshatra = nakshatra_result

    if existing:
        # Update existing record
        if request.full_name is not None:
            existing.full_name = request.full_name
        if request.birth_date is not None:
            existing.birth_date = request.birth_date
        if request.birth_time is not None:
            existing.birth_time = request.birth_time
        if request.birth_place is not None:
            existing.birth_place = request.birth_place
        if zodiac_sign is not None:
            existing.zodiac_sign = zodiac_sign
        if moon_sign is not None:
            existing.moon_sign = moon_sign
        if nakshatra is not None:
            existing.nakshatra = nakshatra
        db.commit()
        db.refresh(existing)
        logger.info("birth_details_updated", user_id=str(user.id))
        birth_details = existing
    else:
        # Create new record
        birth_details = UserBirthDetails(
            user_id=user.id,
            full_name=request.full_name,
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            birth_place=request.birth_place,
            zodiac_sign=zodiac_sign,
            moon_sign=moon_sign,
            nakshatra=nakshatra,
        )
        db.add(birth_details)
        db.commit()
        db.refresh(birth_details)
        logger.info("birth_details_created", user_id=str(user.id))

    return BirthDetailsResponse(
        id=str(birth_details.id),
        user_id=str(birth_details.user_id),
        full_name=birth_details.full_name,
        birth_date=birth_details.birth_date,
        birth_time=birth_details.birth_time,
        birth_place=birth_details.birth_place,
        zodiac_sign=birth_details.zodiac_sign,
        moon_sign=birth_details.moon_sign,
        nakshatra=birth_details.nakshatra,
        created_at=birth_details.created_at,
        updated_at=birth_details.updated_at,
    )


@router.delete("/birth-details")
async def delete_birth_details(
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete the current user's birth details."""
    deleted = (
        db.query(UserBirthDetails)
        .filter(UserBirthDetails.user_id == user.id)
        .delete()
    )
    db.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Birth details not found")

    logger.info("birth_details_deleted", user_id=str(user.id))
    return {"message": "Birth details deleted"}
