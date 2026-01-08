"""
JWT Token Handler.

Creates and validates JWT access and refresh tokens.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from ohgrt_api.config import settings

logger = logging.getLogger(__name__)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Token payload data
        expires_delta: Token expiry time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Token payload data
        expires_delta: Token expiry time

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
    })

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: Encoded JWT token

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """
    Verify token is of expected type.

    Args:
        token: Encoded JWT token
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        Decoded payload if valid and correct type, else None
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != expected_type:
        logger.warning(
            f"Token type mismatch. Expected: {expected_type}, Got: {payload.get('type')}"
        )
        return None

    return payload
