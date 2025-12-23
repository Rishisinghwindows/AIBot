from __future__ import annotations

from typing import TypedDict

import firebase_admin
from firebase_admin import auth, credentials

from app.config import Settings
from app.logger import logger


class FirebaseUserInfo(TypedDict):
    uid: str
    email: str | None
    name: str | None
    picture: str | None


class FirebaseService:
    """Service for verifying Firebase ID tokens."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._initialize_app()

    def _initialize_app(self) -> None:
        """Initialize Firebase Admin SDK if not already initialized."""
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(self.settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred)
                logger.info("firebase_initialized")
            except Exception as e:
                logger.error("firebase_init_failed", error=str(e))
                raise

    def verify_id_token(self, id_token: str) -> FirebaseUserInfo:
        """
        Verify a Firebase ID token and return user info.

        Args:
            id_token: The Firebase ID token from the client

        Returns:
            FirebaseUserInfo with uid, email, name, and picture

        Raises:
            firebase_admin.auth.InvalidIdTokenError: If token is invalid
            firebase_admin.auth.ExpiredIdTokenError: If token is expired
        """
        try:
            decoded = auth.verify_id_token(id_token)
            user_info: FirebaseUserInfo = {
                "uid": decoded["uid"],
                "email": decoded.get("email"),
                "name": decoded.get("name"),
                "picture": decoded.get("picture"),
            }
            logger.info("firebase_token_verified", uid=user_info["uid"])
            return user_info
        except auth.InvalidIdTokenError as e:
            logger.warning("firebase_invalid_token", error=str(e))
            raise
        except auth.ExpiredIdTokenError as e:
            logger.warning("firebase_expired_token", error=str(e))
            raise
        except Exception as e:
            logger.error("firebase_verification_failed", error=str(e))
            raise
