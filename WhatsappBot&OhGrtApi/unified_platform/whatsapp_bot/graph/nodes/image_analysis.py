"""
Image Analysis Node.

Handles incoming image messages and analyzes them using the vision service.
Supports multilingual responses (11+ Indian languages).
Supports:
- Image description
- Text extraction (OCR)
- Food identification
- Document analysis
- Receipt reading
"""

import logging
from typing import Dict

from common.graph.state import BotState
from common.services.vision_service import get_vision_service
from common.i18n.responses import get_image_analysis_label

logger = logging.getLogger(__name__)

INTENT = "image_analysis"


def _detect_analysis_type(caption: str) -> str:
    """
    Detect the type of analysis requested from the caption.

    Args:
        caption: Image caption or user query

    Returns:
        Analysis type: describe, ocr, food, document, receipt
    """
    caption_lower = caption.lower() if caption else ""

    # OCR/Text extraction
    if any(kw in caption_lower for kw in ["text", "extract", "read", "ocr", "words", "पढ़", "लिख"]):
        return "ocr"

    # Food identification
    if any(kw in caption_lower for kw in ["food", "dish", "meal", "recipe", "खाना", "खाद्य", "भोजन"]):
        return "food"

    # Receipt/Bill
    if any(kw in caption_lower for kw in ["receipt", "bill", "invoice", "रसीद", "बिल"]):
        return "receipt"

    # Document
    if any(kw in caption_lower for kw in ["document", "doc", "form", "certificate", "दस्तावेज़"]):
        return "document"

    # Default to description
    return "describe"


async def handle_image_analysis(state: BotState) -> Dict:
    """
    Handle incoming image messages and analyze them.
    Returns response in user's detected language.

    Args:
        state: Current bot state with image data

    Returns:
        State update with analysis result
    """
    whatsapp_message = state.get("whatsapp_message", {})
    detected_lang = state.get("detected_language", "en")

    # Get image bytes - either pre-loaded (test interface) or from WhatsApp
    image_bytes = whatsapp_message.get("image_bytes")
    caption = whatsapp_message.get("caption", "") or whatsapp_message.get("text", "") or ""

    if not image_bytes:
        # Try to get image from media_id (would need WhatsApp download)
        media_id = whatsapp_message.get("media_id")
        if media_id:
            # In production, we'd download from WhatsApp here
            processing_msg = get_image_analysis_label("processing", detected_lang)
            return {
                "response_text": processing_msg,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            send_image = get_image_analysis_label("send_image", detected_lang)
            return {
                "response_text": send_image,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    try:
        vision_service = get_vision_service()

        # Detect analysis type from caption
        analysis_type = _detect_analysis_type(caption)

        logger.info(f"Analyzing image with type: {analysis_type}, caption: {caption[:50] if caption else 'none'}")

        # Perform analysis
        if caption and not any(kw in caption.lower() for kw in ["describe", "extract", "read", "food", "receipt", "document"]):
            # User asked a specific question about the image
            result = await vision_service.custom_query(image_bytes, caption)
        else:
            result = await vision_service.analyze_image(
                image_bytes=image_bytes,
                analysis_type=analysis_type
            )

        if result:
            # Format response based on analysis type (localized)
            emoji_map = {
                "describe": "📷",
                "ocr": "📄",
                "food": "🍽️",
                "document": "📋",
                "receipt": "🧾",
            }
            emoji = emoji_map.get(analysis_type, "📷")
            label = get_image_analysis_label(analysis_type, detected_lang)
            prefix = f"{emoji} *{label}*\n\n"

            return {
                "response_text": f"{prefix}{result}",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "tool_result": {
                    "analysis_type": analysis_type,
                    "result": result,
                },
            }
        else:
            error_msg = get_image_analysis_label("error", detected_lang)
            return {
                "response_text": error_msg,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Image analysis error: {e}", exc_info=True)
        error_msg = get_image_analysis_label("error", detected_lang)
        return {
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
