from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt

from app.config import Settings
from app.logger import logger


class JWTPayload:
    """Decoded JWT payload."""

    def __init__(self, sub: str, email: str, exp: datetime, iat: datetime, token_type: str):
        self.sub = sub  # user_id
        self.email = email
        self.exp = exp
        self.iat = iat
        self.token_type = token_type


class JWTHandler:
    """Handler for creating and validating JWT tokens."""

    def __init__(self, settings: Settings) -> None:
        self.secret = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_expire_days = settings.jwt_refresh_token_expire_days

        if not self.secret:
            raise ValueError("JWT_SECRET_KEY must be set in environment")

    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create a short-lived access token.

        Args:
            user_id: The user's UUID as string
            email: The user's email

        Returns:
            Encoded JWT access token
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_expire_minutes)

        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "iat": now,
            "type": "access",
        }

        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        logger.debug("access_token_created", user_id=user_id)
        return token

    def create_refresh_token(self) -> Tuple[str, str, datetime]:
        """
        Create a long-lived refresh token.

        Returns:
            Tuple of (raw_token, token_hash, expires_at)
            - raw_token: The token to send to the client
            - token_hash: SHA256 hash to store in database
            - expires_at: Expiration datetime
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.refresh_expire_days)

        logger.debug("refresh_token_created")
        return raw_token, token_hash, expires_at

    def decode_access_token(self, token: str) -> Optional[JWTPayload]:
        """
        Decode and validate an access token.

        Args:
            token: The JWT access token

        Returns:
            JWTPayload if valid, None if invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])

            if payload.get("type") != "access":
                logger.warning("jwt_wrong_type", expected="access", got=payload.get("type"))
                return None

            return JWTPayload(
                sub=payload["sub"],
                email=payload["email"],
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                token_type=payload["type"],
            )
        except jwt.ExpiredSignatureError:
            logger.debug("jwt_expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("jwt_invalid", error=str(e))
            return None

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        """Hash a refresh token for database storage/lookup."""
        return hashlib.sha256(token.encode()).hexdigest()
