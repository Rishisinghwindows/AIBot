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
import re
from typing import Dict

from common.graph.state import BotState
from common.services.vision_service import get_vision_service
from common.i18n.detector import detect_language
from common.i18n.responses import get_image_analysis_label, get_image_label
from common.services.img2img_service import get_img2img_service
from whatsapp_bot.graph.context_cache import get_context as get_followup_context

logger = logging.getLogger(__name__)

INTENT = "image_analysis"

LANGUAGE_HINTS = {
    "english": "en",
    "hindi": "hi",
    "हिंदी": "hi",
    "tamil": "ta",
    "தமிழ்": "ta",
    "telugu": "te",
    "తెలుగు": "te",
    "kannada": "kn",
    "ಕನ್ನಡ": "kn",
    "marathi": "mr",
    "मराठी": "mr",
    "gujarati": "gu",
    "ગુજરાતી": "gu",
    "bengali": "bn",
    "bangla": "bn",
    "বাংলা": "bn",
    "punjabi": "pa",
    "ਪੰਜਾਬੀ": "pa",
    "malayalam": "ml",
    "മലയാളം": "ml",
    "odia": "or",
    "oriya": "or",
    "ଓଡ଼ିଆ": "or",
}

TRANSLATE_KEYWORDS = {
    "translate", "translation", "convert", "convert to",
    "anuvad", "bhaashantar", "bhavantar", "भाषांतर", "अनुवाद",
}


def _looks_like_hinglish(text: str) -> bool:
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    if not tokens:
        return False
    hints = {
        "mujhe", "batao", "bata", "ka", "ki", "kya", "kyun", "hai", "nahi",
        "aap", "tum", "mera", "meri", "hum", "hain", "mein", "kaise",
        "ke", "me", "bare", "baare", "detail", "details",
    }
    return sum(1 for t in tokens if t in hints) >= 2


def _detect_language_from_caption(caption: str) -> str:
    if not caption:
        return "en"
    caption_lower = caption.lower()
    for key, code in LANGUAGE_HINTS.items():
        if key.lower() in caption_lower:
            return code
    detected = detect_language(caption)
    if detected == "en" and _looks_like_hinglish(caption):
        return "hi"
    return detected


def _wants_translation(caption: str) -> bool:
    if not caption:
        return False
    caption_lower = caption.lower()
    if any(kw in caption_lower for kw in TRANSLATE_KEYWORDS):
        return True
    # Common phrasing like "hindi me batao" or "kannada me batao"
    if any(lang in caption_lower for lang in LANGUAGE_HINTS.keys()) and (" me " in caption_lower or " में " in caption_lower):
        return True
    return False


def _is_description_request(caption: str) -> bool:
    if not caption:
        return False
    caption_lower = caption.lower()
    describe_keywords = [
        "describe", "details", "detail", "about image", "about photo",
        "image ke bare", "image ke baare", "photo ke bare", "photo ke baare",
        "tasveer ke bare", "tasveer ke baare", "image ka detail", "photo ka detail",
        "batao", "kya hai", "what is there", "what's there",
        "verify", "verify image", "verify this image",
    ]
    return any(kw in caption_lower for kw in describe_keywords)


def _is_no_text(result: str) -> bool:
    if not result:
        return False
    normalized = result.strip().lower()
    return normalized in {
        "no_text",
        "no text",
        "no visible text found",
        "no visible text",
        "no text found",
    }


def _wants_shinchan_style(caption: str) -> bool:
    if not caption:
        return False
    caption_lower = caption.lower()
    return any(
        kw in caption_lower
        for kw in [
            "shinchan",
            "shin-chan",
            "shin chan",
            "sinchan",
            "shinchan style",
            "shinchan-style",
            "shinchan this image",
            "shinchan this photo",
            "shinchan this pic",
            "shinchan this",
            "make shinchan",
            "convert to shinchan",
            "convert into shinchan",
            "shinchanify",
        ]
    )


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
    if any(kw in caption_lower for kw in [
        "text", "extract", "read", "ocr", "words",
        "what is written", "what's written", "read the text",
        "पढ़", "लिख", "क्या लिखा", "क्या लिखा है", "लिखा हुआ", "टेक्स्ट",
        "kya likha", "kya likha hai", "likha hai", "likha hua", "text batao",
        "padh", "padh lo", "likha kya hai",
    ]):
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


async def _extract_text_with_fallback(vision_service, image_bytes: bytes) -> str:
    result = await vision_service.analyze_image(
        image_bytes=image_bytes,
        analysis_type="ocr",
        max_size=1600,
    )
    if result and not _is_no_text(result):
        return result

    strict_prompt = (
        "You are an OCR engine. Extract every visible character exactly as shown. "
        "Preserve line breaks and punctuation. "
        "If absolutely no text is present, reply ONLY with 'NO_TEXT'. "
        "Text may be in Kannada, Hindi, Tamil, Telugu, Gujarati, Bengali, Malayalam, Odia, Punjabi, or English."
    )
    result = await vision_service.analyze_image(
        image_bytes=image_bytes,
        prompt=strict_prompt,
        analysis_type="describe",
        max_size=1600,
    )
    if result and not _is_no_text(result):
        return result

    return result or ""


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
    if caption and detected_lang == "en":
        detected_lang = _detect_language_from_caption(caption)

    # Handle follow-up text queries about the last image without re-upload.
    entities = state.get("extracted_entities", {}) or {}
    if not image_bytes and entities.get("use_last_image"):
        phone = whatsapp_message.get("from_number", "")
        cached = get_followup_context(phone) if phone else None
        last_tool = (cached or {}).get("last_tool_result") or {}
        last_result = last_tool.get("result")
        last_type = last_tool.get("analysis_type") or "ocr"
        if last_result:
            emoji_map = {
                "describe": "📷",
                "ocr": "📄",
                "food": "🍽️",
                "document": "📋",
                "receipt": "🧾",
            }
            emoji = emoji_map.get(last_type, "📷")
            label = get_image_analysis_label(last_type, detected_lang)
            prefix = f"{emoji} *{label}*\n\n"
            return {
                "response_text": f"{prefix}{last_result}",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "detected_language": detected_lang,
            }

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
        if not await vision_service.is_available():
            not_configured = get_image_analysis_label("not_configured", detected_lang)
            return {
                "response_text": not_configured,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        # Shinchan-style image generation from an input image
        if _wants_shinchan_style(caption):
            shinchan_prompt = (
                "Shinchan-inspired 2D cartoon illustration, bold outlines, flat colors, "
                "cute proportions. No text or watermark."
            )
            try:
                img2img_service = get_img2img_service()
                image_bytes_out = await img2img_service.generate(
                    image_bytes=image_bytes,
                    prompt=shinchan_prompt,
                    strength=0.6,
                    guidance_scale=7.0,
                    num_steps=25,
                )
            except Exception as exc:
                logger.error(f"Shinchan img2img failed: {exc}")
                error_msg = get_image_label("error", detected_lang)
                return {
                    "response_text": error_msg,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "detected_language": detected_lang,
                    "error": str(exc),
                }

            success_msg = get_image_label("success", detected_lang)
            return {
                "response_text": success_msg,
                "response_type": "image",
                "response_media_bytes": image_bytes_out,
                "response_media_mime": "image/png",
                "should_fallback": False,
                "intent": INTENT,
                "detected_language": detected_lang,
            }

        # Detect analysis type from caption
        analysis_type = _detect_analysis_type(caption)
        wants_translation = _wants_translation(caption)

        logger.info(f"Analyzing image with type: {analysis_type}, caption: {caption[:50] if caption else 'none'}")

        # Perform analysis
        if wants_translation:
            extracted = await _extract_text_with_fallback(vision_service, image_bytes)
            if extracted and _is_no_text(extracted):
                extracted = ""
            if not extracted:
                no_text = get_image_analysis_label("no_text", detected_lang)
                return {
                    "response_text": no_text,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "detected_language": detected_lang,
                }
            if detected_lang != "en":
                try:
                    from common.services.ai_language_service import ai_translate_response
                    result = await ai_translate_response(
                        text=extracted,
                        target_language=detected_lang,
                    )
                except Exception:
                    result = extracted
            else:
                result = extracted
        elif analysis_type == "ocr":
            result = await _extract_text_with_fallback(vision_service, image_bytes)
            if result and _is_no_text(result):
                result = ""

            if not result:
                no_text = get_image_analysis_label("no_text", detected_lang)
                return {
                    "response_text": no_text,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "detected_language": detected_lang,
                }

            if detected_lang != "en":
                try:
                    from common.services.ai_language_service import ai_translate_response
                    result = await ai_translate_response(
                        text=result,
                        target_language=detected_lang,
                    )
                except Exception:
                    pass
        elif caption and not _is_description_request(caption) and not any(
            kw in caption.lower() for kw in ["extract", "read", "food", "receipt", "document", "ocr", "text"]
        ):
            # User asked a specific question about the image
            result = await vision_service.custom_query(
                image_bytes,
                caption,
                response_language=detected_lang,
            )
        else:
            result = await vision_service.analyze_image(
                image_bytes=image_bytes,
                analysis_type=analysis_type,
                response_language=detected_lang,
            )

        if result:
            if wants_translation and _is_no_text(result):
                no_text = get_image_analysis_label("no_text", detected_lang)
                return {
                    "response_text": no_text,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "detected_language": detected_lang,
                }
            # Format response based on analysis type (localized)
            emoji_map = {
                "describe": "📷",
                "ocr": "📄",
                "food": "🍽️",
                "document": "📋",
                "receipt": "🧾",
            }
            emoji = emoji_map.get(analysis_type, "📷")
            label_key = "translate" if wants_translation else analysis_type
            label = get_image_analysis_label(label_key, detected_lang)
            prefix = f"{emoji} *{label}*\n\n"

            return {
                "response_text": f"{prefix}{result}",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "detected_language": detected_lang,
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
                "detected_language": detected_lang,
            }

    except Exception as e:
        logger.error(f"Image analysis error: {e}", exc_info=True)
        error_msg = get_image_analysis_label("error", detected_lang)
        return {
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "detected_language": detected_lang,
            "error": str(e),
        }
