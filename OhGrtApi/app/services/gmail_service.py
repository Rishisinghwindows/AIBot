from __future__ import annotations

from typing import Any, Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import Settings
from app.logger import logger
from app.utils.errors import ServiceError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailService:
    def __init__(self, settings: Settings, credential: dict | None = None):
        self.settings = settings
        self.creds: Credentials | None = None
        self.service = None
        self.available = False
        self.credential = credential or {}
        if self.credential:
            self._init_from_user_credential()
        else:
            logger.info("gmail_disabled_shared_creds")

    def _init_from_user_credential(self) -> None:
        token = self.credential.get("access_token")
        config = self.credential.get("config", {})
        refresh_token = config.get("refresh_token")
        scopes = config.get("scope", "")
        scope_list = scopes.split() if scopes else SCOPES

        if not token:
            logger.info("gmail_missing_access_token")
            return

        try:
            self.creds = Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.google_oauth_client_id,
                client_secret=self.settings.google_oauth_client_secret,
                scopes=scope_list,
            )
            # Refresh if expired and refresh token is present
            if self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as exc:  # noqa: BLE001
                    logger.error("gmail_refresh_failed", error=str(exc))
                    self.creds = None
            if self.creds:
                self.service = build("gmail", "v1", credentials=self.creds)
                self.available = True
                logger.info("gmail_api_ready")
        except Exception as exc:  # noqa: BLE001
            logger.error("gmail_api_init_error", error=str(exc))
            self.service = None
            self.available = False

    async def search_emails(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.available or not self.service:
            raise ServiceError(
                "Gmail per-user OAuth is not configured. This tool is disabled until user-specific Gmail auth is added."
            )

        q = query.get("raw_query") or ""
        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=q, maxResults=10)
                .execute()
            )
            messages = results.get("messages", [])
            output = []
            for msg_meta in messages:
                msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg_meta["id"], format="metadata")
                    .execute()
                )
                headers = {
                    h["name"].lower(): h["value"]
                    for h in msg.get("payload", {}).get("headers", [])
                }
                output.append(
                    {
                        "id": msg.get("id"),
                        "snippet": msg.get("snippet"),
                        "subject": headers.get("subject", ""),
                        "from": headers.get("from", ""),
                        "date": headers.get("date", ""),
                    }
                )
        except HttpError as exc:
            logger.error("gmail_query_error", error=str(exc))
            raise ServiceError("Gmail query failed") from exc
        return output
