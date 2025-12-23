from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import Settings
from app.logger import logger
from app.utils.errors import ServiceError

# Use canonical Google scopes so the authorization request and token exchange
# always match (avoids "scope has changed" errors).
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class GmailService:
    def __init__(
        self,
        settings: Settings,
        token_path: str | Path | None = None,
        auto_init: bool = True,
        credential: Dict[str, Any] | None = None,
    ):
        self.settings = settings
        self.token_path = self._resolve_token_path(token_path)
        self.creds: Credentials | None = None
        self.service = None
        self.available = False
        self.client_config = self._build_client_config()
        self._credential_override = credential
        if auto_init:
            try:
                self._init_client()
            except ServiceError:
                # Defer raising until a Gmail action is requested to avoid blocking app startup.
                self.service = None

    def _resolve_token_path(self, token_path: str | Path | None) -> Path:
        raw_path = Path(token_path) if token_path else Path(self.settings.gmail_token_file)
        if raw_path.is_absolute():
            return raw_path
        project_root = Path(__file__).resolve().parents[2]
        return project_root / raw_path

    def _build_client_config(self) -> Dict[str, Any] | None:
        client_id = (self.settings.google_oauth_client_id or "").strip()
        client_secret = (self.settings.google_oauth_client_secret or "").strip()
        redirect_uri = (self.settings.google_oauth_redirect_uri or "").strip()

        if not (client_id and client_secret):
            return None

        redirect_uris = [redirect_uri or "http://localhost"]
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": redirect_uris,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        }

    def _build_flow(self, redirect_uri: str) -> Flow:
        if not self.client_config:
            raise ServiceError("Google OAuth is not configured")
        return Flow.from_client_config(
            self.client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )

    def _persist_credentials(self, creds: Credentials, token_path: Path | None = None) -> None:
        dest = Path(token_path) if token_path else self.token_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(creds.to_json())

    def _load_credentials(self, refresh: bool = True) -> Credentials:
        # Use credential override if provided (from OAuth provider connection)
        if self._credential_override:
            try:
                token_data = self._credential_override
                if isinstance(token_data, dict):
                    creds = Credentials(
                        token=token_data.get("access_token"),
                        refresh_token=token_data.get("refresh_token"),
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=self.settings.google_oauth_client_id,
                        client_secret=self.settings.google_oauth_client_secret,
                        scopes=SCOPES,
                    )
                    if refresh and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    return creds
            except Exception as exc:
                logger.error("gmail_credential_override_failed", error=str(exc))
                raise ServiceError("Gmail credential override is invalid") from exc

        if not self.token_path.exists():
            raise ServiceError("Gmail authorization not found for this user.")

        try:
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        except Exception as exc:  # noqa: BLE001
            logger.error("gmail_token_load_failed", error=str(exc))
            raise ServiceError("Gmail token is invalid") from exc

        if refresh and creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._persist_credentials(creds)
            except Exception as exc:  # noqa: BLE001
                logger.error("gmail_refresh_failed", error=str(exc))
                raise ServiceError("Failed to refresh Gmail token") from exc

        if not creds or not creds.valid:
            raise ServiceError("Gmail token is missing or expired")

        return creds

    def _init_client(self) -> None:
        try:
            creds = self._load_credentials()
        except ServiceError as exc:
            logger.error("gmail_client_init_failed", error=str(exc))
            raise

        try:
            self.service = build("gmail", "v1", credentials=creds)
            self.creds = creds
            self.available = True
            logger.info("gmail_api_ready", token_path=str(self.token_path))
        except Exception as exc:  # noqa: BLE001
            logger.error("gmail_api_init_error", error=str(exc))
            raise ServiceError("Failed to initialize Gmail API client") from exc

    def ensure_client(self) -> None:
        """Initialize the Gmail API client if it is not already available."""
        if self.service:
            return
        self._init_client()

    def generate_authorization_url(self, state: str | None = None) -> Tuple[str, str]:
        flow = self._build_flow(self.settings.google_oauth_redirect_uri)
        auth_url, flow_state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return auth_url, flow_state

    def exchange_code_for_token(self, code: str, token_path: Path | None = None) -> Credentials:
        flow = self._build_flow(self.settings.google_oauth_redirect_uri)
        try:
            flow.fetch_token(code=code)
        except Exception as exc:  # noqa: BLE001
            logger.error("gmail_token_exchange_failed", error=str(exc))
            raise ServiceError("Failed to exchange Gmail authorization code") from exc

        creds = flow.credentials
        self._persist_credentials(creds, token_path=token_path)
        self.creds = creds
        return creds

    def load_credentials_only(self) -> Credentials:
        """Load credentials without building the API client (used for status checks)."""
        return self._load_credentials()

    async def search_emails(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.service:
            self.ensure_client()

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
