"""
WhatsApp Webhook Handler.

Handles incoming webhooks from Meta WhatsApp Cloud API.
"""

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from whatsapp_bot.config import settings
from whatsapp_bot.graph import process_message
from common.whatsapp.client import get_whatsapp_client, initialize_whatsapp_client
from common.whatsapp.models import (
    WebhookPayload,
    extract_message,
    is_status_update,
)
from common.i18n.detector import detect_language
from common.services.stt_service import get_stt_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def verify_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature from Meta.

    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value

    Returns:
        True if signature is valid
    """
    if not settings.whatsapp_app_secret:
        logger.warning("WHATSAPP_APP_SECRET not configured, skipping verification")
        return True

    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = signature[7:]

    computed = hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed, expected_signature)


@router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
) -> PlainTextResponse:
    """
    Webhook verification endpoint for Meta.

    Meta sends a GET request with hub.mode, hub.challenge, and hub.verify_token
    to verify the webhook URL during setup.
    """
    if hub_mode == "subscribe":
        if hub_verify_token == settings.whatsapp_verify_token:
            logger.info("WhatsApp webhook verified successfully")
            return PlainTextResponse(content=hub_challenge or "", status_code=200)
        else:
            logger.warning(
                f"Webhook verification failed. Token mismatch. "
                f"Expected: {settings.whatsapp_verify_token}, Got: {hub_verify_token}"
            )
            raise HTTPException(status_code=403, detail="Verification token mismatch")

    logger.warning(f"Webhook verification failed. Invalid mode: {hub_mode}")
    raise HTTPException(status_code=400, detail="Invalid verification request")


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Main webhook endpoint for incoming messages.

    Meta sends POST requests with message events.
    We respond immediately with 200 and process in background.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()

        # Verify signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(body, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        payload_dict = await request.json()
        logger.debug(f"Received webhook payload: {payload_dict}")

        # Validate it's a WhatsApp webhook
        if payload_dict.get("object") != "whatsapp_business_account":
            logger.warning(f"Unknown webhook object: {payload_dict.get('object')}")
            return {"status": "ignored"}

        # Parse with Pydantic model
        try:
            webhook_data = WebhookPayload(**payload_dict)
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return {"status": "parse_error"}

        # Skip status updates
        if is_status_update(webhook_data):
            logger.debug("Received status update, ignoring")
            return {"status": "status_update"}

        # Extract message
        message = extract_message(webhook_data)

        if message:
            # extract_message already returns a dict
            message_dict = message
            logger.info(
                f"Received message from {message_dict.get('from_number', 'unknown')}: "
                f"{(message_dict.get('text') or '[non-text]')[:50]}"
            )

            # Process message in background
            background_tasks.add_task(process_and_respond, message_dict)
        else:
            logger.debug("No message to process in webhook")

        # Always return 200 to acknowledge receipt
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def process_and_respond(message: dict) -> None:
    """
    Background task to process message and send response.

    Args:
        message: Extracted WhatsApp message dict
    """
    # Initialize WhatsApp client if needed
    try:
        client = get_whatsapp_client()
    except ValueError:
        client = initialize_whatsapp_client(
            access_token=settings.whatsapp_access_token,
            phone_number_id=settings.whatsapp_phone_number_id,
        )

    is_voice_input = message.get("message_type") == "audio"
    is_image_input = message.get("message_type") == "image"

    ctx_service = None
    try:
        # Record WhatsApp activity for admin analytics (best-effort)
        try:
            from ohgrt_api.services.context_service import get_context_service
            ctx_service = get_context_service()
            await ctx_service.record_whatsapp_activity(message.get("from_number", ""))
            await ctx_service.record_whatsapp_message(
                phone=message.get("from_number", ""),
                direction="incoming",
                text=message.get("text"),
                message_id=message.get("message_id"),
                raw_payload=message,
            )
        except Exception as e:
            logger.warning(f"Failed to record WhatsApp activity: {e}")

        # Mark message as read
        await client.mark_as_read(message["message_id"])

        # Handle voice messages
        if is_voice_input and message.get("media_id"):
            try:
                media_url = await client.get_media_url(message["media_id"])
                if media_url:
                    audio_bytes = await client.download_media(media_url)
                    if audio_bytes:
                        stt_service = get_stt_service()
                        transcribed = await stt_service.transcribe_bytes(audio_bytes)
                        if transcribed:
                            message["text"] = transcribed
                            logger.info(f"Transcribed: {transcribed[:50]}...")
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                message["text"] = "Voice message received"

        # Handle image messages
        if is_image_input and message.get("media_id"):
            try:
                media_url = await client.get_media_url(message["media_id"])
                if media_url:
                    image_bytes = await client.download_media(media_url)
                    if image_bytes:
                        message["image_bytes"] = image_bytes
            except Exception as e:
                logger.error(f"Image download failed: {e}", exc_info=True)

        # Send typing indicator
        try:
            await client.send_typing_indicator(
                to=message["from_number"],
                message_id=message["message_id"],
                duration=3,
            )
            logger.debug("Typing indicator sent")
        except Exception as e:
            logger.warning(f"Failed to send typing indicator: {e}")

        # Process through LangGraph
        result = await process_message(message)

        response_text = result.get("response_text", "")
        response_type = result.get("response_type", "text")

        # If input was voice and we have a text response, convert to voice
        if is_voice_input and response_text and response_type == "text":
            try:
                from common.services.tts_service import get_tts_service

                tts_service = get_tts_service()
                detected_lang = result.get("detected_language") or detect_language(response_text)
                audio_bytes = await tts_service.text_to_speech(
                    text=response_text,
                    language=detected_lang,
                )

                if audio_bytes:
                    mime_type = tts_service.get_audio_mime_type()
                    audio_id = await client.upload_media(
                        media_bytes=audio_bytes,
                        mime_type=mime_type,
                    )
                    if audio_id:
                        await client.send_audio_message(
                            to=message["from_number"],
                            audio_id=audio_id,
                            reply_to=message["message_id"],
                        )
                    else:
                        raise RuntimeError("Audio upload failed")
                    await client.send_text_message(
                        to=message["from_number"],
                        text=f"📝 {response_text}",
                    )
                    if ctx_service:
                        try:
                            await ctx_service.record_whatsapp_message(
                                phone=message.get("from_number", ""),
                                direction="outgoing",
                                text=response_text,
                                response_type="audio",
                                media_url=audio_id,
                            )
                        except Exception:
                            pass
                    return

            except ImportError as e:
                logger.warning(f"TTS service not available: {e}")
            except Exception as e:
                logger.error(f"TTS generation failed: {e}", exc_info=True)

        # Send response
        if response_type == "text" and response_text:
            await client.send_text_message(
                to=message["from_number"],
                text=response_text,
                reply_to=message["message_id"],
            )
            if ctx_service:
                try:
                    await ctx_service.record_whatsapp_message(
                        phone=message.get("from_number", ""),
                        direction="outgoing",
                        text=response_text,
                        response_type=response_type,
                    )
                except Exception:
                    pass
        elif response_type == "image" and result.get("response_media_url"):
            await client.send_image_message(
                to=message["from_number"],
                image_url=result["response_media_url"],
                caption=response_text,
                reply_to=message["message_id"],
            )
            if ctx_service:
                try:
                    await ctx_service.record_whatsapp_message(
                        phone=message.get("from_number", ""),
                        direction="outgoing",
                        text=response_text,
                        response_type=response_type,
                        media_url=result.get("response_media_url"),
                    )
                except Exception:
                    pass
        elif response_type == "interactive" and result.get("buttons"):
            await client.send_interactive_buttons(
                to=message["from_number"],
                body_text=response_text,
                buttons=result["buttons"],
            )
            if ctx_service:
                try:
                    await ctx_service.record_whatsapp_message(
                        phone=message.get("from_number", ""),
                        direction="outgoing",
                        text=response_text,
                        response_type=response_type,
                    )
                except Exception:
                    pass
        elif response_type == "location_request":
            # Send interactive location request button
            await client.request_location(
                to=message["from_number"],
                body_text=response_text,
            )
            if ctx_service:
                try:
                    await ctx_service.record_whatsapp_message(
                        phone=message.get("from_number", ""),
                        direction="outgoing",
                        text=response_text,
                        response_type=response_type,
                    )
                except Exception:
                    pass
        else:
            # Fallback to text if we have response text
            if response_text:
                await client.send_text_message(
                    to=message["from_number"],
                    text=response_text,
                    reply_to=message["message_id"],
                )
                if ctx_service:
                    try:
                        await ctx_service.record_whatsapp_message(
                            phone=message.get("from_number", ""),
                            direction="outgoing",
                            text=response_text,
                            response_type=response_type,
                        )
                    except Exception:
                        pass
            else:
                logger.warning(f"Unknown response type: {result}")

        logger.info(
            f"Response sent to {message['from_number']}, intent: {result.get('intent')}"
        )

    except Exception as e:
        logger.error(f"Error in process_and_respond: {e}", exc_info=True)

        try:
            await client.send_text_message(
                to=message["from_number"],
                text="Sorry, I encountered an error. Please try again.",
            )
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
