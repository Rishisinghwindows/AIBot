"""
Image Generation Node

Uses fal.ai FLUX.1 model for fast image generation.
"""

import re
import httpx
from ohgrt_api.graph.state import BotState
from ohgrt_api.config import get_settings
from ohgrt_api.logger import logger

INTENT = "image"


def _clean_prompt(prompt: str) -> str:
    """
    Clean the image prompt by removing common prefixes.

    Args:
        prompt: Raw user prompt

    Returns:
        Cleaned prompt suitable for image generation
    """
    # Common prefixes to remove (of/on/for/about/with are common prepositions)
    # Also handle "create X image" pattern (e.g., "create lion image")
    prefixes_to_remove = [
        r"^generate\s+(an?\s+)?image\s+(of|on|for|about|with)?\s*",
        r"^create\s+(an?\s+)?image\s+(of|on|for|about|with)?\s*",
        r"^make\s+(an?\s+)?image\s+(of|on|for|about|with)?\s*",
        r"^generate\s+(an?\s+)?picture\s+(of|on|for|about|with)?\s*",
        r"^create\s+(an?\s+)?picture\s+(of|on|for|about|with)?\s*",
        r"^make\s+(an?\s+)?picture\s+(of|on|for|about|with)?\s*",
        r"^draw\s+(an?\s+)?(image\s+|picture\s+)?(of|on|for|about|with)?\s*",
        r"^paint\s+(an?\s+)?(image\s+|picture\s+)?(of|on|for|about|with)?\s*",
        r"^design\s+(an?\s+)?(image\s+|picture\s+)?(of|on|for|about|with)?\s*",
    ]

    # Suffixes to remove (e.g., "lion image" -> "lion")
    suffixes_to_remove = [
        r"\s+image$",
        r"\s+picture$",
        r"\s+photo$",
        r"\s+pic$",
    ]

    clean = prompt.strip()

    # Handle "create/generate/make X image/picture" pattern first
    # e.g., "create lion image" -> "lion"
    alt_pattern = r"^(create|generate|make|draw|paint)\s+(.+?)\s+(image|picture|photo|pic)$"
    alt_match = re.match(alt_pattern, clean, re.IGNORECASE)
    if alt_match:
        clean = alt_match.group(2).strip()
    else:
        # Try standard prefix removal
        for pattern in prefixes_to_remove:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)

        # Remove trailing "image", "picture", etc.
        for pattern in suffixes_to_remove:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)

    return clean.strip() or prompt


async def generate_image_fal(prompt: str) -> dict:
    """
    Generate image using fal.ai API.

    Args:
        prompt: Image description

    Returns:
        Result dict with success, data, and error
    """
    settings = get_settings()

    if not settings.fal_key:
        return {
            "success": False,
            "error": "Image generation is not configured.",
            "tool_name": "image_gen"
        }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://fal.run/fal-ai/flux/schnell",
                headers={
                    "Authorization": f"Key {settings.fal_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt,
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 4,
                    "num_images": 1,
                    "enable_safety_checker": True,
                }
            )

            if response.status_code == 200:
                data = response.json()
                images = data.get("images", [])
                if images:
                    return {
                        "success": True,
                        "data": {"image_url": images[0].get("url")},
                        "tool_name": "image_gen"
                    }
                return {
                    "success": False,
                    "error": "No image generated",
                    "tool_name": "image_gen"
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "tool_name": "image_gen"
                }
    except Exception as e:
        logger.error(f"fal.ai image generation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "tool_name": "image_gen"
        }


async def handle_image_generation(state: BotState) -> dict:
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
                "Please provide a more detailed description.\n\n"
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
        result = await generate_image_fal(clean_prompt)

        if result.get("success"):
            image_url = result.get("data", {}).get("image_url")

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
                        "_Please try again._"
                    ),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }
        else:
            error = result.get("error", "Unknown error")
            logger.warning(f"Image generation failed: {error}")

            return {
                "tool_result": result,
                "response_text": (
                    "*Image Generation*\n\n"
                    "Could not generate image.\n\n"
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
        return {
            "response_text": (
                "*Image Generation*\n\n"
                "An error occurred while generating the image.\n\n"
                "_Please try again later._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
