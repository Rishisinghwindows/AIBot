"""
WhatsApp Webhook Handlers

Handles incoming webhooks from Meta WhatsApp Cloud API.
"""

import logging
import hashlib
import hmac
from typing import Optional

from fastapi import APIRouter, Request, Query, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.whatsapp.client import get_whatsapp_client
from app.whatsapp.models import WebhookPayload, extract_message, is_status_update
from app.graph.whatsapp_graph import process_whatsapp_message


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
    settings = get_settings()

    if not settings.whatsapp_app_secret:
        # Skip verification if app secret not configured
        logger.warning("WHATSAPP_APP_SECRET not configured, skipping signature verification")
        return True

    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = signature[7:]  # Remove "sha256=" prefix

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
    settings = get_settings()

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

        # Skip status updates (delivered, read, etc.)
        if is_status_update(webhook_data):
            logger.debug("Received status update, ignoring")
            return {"status": "status_update"}

        # Extract message
        message = extract_message(webhook_data)

        if message:
            logger.info(
                f"Received message from {message.from_number}: "
                f"{(message.text or '[non-text]')[:50]}"
            )

            # Process message in background to respond quickly
            background_tasks.add_task(process_and_respond, message.to_dict())
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


async def transcribe_audio(client: "WhatsAppClient", media_id: str) -> Optional[str]:
    """
    Download and transcribe WhatsApp audio message.

    Args:
        client: WhatsApp client instance
        media_id: WhatsApp media ID

    Returns:
        Transcribed text or None if failed
    """
    try:
        from app.config import get_settings
        import openai
        import io

        settings = get_settings()

        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured for transcription")
            return None

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

        # Transcribe using OpenAI Whisper
        openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "voice_message.ogg"

        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

        transcribed_text = transcription.text.strip()
        logger.info(f"Audio transcribed: {transcribed_text[:100]}...")
        return transcribed_text

    except Exception as e:
        logger.error(f"Audio transcription failed: {e}", exc_info=True)
        return None


async def process_and_respond(message: dict):
    """
    Background task to process message and send response.

    Args:
        message: Extracted WhatsApp message dict
    """
    client = get_whatsapp_client()

    # Check if input was a voice message
    is_voice_input = message.get("message_type") == "audio"

    try:
        # Mark message as read
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

        # Send typing indicator (react with hourglass)
        try:
            await client.send_reaction(
                to=message["from_number"],
                message_id=message["message_id"],
                emoji="⏳",
            )
        except Exception as e:
            logger.warning(f"Failed to send typing reaction: {e}")

        # Process through LangGraph workflow
        result = await process_whatsapp_message(message)

        # Remove typing indicator
        try:
            await client.send_reaction(
                to=message["from_number"],
                message_id=message["message_id"],
                emoji="",  # Empty emoji removes reaction
            )
        except Exception as e:
            logger.warning(f"Failed to remove typing reaction: {e}")

        response_text = result.get("response_text", "")
        response_type = result.get("response_type", "text")

        # If input was voice and we have a text response, convert to voice
        if is_voice_input and response_text and response_type == "text":
            try:
                from app.services.tts_service import get_tts_service
                from app.i18n import detect_language

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
        elif response_type == "image" and result.get("response_media_url"):
            await client.send_image_message(
                to=message["from_number"],
                image_url=result["response_media_url"],
                caption=response_text,
                reply_to=message["message_id"],
            )
        elif response_type == "audio" and result.get("response_media_url"):
            await client.send_audio_message(
                to=message["from_number"],
                audio_url=result["response_media_url"],
                reply_to=message["message_id"],
            )
        elif response_type == "interactive" and result.get("buttons"):
            await client.send_interactive_buttons(
                to=message["from_number"],
                body_text=response_text,
                buttons=result["buttons"],
                reply_to=message["message_id"],
            )
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


