"""
Image Generation Node

Uses fal.ai FLUX.1 schnell model for fast image generation.
"""

import logging
import re
from bot.state import BotState
from bot.tools.fal_image import generate_image
from bot.utils.response_formatter import sanitize_error, create_service_error_response

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "image"


def _clean_prompt(prompt: str) -> str:
    """
    Clean the image prompt by removing common prefixes.

    Args:
        prompt: Raw user prompt

    Returns:
        Cleaned prompt suitable for image generation
    """
    # Common prefixes to remove
    prefixes_to_remove = [
        r"^generate\s+(an?\s+)?image\s+(of\s+)?",
        r"^create\s+(an?\s+)?image\s+(of\s+)?",
        r"^make\s+(an?\s+)?image\s+(of\s+)?",
        r"^generate\s+(an?\s+)?picture\s+(of\s+)?",
        r"^create\s+(an?\s+)?picture\s+(of\s+)?",
        r"^make\s+(an?\s+)?picture\s+(of\s+)?",
        r"^draw\s+(an?\s+)?",
        r"^paint\s+(an?\s+)?",
        r"^design\s+(an?\s+)?",
    ]

    clean = prompt.strip()
    for pattern in prefixes_to_remove:
        clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)

    return clean.strip() or prompt


def handle_image_generation(state: BotState) -> dict:
    """
    Node function: Generate image from text prompt.

    Args:
        state: Current bot state with extracted prompt

    Returns:
        Updated state with image URL or error
    """
    entities = state.get("extracted_entities", {})
    raw_prompt = entities.get("image_prompt", "") or state.get("current_query", "")

    if not raw_prompt:
        return {
            "response_text": (
                "*Image Generation*\n\n"
                "What image would you like me to generate?\n\n"
                "*Example:* Generate image of a sunset on the beach"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    # Clean the prompt
    clean_prompt = _clean_prompt(raw_prompt)

    if not clean_prompt or len(clean_prompt) < 3:
        return {
            "response_text": (
                "*Image Generation*\n\n"
                "Please provide a more detailed description for the image.\n\n"
                "*Tips:*\n"
                "- Be specific about colors, style, and mood\n"
                "- Describe the scene or subject clearly\n\n"
                "*Example:* A serene mountain lake at sunset with purple and orange sky"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    try:
        result = generate_image(clean_prompt)

        if result["success"]:
            image_url = result["data"].get("image_url")

            if image_url:
                return {
                    "tool_result": result,
                    "response_text": f"*Image Generated*\n\n_{clean_prompt}_",
                    "response_media_url": image_url,
                    "response_type": "image",
                    "should_fallback": False,
                    "intent": INTENT,
                }
            else:
                return {
                    "tool_result": result,
                    "response_text": (
                        "*Image Generation*\n\n"
                        "Image was created but couldn't be retrieved.\n\n"
                        "_Please try again with the same or a different description._"
                    ),
                    "response_type": "text",
                    "should_fallback": True,
                    "intent": INTENT,
                }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "image generation")
            return {
                "tool_result": result,
                "response_text": (
                    "*Image Generation*\n\n"
                    f"{user_message}\n\n"
                    "*Try:*\n"
                    "- A simpler description\n"
                    "- Different subject or style\n"
                    "- Avoiding complex scenes"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Image generation handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="Image Generation",
            raw_error=str(e)
        )
