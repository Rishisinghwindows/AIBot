from __future__ import annotations

from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ohgrt_api.config import Settings
from ohgrt_api.logger import logger
from ohgrt_api.utils.errors import ServiceError


class GoogleDriveService:
    """Per-user Google Drive client backed by stored OAuth credentials."""

    def __init__(self, settings: Settings, credential: dict | None = None):
        self.settings = settings
        self.credential = credential or {}
        self.creds: Credentials | None = None
        self.service = None
        self.available = False
        if self.credential:
            self._init_from_user_credential()

    def _init_from_user_credential(self) -> None:
        token = self.credential.get("access_token")
        config = self.credential.get("config", {})
        refresh_token = config.get("refresh_token")
        scopes = config.get("scope", "") or self.settings.google_drive_scopes
        scope_list = scopes.split()

        if not token:
            logger.info("drive_missing_access_token")
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
            if self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as exc:  # noqa: BLE001
                    logger.error("drive_refresh_failed", error=str(exc))
                    self.creds = None
            if self.creds:
                self.service = build("drive", "v3", credentials=self.creds)
                self.available = True
                logger.info("drive_api_ready")
        except Exception as exc:  # noqa: BLE001
            logger.error("drive_api_init_error", error=str(exc))
            self.service = None
            self.available = False

    async def list_files(self, query: str | None = None, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.available or not self.service:
            raise ServiceError("Google Drive not configured. Connect Drive first.")
        q = query or ""
        try:
            results = (
                self.service.files()
                .list(
                    pageSize=limit,
                    q=q or None,
                    fields="files(id, name, mimeType, modifiedTime)",
                    spaces="drive",
                )
                .execute()
            )
            return results.get("files", [])
        except HttpError as exc:
            logger.error("drive_list_error", error=str(exc))
            raise ServiceError("Google Drive query failed") from exc
