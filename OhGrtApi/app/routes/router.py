from __future__ import annotations

from datetime import datetime, timezone, timedelta
import uuid
import urllib.parse
from typing import Dict, Any
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt_handler import JWTHandler
from app.models.models import (
    OAuthExchangeRequest,
    OAuthStartResponse,
    ProviderConnectRequest,
    ProviderInfo,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import RefreshToken, User, IntegrationCredential, UsedNonce
from app.logger import logger
from app.services.firebase_service import FirebaseService
from app.services.profile_service import ProfileService
from app.utils.models import Profile, ProfileCreate

router = APIRouter(prefix="/auth", tags=["authentication"])

# Legacy Gmail router for backwards compatibility with frontend
gmail_router = APIRouter(prefix="/gmail", tags=["gmail"])

# Legacy Jira router for backwards compatibility with frontend
jira_router = APIRouter(prefix="/jira", tags=["jira"])

# Legacy GitHub router for backwards compatibility with frontend
github_router = APIRouter(prefix="/github", tags=["github"])

# Legacy Slack router for backwards compatibility with frontend
slack_router = APIRouter(prefix="/slack", tags=["slack"])

# Legacy Uber router for backwards compatibility with frontend
uber_router = APIRouter(prefix="/uber", tags=["uber"])

# OAuth2 scheme for Firebase tokens
firebase_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_firebase_service(settings: Settings = Depends(get_settings)) -> FirebaseService:
    return FirebaseService(settings)


def get_profile_service(settings: Settings = Depends(get_settings)) -> ProfileService:
    return ProfileService(settings)


async def get_current_profile_for_gmail(
    token: str = Depends(firebase_oauth2_scheme),
    profile_service: ProfileService = Depends(get_profile_service),
    firebase_service: FirebaseService = Depends(get_firebase_service),
) -> Profile:
    """Firebase-based authentication for Gmail endpoints."""
    decoded_token = firebase_service.verify_token(token)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = decoded_token.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (email missing)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile = profile_service.get_by_email(email=email)
    if profile is None:
        name = decoded_token.get("name", "")
        first_name = name.split(" ")[0] if name else ""
        last_name = " ".join(name.split(" ")[1:]) if " " in name else ""

        profile_create = ProfileCreate(
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        profile = profile_service.create(profile_create)

    return profile


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
            detail="User not found",
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
        created_at=user.created_at,
    )


# --- Provider connect (API-key and OAuth/one-touch) ---

PROVIDER_CATALOG = [
    {"name": "slack", "display_name": "Slack", "auth_type": "oauth"},
    {"name": "jira", "display_name": "Jira", "auth_type": "oauth"},
    {"name": "confluence", "display_name": "Confluence", "auth_type": "api_key"},
    {"name": "github", "display_name": "GitHub", "auth_type": "oauth"},
    {"name": "gmail", "display_name": "Gmail", "auth_type": "oauth"},
    {"name": "google_drive", "display_name": "Google Drive", "auth_type": "oauth"},
    {"name": "uber", "display_name": "Uber", "auth_type": "oauth"},
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
    """Upsert integration credential."""
    existing = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.provider == provider,
        )
        .first()
    )

    stored_config = config.copy() if config else {}

    if existing:
        existing.access_token = access_token
        existing.display_name = display_name
        if merge_existing_config and existing.config:
            merged = dict(existing.config)
            if stored_config:
                merged.update(stored_config)
            existing.config = merged
        else:
            existing.config = stored_config
    else:
        cred = IntegrationCredential(
            user_id=user_id,
            provider=provider,
            display_name=display_name,
            access_token=access_token,
            config=stored_config,
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

    if existing:
        existing.access_token = request.secret
        existing.display_name = request.display_name
        existing.config = request.config or {}
    else:
        cred = IntegrationCredential(
            user_id=user.id,
            provider=request.provider,
            display_name=request.display_name,
            access_token=request.secret,
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
    return {"message": "Disconnected successfully"}


# --- GitHub OAuth (one-touch) ---


@router.get("/github/start", response_model=OAuthStartResponse)
async def github_oauth_start(
    user: User = Depends(__import__("app.auth.dependencies", fromlist=["get_current_user"]).get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OAuthStartResponse:
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    state = _create_nonce(db, expires_in_minutes=10)

    params = urllib.parse.urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": settings.github_scopes,
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
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")

    if not _consume_nonce(db, request.state):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

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

    if existing:
        existing.access_token = access_token
        existing.display_name = "GitHub"
        existing.config = {**(existing.config or {}), **config}
    else:
        cred = IntegrationCredential(
            user_id=user.id,
            provider="github",
            display_name="GitHub",
            access_token=access_token,
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
        raise HTTPException(status_code=404, detail="Unknown provider")

    # Reuse the existing GitHub handler
    if provider == "github":
        return await github_oauth_start(user=user, db=db, settings=settings)

    state = _create_nonce(db, expires_in_minutes=10)

    if provider == "slack":
        if not settings.slack_client_id or not settings.slack_client_secret:
            raise HTTPException(status_code=503, detail="Slack OAuth is not configured")
        params = urllib.parse.urlencode(
            {
                "client_id": settings.slack_client_id,
                "redirect_uri": settings.slack_redirect_uri,
                "scope": settings.slack_scopes,
                "state": state,
            }
        )
        auth_url = f"https://slack.com/oauth/v2/authorize?{params}"
        return OAuthStartResponse(auth_url=auth_url, state=state)

    if provider in ("gmail", "google_drive"):
        if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
            raise HTTPException(status_code=503, detail="Google OAuth is not configured")
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

    if provider == "jira":
        if not settings.atlassian_client_id or not settings.atlassian_client_secret:
            raise HTTPException(status_code=503, detail="Atlassian OAuth is not configured")
        scopes = settings.atlassian_scopes.split()
        params = {
            "audience": "api.atlassian.com",
            "client_id": settings.atlassian_client_id,
            "redirect_uri": settings.atlassian_redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "prompt": "consent",
        }
        auth_url = "https://auth.atlassian.com/authorize?" + urllib.parse.urlencode(params)
        return OAuthStartResponse(auth_url=auth_url, state=state)

    if provider == "uber":
        if not settings.uber_client_id or not settings.uber_client_secret:
            raise HTTPException(status_code=503, detail="Uber OAuth is not configured")
        params = {
            "client_id": settings.uber_client_id,
            "redirect_uri": settings.uber_redirect_uri,
            "response_type": "code",
            "scope": settings.uber_scopes,
            "state": state,
        }
        auth_url = "https://login.uber.com/oauth/v2/authorize?" + urllib.parse.urlencode(params)
        return OAuthStartResponse(auth_url=auth_url, state=state)

    raise HTTPException(status_code=404, detail="Provider not supported")


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
        raise HTTPException(status_code=404, detail="Unknown provider")

    if provider == "github":
        return await github_oauth_exchange(request=request, user=user, db=db, settings=settings)

    if not _consume_nonce(db, request.state):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if provider == "slack":
        if not settings.slack_client_id or not settings.slack_client_secret:
            raise HTTPException(status_code=503, detail="Slack OAuth is not configured")
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
                raise HTTPException(status_code=400, detail="Slack access token missing")
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
            raise HTTPException(status_code=503, detail="Google OAuth is not configured")
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

            # Also write token.json for GmailService compatibility
            if provider == "gmail":
                import json
                from pathlib import Path
                token_file_data = {
                    "token": access_token,
                    "refresh_token": refresh_token,
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "scopes": scope.split() if scope else [],
                }
                if expires_in:
                    token_file_data["expiry"] = expiry_dt.isoformat().replace("+00:00", "Z")
                token_path = Path(__file__).resolve().parents[2] / settings.gmail_token_file
                token_path.parent.mkdir(parents=True, exist_ok=True)
                token_path.write_text(json.dumps(token_file_data))
                logger.info("gmail_token_saved", path=str(token_path))

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

    if provider == "jira":
        if not settings.atlassian_client_id or not settings.atlassian_client_secret:
            raise HTTPException(status_code=503, detail="Atlassian OAuth is not configured")
        token_url = "https://auth.atlassian.com/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": settings.atlassian_client_id,
            "client_secret": settings.atlassian_client_secret,
            "code": request.code,
            "redirect_uri": settings.atlassian_redirect_uri,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                token_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if token_resp.status_code >= 400:
                logger.error("jira_token_exchange_failed", status=token_resp.status_code, body=token_resp.text)
                raise HTTPException(status_code=400, detail="Atlassian token exchange failed")
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                detail = token_data.get("error_description") or token_data.get("error") or "Atlassian token exchange failed"
                raise HTTPException(status_code=400, detail=detail)
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            scope = token_data.get("scope")

            # Get accessible resources (cloud IDs) to find the Jira site
            resources_resp = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            cloud_id = None
            site_url = None
            if resources_resp.status_code == 200:
                resources = resources_resp.json()
                if resources and len(resources) > 0:
                    # Use the first accessible site
                    cloud_id = resources[0].get("id")
                    site_url = resources[0].get("url")
                    logger.info("jira_cloud_id_found", cloud_id=cloud_id, site_url=site_url)

            config: Dict[str, Any] = {
                "scope": scope,
                "refresh_token": refresh_token,
                "cloud_id": cloud_id,
                "site_url": site_url,
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
            provider="jira",
            display_name="Jira",
            access_token=access_token,
            config=config,
            merge_existing_config=True,
        )
        return ProviderInfo(name="jira", display_name="Jira", auth_type="oauth", connected=True)

    if provider == "uber":
        if not settings.uber_client_id or not settings.uber_client_secret:
            raise HTTPException(status_code=503, detail="Uber OAuth is not configured")
        token_url = "https://login.uber.com/oauth/v2/token"
        payload = {
            "client_id": settings.uber_client_id,
            "client_secret": settings.uber_client_secret,
            "grant_type": "authorization_code",
            "code": request.code,
            "redirect_uri": settings.uber_redirect_uri,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code >= 400:
                logger.error("uber_token_exchange_failed", status=token_resp.status_code, body=token_resp.text)
                raise HTTPException(status_code=400, detail="Uber token exchange failed")
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                detail = token_data.get("error_description") or token_data.get("error") or "Uber token exchange failed"
                raise HTTPException(status_code=400, detail=detail)
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            scope = token_data.get("scope")

            config: Dict[str, Any] = {
                "scope": scope,
                "refresh_token": refresh_token,
            }
            if expires_in:
                try:
                    expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                    config["expires_at"] = expiry_dt.isoformat()
                except Exception:
                    pass

            # Optionally fetch user profile info
            try:
                profile_resp = await client.get(
                    "https://api.uber.com/v1.2/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if profile_resp.status_code == 200:
                    profile_data = profile_resp.json()
                    config["first_name"] = profile_data.get("first_name")
                    config["last_name"] = profile_data.get("last_name")
                    config["rider_id"] = profile_data.get("rider_id")
            except Exception as e:
                logger.warning("uber_profile_fetch_failed", error=str(e))

        _upsert_credential(
            db,
            user_id=user.id,
            provider="uber",
            display_name="Uber",
            access_token=access_token,
            config=config,
            merge_existing_config=True,
        )
        return ProviderInfo(name="uber", display_name="Uber", auth_type="oauth", connected=True)

    raise HTTPException(status_code=404, detail="Provider not supported")


# ===== Legacy Gmail Endpoints for Frontend Compatibility =====

@gmail_router.get("/status")
async def gmail_status(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
) -> dict:
    """Check if Gmail is connected for the current user."""
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == profile.id,
            IntegrationCredential.provider == "gmail",
        )
        .first()
    )
    return {"connected": cred is not None}


@gmail_router.get("/oauth-url")
async def gmail_oauth_url(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the OAuth URL for Gmail authorization."""
    # Create a mock user object with the profile id for compatibility
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    response = await provider_oauth_start(provider="gmail", user=mock_user, db=db, settings=settings)
    return {"auth_url": response.auth_url, "state": response.state}


@gmail_router.post("/exchange")
@gmail_router.post("/oauth/exchange")  # Alias for frontend compatibility
async def gmail_exchange(
    request: OAuthExchangeRequest,
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProviderInfo:
    """Exchange OAuth code for Gmail access token."""
    # Create a mock user object with the profile id for compatibility
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    return await provider_oauth_exchange(provider="gmail", request=request, user=mock_user, db=db, settings=settings)


# ===== Legacy Jira Endpoints for Frontend Compatibility =====

@jira_router.get("/status")
async def jira_status(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
) -> dict:
    """Check if Jira is connected for the current user."""
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == profile.id,
            IntegrationCredential.provider == "jira",
        )
        .first()
    )
    if cred:
        return {
            "connected": True,
            "site_url": cred.config.get("site_url") if cred.config else None,
        }
    return {"connected": False}


@jira_router.get("/oauth-url")
async def jira_oauth_url(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the OAuth URL for Jira authorization."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    response = await provider_oauth_start(provider="jira", user=mock_user, db=db, settings=settings)
    return {"auth_url": response.auth_url, "state": response.state}


@jira_router.post("/exchange")
@jira_router.post("/oauth/exchange")  # Alias for frontend compatibility
async def jira_exchange(
    request: OAuthExchangeRequest,
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProviderInfo:
    """Exchange OAuth code for Jira access token."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    return await provider_oauth_exchange(provider="jira", request=request, user=mock_user, db=db, settings=settings)


# ===== Legacy GitHub Endpoints for Frontend Compatibility =====

@github_router.get("/status")
async def github_status(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
) -> dict:
    """Check if GitHub is connected for the current user."""
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == profile.id,
            IntegrationCredential.provider == "github",
        )
        .first()
    )
    if cred:
        return {
            "connected": True,
            "owner": cred.config.get("owner") if cred.config else None,
        }
    return {"connected": False}


@github_router.get("/oauth-url")
async def github_oauth_url(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the OAuth URL for GitHub authorization."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    response = await github_oauth_start(user=mock_user, db=db, settings=settings)
    return {"auth_url": response.auth_url, "state": response.state}


@github_router.post("/exchange")
@github_router.post("/oauth/exchange")  # Alias for frontend compatibility
async def github_exchange(
    request: OAuthExchangeRequest,
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProviderInfo:
    """Exchange OAuth code for GitHub access token."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    return await github_oauth_exchange(request=request, user=mock_user, db=db, settings=settings)


# ===== Legacy Slack Endpoints for Frontend Compatibility =====

@slack_router.get("/status")
async def slack_status(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
) -> dict:
    """Check if Slack is connected for the current user."""
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == profile.id,
            IntegrationCredential.provider == "slack",
        )
        .first()
    )
    if cred:
        team = cred.config.get("team") if cred.config else None
        return {
            "connected": True,
            "team_name": team.get("name") if team else None,
        }
    return {"connected": False}


@slack_router.get("/oauth-url")
async def slack_oauth_url(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the OAuth URL for Slack authorization."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    response = await provider_oauth_start(provider="slack", user=mock_user, db=db, settings=settings)
    return {"auth_url": response.auth_url, "state": response.state}


@slack_router.post("/exchange")
@slack_router.post("/oauth/exchange")  # Alias for frontend compatibility
async def slack_exchange(
    request: OAuthExchangeRequest,
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProviderInfo:
    """Exchange OAuth code for Slack access token."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    return await provider_oauth_exchange(provider="slack", request=request, user=mock_user, db=db, settings=settings)


# ===== Legacy Uber Endpoints for Frontend Compatibility =====

@uber_router.get("/status")
async def uber_status(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
) -> dict:
    """Check if Uber is connected for the current user."""
    cred = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == profile.id,
            IntegrationCredential.provider == "uber",
        )
        .first()
    )
    if cred:
        return {
            "connected": True,
            "first_name": cred.config.get("first_name") if cred.config else None,
            "rider_id": cred.config.get("rider_id") if cred.config else None,
        }
    return {"connected": False}


@uber_router.get("/oauth-url")
async def uber_oauth_url(
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get the OAuth URL for Uber authorization."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    response = await provider_oauth_start(provider="uber", user=mock_user, db=db, settings=settings)
    return {"auth_url": response.auth_url, "state": response.state}


@uber_router.post("/exchange")
@uber_router.post("/oauth/exchange")  # Alias for frontend compatibility
async def uber_exchange(
    request: OAuthExchangeRequest,
    profile: Profile = Depends(get_current_profile_for_gmail),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ProviderInfo:
    """Exchange OAuth code for Uber access token."""
    class MockUser:
        def __init__(self, user_id):
            self.id = user_id
    mock_user = MockUser(profile.id)
    return await provider_oauth_exchange(provider="uber", request=request, user=mock_user, db=db, settings=settings)
