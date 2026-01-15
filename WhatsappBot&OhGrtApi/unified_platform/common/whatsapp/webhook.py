"""
WhatsApp Webhook Handlers

Handles incoming webhooks from Meta WhatsApp Cloud API.
"""

import logging
import hashlib
import hmac
import io
from typing import Optional
import asyncio
from fastapi import APIRouter, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse

from common.config.settings import settings

from common.whatsapp.client import get_whatsapp_client, WhatsAppClient
from common.whatsapp.models import WebhookPayload, extract_message, is_status_update


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
    if not settings.WHATSAPP_APP_SECRET:
        # Skip verification if app secret not configured
        logger.warning("WHATSAPP_APP_SECRET not configured, skipping signature verification")
        return True

    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = signature[7:]  # Remove "sha256=" prefix

    computed = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"),
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
        if hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return PlainTextResponse(content=hub_challenge or "", status_code=200)
        else:
            logger.warning(
                f"Webhook verification failed. Token mismatch. "
                f"Expected: {settings.WHATSAPP_VERIFY_TOKEN}, Got: {hub_verify_token}"
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
        print(f"[WEBHOOK] Payload: {payload_dict}")  # Debug print

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

        # Skip status updates (delivered, read, etc.)
        if is_status_update(webhook_data):
            logger.debug("Received status update, ignoring")
            return {"status": "status_update"}

        # Extract message
        message = extract_message(webhook_data)

        if message:
            log_text = message.get('text', '[non-text]')[:50] if message.get('text') else f"[{message.get('message_type', 'unknown')}]"
            if message.get('message_type') == 'location':
                log_text = f"[location: {message.get('location')}]"
            logger.info(
                f"Received message from {message['from_number']}: {log_text}"
            )

            # Process message in background to respond quickly
            background_tasks.add_task(process_and_respond, message)
        else:
            logger.debug("No message to process in webhook")

        # Always return 200 to acknowledge receipt
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        # Still return 200 to prevent retries from Meta
        return {"status": "error", "message": str(e)}


async def transcribe_audio(client: WhatsAppClient, media_id: str) -> Optional[str]:
    """
    Download and transcribe WhatsApp audio message using local MLX Whisper.

    Args:
        client: WhatsApp client instance
        media_id: WhatsApp media ID

    Returns:
        Transcribed text or None if failed
    """
    try:
        from common.services.stt_service import get_stt_service

        # Get media URL from WhatsApp
        media_url = await client.get_media_url(media_id)
        if not media_url:
            logger.error("Failed to get media URL for transcription")
            return None

        # Download the audio
        audio_bytes = await client.download_media(media_url)
        if not audio_bytes:
            logger.error("Failed to download audio for transcription")
            return None

        # Transcribe using local MLX Whisper
        stt_service = get_stt_service()
        transcribed_text = await stt_service.transcribe_bytes(audio_bytes)

        if transcribed_text:
            logger.info(f"Audio transcribed (local): {transcribed_text[:100]}...")
            return transcribed_text
        else:
            logger.warning("Local transcription returned empty result")
            return None

    except ImportError as e:
        logger.warning(f"STT service not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}", exc_info=True)
        return None


def detect_language(text: str) -> str:
    """
    Detect language of text for TTS voice selection.

    Simple heuristic based on character ranges.
    """
    # Check for Devanagari (Hindi, Marathi, Sanskrit)
    if any('\u0900' <= c <= '\u097F' for c in text):
        return "hi"
    # Check for Tamil
    if any('\u0B80' <= c <= '\u0BFF' for c in text):
        return "ta"
    # Check for Telugu
    if any('\u0C00' <= c <= '\u0C7F' for c in text):
        return "te"
    # Check for Bengali
    if any('\u0980' <= c <= '\u09FF' for c in text):
        return "bn"
    # Check for Gujarati
    if any('\u0A80' <= c <= '\u0AFF' for c in text):
        return "gu"
    # Check for Kannada
    if any('\u0C80' <= c <= '\u0CFF' for c in text):
        return "kn"
    # Check for Malayalam
    if any('\u0D00' <= c <= '\u0D7F' for c in text):
        return "ml"
    # Check for Punjabi (Gurmukhi)
    if any('\u0A00' <= c <= '\u0A7F' for c in text):
        return "pa"
    # Default to English
    return "en"


async def process_and_respond(message: dict):
    """
    Background task to process message and send response.

    Args:
        message: Extracted WhatsApp message dict
    """
    from common.graph import process_message
    client = get_whatsapp_client()

    # Check if input was a voice message
    is_voice_input = message.get("message_type") == "audio"

    try:
        # Mark message as read (shows double blue tick ✓✓)
        await client.mark_as_read(message["message_id"])

        # If voice message, transcribe it first
        if is_voice_input and message.get("media_id"):
            transcribed_text = await transcribe_audio(client, message["media_id"])
            if transcribed_text:
                message["text"] = transcribed_text
                logger.info(f"Voice message transcribed: {transcribed_text[:50]}...")
            else:
                # Fallback message if transcription fails
                message["text"] = "Voice message received but could not be transcribed"

        # Send official typing indicator (shows "typing..." for 5 seconds)
        await client.send_typing_indicator(
            to=message["from_number"],
            message_id=message["message_id"],
            duration=5  # Show typing for 5 seconds
        )

        # Process through LangGraph
        result = await process_message(message)

        response_text = result.get("response_text", "")
        response_type = result.get("response_type", "text")

        # If input was voice and we have a text response, convert to voice
        if is_voice_input and response_text and response_type == "text":
            try:
                from common.services.tts_service import get_tts_service

                tts_service = get_tts_service()

                # Detect language of response for appropriate voice
                detected_lang = detect_language(response_text)

                # Generate audio URL
                audio_url = await tts_service.text_to_speech_url(
                    text=response_text,
                    language=detected_lang,
                )

                if audio_url:
                    # Send voice response
                    await client.send_audio_message(
                        to=message["from_number"],
                        audio_url=audio_url,
                        reply_to=message["message_id"],
                    )
                    # Also send text as follow-up for reference
                    await client.send_text_message(
                        to=message["from_number"],
                        text=f"📝 {response_text}",
                    )
                    logger.info(
                        f"Voice response sent to {message['from_number']}, "
                        f"intent: {result.get('intent')}, language: {detected_lang}"
                    )
                    return

            except ImportError as e:
                logger.warning(f"TTS service not available: {e}")
            except Exception as e:
                logger.error(f"TTS generation failed: {e}", exc_info=True)
                # Fall through to text response

        # Send response based on type
        if response_type == "text" and response_text:
            await client.send_text_message(
                to=message["from_number"],
                text=response_text,
                reply_to=message["message_id"],
            )
        elif response_type == "image":
            media_bytes = result.get("response_media_bytes")
            if media_bytes:
                mime_type = result.get("response_media_mime", "image/jpeg")
                media_id = await client.upload_media(media_bytes, mime_type=mime_type)
                if media_id:
                    await client.send_image_message(
                        to=message["from_number"],
                        image_id=media_id,
                        caption=response_text,
                        reply_to=message["message_id"],
                    )
                else:
                    logger.error("Image upload failed; falling back to text response.")
                    if response_text:
                        await client.send_text_message(
                            to=message["from_number"],
                            text=response_text,
                            reply_to=message["message_id"],
                        )
            elif result.get("response_media_url"):
                await client.send_image_message(
                    to=message["from_number"],
                    image_url=result["response_media_url"],
                    caption=response_text,
                    reply_to=message["message_id"],
                )
            else:
                logger.warning("Image response missing media URL/bytes.")
        elif response_type == "location_request" and response_text:
            # Send interactive location request message
            logger.info(f"Sending location request to {message['from_number']}")
            location_result = await client.request_location(
                to=message["from_number"],
                body_text=response_text,
            )
            logger.info(f"Location request result: {location_result}")
        else:
            logger.warning(f"Unknown response type or empty response: {result}")

        logger.info(
            f"Response sent to {message['from_number']}, intent: {result.get('intent')}"
        )

    except Exception as e:
        logger.error(f"Error in process_and_respond: {e}", exc_info=True)

        # Try to send error message to user
        try:
            await client.send_text_message(
                to=message["from_number"],
                text="Sorry, I encountered an error processing your message. Please try again.",
            )
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
