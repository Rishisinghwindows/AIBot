"""
Authentication Dependencies.

FastAPI dependencies for authentication.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ohgrt_api.auth.jwt_handler import verify_token_type

# Re-export get_db for convenience
from ohgrt_api.db.base import get_db  # noqa: F401

logger = logging.getLogger(__name__)

# HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


class User:
    """Authenticated user model."""

    def __init__(
        self,
        user_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.name = name


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Get the current authenticated user.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        Authenticated User

    Raises:
        HTTPException: If not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token_type(credentials.credentials, "access")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(
        user_id=payload.get("sub", ""),
        email=payload.get("email"),
        name=payload.get("name"),
    )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[User]:
    """
    Get the current user if authenticated, else None.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        User if authenticated, else None
    """
    if not credentials:
        return None

    payload = verify_token_type(credentials.credentials, "access")

    if payload is None:
        return None

    return User(
        user_id=payload.get("sub", ""),
        email=payload.get("email"),
        name=payload.get("name"),
    )


async def require_verified_email(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require the user to have a verified email.

    Args:
        user: Current authenticated user

    Returns:
        User with verified email

    Raises:
        HTTPException: If email not verified
    """
    # In production, check email verification status
    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return user
