"""
Authentication module.

Provides Firebase and JWT authentication.
"""

from ohgrt_api.auth.router import router
from ohgrt_api.auth.firebase import verify_firebase_token
from ohgrt_api.auth.jwt_handler import create_access_token, decode_token
from ohgrt_api.auth.dependencies import get_current_user, get_optional_user

__all__ = [
    "router",
    "verify_firebase_token",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "get_optional_user",
]
