"""
WhatsApp Cloud API Client

Handles sending messages via Meta WhatsApp Cloud API.
"""

import httpx
import logging
from typing import Optional, List

from app.config import get_settings


logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"


class WhatsAppClient:
    """Client for WhatsApp Cloud API."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
    ):
        """
        Initialize WhatsApp client.

        Args:
            access_token: WhatsApp API access token (defaults to settings)
            phone_number_id: WhatsApp phone number ID (defaults to settings)
        """
        settings = get_settings()
        self.access_token = access_token or settings.whatsapp_access_token
        self.phone_number_id = phone_number_id or settings.whatsapp_phone_number_id
        self.api_url = f"{WHATSAPP_API_URL}/{self.phone_number_id}/messages"

    def _get_headers(self) -> dict:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        to: str,
        text: str,
        preview_url: bool = False,
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Send a text message.

        Args:
            to: Recipient phone number (with country code, no + or spaces)
            text: Message text (max 4096 characters)
            preview_url: Whether to show URL previews
            reply_to: Message ID to reply to (optional)

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": preview_url, "body": text[:4096]},
        }

        if reply_to:
            payload["context"] = {"message_id": reply_to}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            result = response.json()

            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {result}")

            return result

    async def send_image_message(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Send an image message via URL.

        Args:
            to: Recipient phone number
            image_url: Public URL of the image
            caption: Optional caption (max 1024 characters)
            reply_to: Message ID to reply to (optional)

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {"link": image_url},
        }

        if caption:
            payload["image"]["caption"] = caption[:1024]

        if reply_to:
            payload["context"] = {"message_id": reply_to}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            result = response.json()

            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {result}")

            return result

    async def send_audio_message(
        self,
        to: str,
        audio_url: str,
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Send an audio message via URL.

        Args:
            to: Recipient phone number
            audio_url: Public URL of the audio file
            reply_to: Message ID to reply to (optional)

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
            "audio": {"link": audio_url},
        }

        if reply_to:
            payload["context"] = {"message_id": reply_to}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            result = response.json()

            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {result}")

            return result

    async def send_document_message(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Send a document message via URL.

        Args:
            to: Recipient phone number
            document_url: Public URL of the document
            filename: Display filename
            caption: Optional caption
            reply_to: Message ID to reply to (optional)

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
            },
        }

        if caption:
            payload["document"]["caption"] = caption[:1024]

        if reply_to:
            payload["context"] = {"message_id": reply_to}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            result = response.json()

            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {result}")

            return result

    async def send_reaction(
        self,
        to: str,
        message_id: str,
        emoji: str,
    ) -> dict:
        """
        Send a reaction to a message.

        Args:
            to: Recipient phone number
            message_id: ID of the message to react to
            emoji: Emoji character (empty string removes reaction)

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "reaction",
            "reaction": {
                "message_id": message_id,
                "emoji": emoji,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            return response.json()

    async def mark_as_read(self, message_id: str) -> dict:
        """
        Mark a message as read.

        Args:
            message_id: ID of the message to mark as read

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            return response.json()

    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Send an interactive button message.

        Args:
            to: Recipient phone number
            body_text: Main message body
            buttons: List of button dicts with "id" and "title" keys (max 3)
            header_text: Optional header text
            footer_text: Optional footer text
            reply_to: Message ID to reply to (optional)

        Returns:
            API response dict
        """
        button_items = [
            {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
            for b in buttons[:3]
        ]

        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": button_items},
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if reply_to:
            payload["context"] = {"message_id": reply_to}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            return response.json()

    async def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Send an interactive list message.

        Args:
            to: Recipient phone number
            body_text: Main message body
            button_text: Button text to open the list
            sections: List of section dicts with "title" and "rows" keys
            header_text: Optional header text
            footer_text: Optional footer text
            reply_to: Message ID to reply to (optional)

        Returns:
            API response dict
        """
        interactive = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text[:20],
                "sections": sections[:10],  # Max 10 sections
            },
        }

        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}

        if footer_text:
            interactive["footer"] = {"text": footer_text}

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        if reply_to:
            payload["context"] = {"message_id": reply_to}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            return response.json()

    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get the download URL for a media file.

        Args:
            media_id: WhatsApp media ID

        Returns:
            Download URL or None if failed
        """
        url = f"{WHATSAPP_API_URL}/{media_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("url")

            logger.error(f"Failed to get media URL: {response.text}")
            return None

    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media content from WhatsApp.

        Args:
            media_url: URL from get_media_url

        Returns:
            Media bytes or None if failed
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                media_url,
                headers=self._get_headers(),
            )

            if response.status_code == 200:
                return response.content

            logger.error(f"Failed to download media: {response.status_code}")
            return None


# Singleton instance
_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create WhatsApp client singleton."""
    global _client
    if _client is None:
        _client = WhatsAppClient()
    return _client
