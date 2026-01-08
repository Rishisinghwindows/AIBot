"""
WhatsApp Cloud API Client

Handles sending messages via Meta WhatsApp Cloud API.
"""

import httpx
import logging
from typing import Optional, List

from common.config.settings import settings


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
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
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
            
    async def send_typing_indicator(self, to: str, message_id: str, duration: float = 0) -> dict:
        """
        Send WhatsApp typing indicator (official Cloud API).

        Shows "typing..." under bot name for up to 25 seconds
        or until a reply is sent.

        API format per Meta's official docs:
        - Uses status endpoint with typing_indicator field
        - Automatically marks message as read (blue ticks)
        - Dismisses after 25 seconds or when response is sent

        Args:
            to: Recipient phone number
            message_id: Message ID to respond to
            duration: Optional delay in seconds to hold typing (default 0)
        """
        import asyncio

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "status": "read",
            "message_id": message_id,
            "typing_indicator": {
                "type": "text"
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )

            result = response.json()
            if response.status_code == 200:
                logger.info("Typing indicator sent successfully")
                # Hold typing for specified duration
                if duration > 0:
                    await asyncio.sleep(duration)
            else:
                logger.warning(f"Typing indicator error: {result}")

            return result

    # async def send_typing_indicator(self, to: str) -> dict:
    #     """
    #     Send typing indicator to recipient (shows "typing..." in chat).

    #     Args:
    #         to: Recipient phone number

    #     Returns:
    #         API response dict
    #     """
    #     payload = {
    #         "messaging_product": "whatsapp",
    #         "recipient_type": "individual",
    #         "to": to,
    #         "type": "text",
    #         "typing_indicator": {
    #             "type": "text",
    #         },
    #     }
        
    # async def send_typing_indicator(self, to: str, message_id: str) -> dict:
    #     """
    #     Show typing indicator ("typing...") in WhatsApp chat.

    #     WhatsApp Cloud API supports typing indicators via the messages endpoint.
    #     The typing indicator shows for up to 25 seconds or until a response is sent.

    #     API Endpoint: POST /{PHONE_NUMBER_ID}/messages
    #     Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/messages/

    #     Args:
    #         to: Recipient phone number
    #         message_id: The message ID to respond to (required for typing indicator)

    #     Returns:
    #         API response dict
    #     """
    #     if not message_id:
    #         logger.debug("No message_id provided for typing indicator, skipping")
    #         return {"status": "skipped", "reason": "no_message_id"}

    #     # WhatsApp Cloud API typing indicator format
    #     # Reference: Meta's official Postman collection
    #     payload = {
    #         "messaging_product": "whatsapp",
    #         "recipient_type": "individual",
    #         "to": to,
    #         "type": "reaction",
    #         "reaction": {
    #             "message_id": message_id,
    #             "emoji": ""  # Empty emoji to trigger presence/typing
    #         }
    #     }

    #     try:
    #         async with httpx.AsyncClient(timeout=10.0) as client:
    #             response = await client.post(
    #                 self.api_url,
    #                 headers=self._get_headers(),
    #                 json=payload,
    #             )
    #             result = response.json()

    #             # If reaction method fails, try status-based typing indicator
    #             if response.status_code != 200:
    #                 logger.debug(f"Reaction typing failed: {result}, trying status method")
    #                 return await self._send_typing_via_status(message_id)

    #             logger.debug(f"Typing indicator sent via reaction method")
    #             return result

    #     except Exception as e:
    #         logger.debug(f"Typing indicator failed: {e}")
    #         return {"error": str(e)}

    # async def _send_typing_via_status(self, message_id: str) -> dict:
    #     """
    #     Alternative method: Send typing indicator via status update.

    #     This uses the newer WhatsApp Cloud API status field.
    #     """
    #     payload = {
    #         "messaging_product": "whatsapp",
    #         "status": "read",  # Mark as read first
    #         "message_id": message_id,
    #     }

    #     try:
    #         async with httpx.AsyncClient(timeout=10.0) as client:
    #             response = await client.post(
    #                 self.api_url,
    #                 headers=self._get_headers(),
    #                 json=payload,
    #             )
    #             return response.json()
    #     except Exception as e:
    #         logger.debug(f"Status typing failed: {e}")
    #         return {"error": str(e)}

    async def request_location(
        self,
        to: str,
        body_text: str,
    ) -> dict:
        """
        Request user's location using interactive location request message.

        Args:
            to: Recipient phone number
            body_text: Message explaining why location is needed

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "location_request_message",
                "body": {"text": body_text},
                "action": {"name": "send_location"},
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            result = response.json()

            if response.status_code != 200:
                logger.error(f"Location request API error: {result}")

            return result

    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
    ) -> dict:
        """
        Send an interactive button message.

        Args:
            to: Recipient phone number
            body_text: Main message body
            buttons: List of button dicts with "id" and "title" keys (max 3)
            header_text: Optional header text
            footer_text: Optional footer text

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

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
            )
            return response.json()

    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get download URL for WhatsApp media.

        Args:
            media_id: WhatsApp media ID

        Returns:
            Media download URL or None
        """
        url = f"{WHATSAPP_API_URL}/{media_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                return data.get("url")
            else:
                logger.error(f"Failed to get media URL: {response.json()}")
                return None

    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media from WhatsApp CDN.

        Args:
            media_url: Media URL from get_media_url

        Returns:
            Media bytes or None
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                media_url,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )

            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to download media: {response.status_code}")
                return None

    async def upload_media(self, media_bytes: bytes, mime_type: str = "audio/mpeg") -> Optional[str]:
        """
        Upload media to WhatsApp servers and get a media ID.

        Args:
            media_bytes: Media file bytes
            mime_type: MIME type of the media

        Returns:
            Media ID or None if failed
        """
        upload_url = f"{WHATSAPP_API_URL}/{self.phone_number_id}/media"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    upload_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    data={"messaging_product": "whatsapp"},
                    files={"file": ("audio.mp3", media_bytes, mime_type)},
                )

                if response.status_code == 200:
                    data = response.json()
                    media_id = data.get("id")
                    logger.info(f"Media uploaded successfully, ID: {media_id}")
                    return media_id
                else:
                    logger.error(f"Media upload failed: {response.json()}")
                    return None

        except Exception as e:
            logger.error(f"Media upload error: {e}", exc_info=True)
            return None

    async def send_audio_message(
        self,
        to: str,
        audio_url: Optional[str] = None,
        audio_id: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Send an audio message via URL or media ID.

        Args:
            to: Recipient phone number
            audio_url: Public URL of the audio file (optional)
            audio_id: WhatsApp media ID (optional, preferred)
            reply_to: Message ID to reply to (optional)

        Returns:
            API response dict
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
        }

        # Prefer media ID over URL
        if audio_id:
            payload["audio"] = {"id": audio_id}
        elif audio_url:
            payload["audio"] = {"link": audio_url}
        else:
            logger.error("Either audio_url or audio_id must be provided")
            return {"error": "No audio source provided"}

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
                logger.error(f"WhatsApp API error sending audio: {result}")

            return result


# Singleton instance
_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create WhatsApp client singleton."""
    global _client
    if _client is None:
        _client = WhatsAppClient()
    return _client


def initialize_whatsapp_client(
    access_token: Optional[str] = None,
    phone_number_id: Optional[str] = None,
) -> WhatsAppClient:
    """
    Initialize the WhatsApp client singleton with custom credentials.

    Args:
        access_token: WhatsApp API access token
        phone_number_id: WhatsApp phone number ID

    Returns:
        Initialized WhatsApp client
    """
    global _client
    _client = WhatsAppClient(
        access_token=access_token,
        phone_number_id=phone_number_id,
    )
    return _client
