from __future__ import annotations

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import Settings
from app.logger import logger
from app.utils.errors import ServiceError

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


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

        logger.info(
            "gmail_init_attempt",
            has_access_token=bool(token),
            has_refresh_token=bool(refresh_token),
            scopes=scope_list,
        )

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
            logger.info("gmail_credentials_created", expired=self.creds.expired, has_refresh=bool(self.creds.refresh_token))

            # Refresh if expired and refresh token is present
            if self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("gmail_refreshing_token")
                    self.creds.refresh(Request())
                    logger.info("gmail_token_refreshed")
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

    async def get_email_by_id(self, email_id: str) -> Dict[str, Any]:
        """
        Get full email details by ID.

        Args:
            email_id: The Gmail message ID

        Returns:
            Dict with full email details including body
        """
        if not self.available or not self.service:
            raise ServiceError(
                "Gmail is not configured. Please connect Gmail via Settings > Integrations."
            )

        try:
            # Get full message with body
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )

            headers = {
                h["name"].lower(): h["value"]
                for h in msg.get("payload", {}).get("headers", [])
            }

            # Extract body from payload
            body = ""
            payload = msg.get("payload", {})

            def extract_body(part: dict) -> str:
                """Recursively extract body from message parts."""
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                elif part.get("mimeType") == "text/html":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                elif "parts" in part:
                    for sub_part in part["parts"]:
                        result = extract_body(sub_part)
                        if result:
                            return result
                return ""

            # Check if body is directly in payload or in parts
            if "body" in payload and payload["body"].get("data"):
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
            elif "parts" in payload:
                body = extract_body(payload)

            return {
                "id": msg.get("id"),
                "threadId": msg.get("threadId"),
                "snippet": msg.get("snippet"),
                "subject": headers.get("subject", ""),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "cc": headers.get("cc", ""),
                "date": headers.get("date", ""),
                "body": body,
                "labelIds": msg.get("labelIds", []),
            }

        except HttpError as exc:
            logger.error("gmail_get_email_error", error=str(exc), email_id=email_id)
            raise ServiceError(f"Failed to get email: {exc}") from exc

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = False,
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API.

        Args:
            to: Recipient email address (comma-separated for multiple)
            subject: Email subject
            body: Email body (plain text or HTML)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: If True, treat body as HTML content

        Returns:
            Dict with message id and thread id
        """
        if not self.available or not self.service:
            raise ServiceError(
                "Gmail is not configured. Please connect Gmail via Settings > Integrations."
            )

        try:
            # Create message
            if html:
                message = MIMEMultipart("alternative")
                message.attach(MIMEText(body, "html"))
            else:
                message = MIMEText(body)

            message["to"] = to
            message["subject"] = subject

            if cc:
                message["cc"] = cc
            if bcc:
                message["bcc"] = bcc

            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            # Send the message
            sent_message = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            logger.info(
                "gmail_email_sent",
                message_id=sent_message.get("id"),
                to=to,
                subject=subject[:50],
            )

            return {
                "success": True,
                "message_id": sent_message.get("id"),
                "thread_id": sent_message.get("threadId"),
            }

        except HttpError as exc:
            logger.error("gmail_send_error", error=str(exc), to=to, subject=subject)
            raise ServiceError(f"Failed to send email: {exc}") from exc
