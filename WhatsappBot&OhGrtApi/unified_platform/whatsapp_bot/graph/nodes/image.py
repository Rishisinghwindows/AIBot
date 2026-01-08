"""
Image Generation Node.

Handles AI image generation requests.
Supports multilingual responses (11+ Indian languages).
"""

import logging
import re
from typing import Dict

from common.graph.state import BotState
from common.services.image_service import ImageService
from common.i18n.responses import get_image_label, get_phrase

logger = logging.getLogger(__name__)

INTENT = "image"


def extract_prompt(text: str) -> str:
    """
    Extract image generation prompt from text.

    Args:
        text: User message

    Returns:
        Cleaned prompt
    """
    # Remove common trigger words
    trigger_words = [
        "generate", "create", "make", "draw", "image", "picture",
        "photo", "of", "a", "an", "the", "for me", "please",
    ]

    prompt = text.lower()
    for word in trigger_words:
        prompt = re.sub(rf'\b{word}\b', '', prompt, flags=re.IGNORECASE)

    return prompt.strip()


async def handle_image_generation(state: BotState) -> Dict:
    """
    Handle image generation requests.
    Returns response in user's detected language.

    Args:
        state: Current bot state

    Returns:
        State update with generated image
    """
    query = state.get("current_query", "")
    entities = state.get("extracted_entities", {})
    detected_lang = state.get("detected_language", "en")

    # Get prompt
    prompt = entities.get("prompt") or extract_prompt(query)

    if not prompt or len(prompt) < 3:
        describe = get_image_label("describe", detected_lang)
        return {
            "response_text": describe,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "route_log": state.get("route_log", []) + ["image:missing_prompt"],
        }

    try:
        from whatsapp_bot.config import settings

        if not settings.fal_key:
            return {
                "response_text": "Image generation service is not configured.",
                "response_type": "text",
                "should_fallback": True,
                "intent": INTENT,
            }

        # Initialize service
        image_service = ImageService(api_key=settings.fal_key)

        # Generate image
        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        image_url = await image_service.generate_image(prompt=prompt)

        if image_url:
            success_msg = get_image_label("success", detected_lang)
            return {
                "response_text": success_msg,
                "response_type": "image",
                "response_media_url": image_url,
                "should_fallback": False,
                "intent": INTENT,
                "tool_result": {"prompt": prompt, "url": image_url},
                "route_log": state.get("route_log", []) + ["image:success"],
            }
        else:
            error_msg = get_image_label("error", detected_lang)
            return {
                "response_text": error_msg,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "route_log": state.get("route_log", []) + ["image:no_url"],
            }

    except Exception as e:
        logger.error(f"Image generation error: {e}")
        error_msg = get_image_label("error", detected_lang)
        return {
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": True,
            "intent": INTENT,
            "error": str(e),
            "route_log": state.get("route_log", []) + ["image:error"],
        }
