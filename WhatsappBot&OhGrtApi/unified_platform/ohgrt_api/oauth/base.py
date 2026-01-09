"""Base OAuth utilities and token management."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ohgrt_api.db.models import IntegrationCredential, User
from ohgrt_api.logger import logger


def get_or_create_credential(
    db: Session,
    user_id: UUID,
    provider: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    scope: Optional[str] = None,
    extra_config: Optional[dict] = None,
) -> IntegrationCredential:
    """Get or create an integration credential for a user/provider."""
    credential = (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.provider == provider,
        )
        .first()
    )

    config = extra_config or {}
    if refresh_token:
        config["refresh_token"] = refresh_token
    if expires_at:
        config["expires_at"] = expires_at.isoformat()
    if scope:
        config["scope"] = scope

    if credential:
        credential.access_token = access_token
        credential.config = config
        credential.updated_at = datetime.now(timezone.utc)
        logger.info("oauth_credential_updated", provider=provider, user_id=str(user_id))
    else:
        credential = IntegrationCredential(
            user_id=user_id,
            provider=provider,
            access_token=access_token,
            config=config,
        )
        db.add(credential)
        logger.info("oauth_credential_created", provider=provider, user_id=str(user_id))

    db.commit()
    db.refresh(credential)
    return credential


def get_credential(
    db: Session,
    user_id: UUID,
    provider: str,
) -> Optional[IntegrationCredential]:
    """Get an integration credential for a user/provider."""
    return (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.provider == provider,
        )
        .first()
    )


def delete_credential(
    db: Session,
    user_id: UUID,
    provider: str,
) -> bool:
    """Delete an integration credential."""
    credential = get_credential(db, user_id, provider)
    if credential:
        db.delete(credential)
        db.commit()
        logger.info("oauth_credential_deleted", provider=provider, user_id=str(user_id))
        return True
    return False


def generate_state() -> str:
    """Generate a secure random state for OAuth."""
    return secrets.token_urlsafe(32)


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[User]:
    """Get user by Firebase UID."""
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()
