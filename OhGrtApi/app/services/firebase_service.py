
import json
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials

from app.logger import logger
from app.utils.errors import ServiceError


class FirebaseService:
    """
    Lightweight wrapper around firebase_admin that centralizes
    credential loading and token verification.
    """

    def __init__(self, settings):
        self.settings = settings
        self.app = self._get_or_init_app()

    def _load_credentials(self) -> Dict[str, Any]:
        raw_creds = self.settings.firebase_credentials
        if not raw_creds:
            logger.error("firebase_credentials_missing")
            raise ServiceError("Firebase credentials are not configured")

        try:
            cred_json = json.loads(raw_creds)
        except json.JSONDecodeError as exc:
            logger.error("firebase_credentials_invalid_json", error=str(exc))
            raise ServiceError("Invalid Firebase credentials JSON") from exc

        # Handle escaped newlines that often appear in env vars
        private_key: Optional[str] = cred_json.get("private_key")
        if private_key:
            cred_json["private_key"] = private_key.replace("\\n", "\n")

        return cred_json

    def _get_or_init_app(self) -> firebase_admin.App:
        try:
            return firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(self._load_credentials())
            return firebase_admin.initialize_app(cred)

    def verify_token(self, token: str):
        if not token:
            logger.warning("firebase_verify_missing_token")
            return None

        try:
            decoded_token = auth.verify_id_token(token, app=self.app)
            return decoded_token
        except Exception as exc:
            logger.warning("firebase_verify_failed", error=str(exc))
            return None
