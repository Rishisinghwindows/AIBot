"""
Firebase Authentication.

Verifies Firebase ID tokens for Google Sign-In.
"""

import logging
from typing import Optional, Dict, Any

import firebase_admin
from firebase_admin import credentials, auth

from ohgrt_api.config import settings

logger = logging.getLogger(__name__)

_firebase_initialized = False


def initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK.

    Returns:
        True if initialized successfully
    """
    global _firebase_initialized

    if _firebase_initialized:
        return True

    try:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized")
        return True
    except FileNotFoundError:
        logger.warning(
            f"Firebase credentials not found at {settings.firebase_credentials_path}"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False


async def verify_firebase_token(id_token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Firebase ID token.

    Args:
        id_token: Firebase ID token from client

    Returns:
        Decoded token claims or None if invalid
    """
    if not _firebase_initialized:
        if not initialize_firebase():
            logger.error("Firebase not initialized, cannot verify token")
            return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
            "email_verified": decoded_token.get("email_verified", False),
        }
    except auth.ExpiredIdTokenError:
        logger.warning("Firebase token expired")
        return None
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase token: {e}")
        return None
    except Exception as e:
        logger.error(f"Firebase token verification error: {e}")
        return None


async def get_firebase_user(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get Firebase user by UID.

    Args:
        uid: Firebase user ID

    Returns:
        User data or None
    """
    if not _firebase_initialized:
        if not initialize_firebase():
            return None

    try:
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "name": user.display_name,
            "picture": user.photo_url,
            "email_verified": user.email_verified,
        }
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        logger.error(f"Error fetching Firebase user: {e}")
        return None
