"""
Image Generation Service

Uses fal.ai FLUX.1 schnell model for fast image generation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.logger import logger


def generate_image(
    prompt: str,
    num_inference_steps: int = 4,
    image_size: str = "landscape_4_3",
) -> Dict[str, Any]:
    """
    Generate an image using FLUX.1 schnell model.

    Args:
        prompt: Text description of the image to generate
        num_inference_steps: Number of inference steps (1-4 for schnell)
        image_size: Image aspect ratio (square_hd, landscape_4_3, portrait_4_3, etc.)

    Returns:
        Dictionary with success status, image URL or error
    """
    from app.config import get_settings

    settings = get_settings()
    fal_key = getattr(settings, 'fal_key', '') or getattr(settings, 'FAL_KEY', '')

    if not fal_key:
        return {
            "success": False,
            "data": None,
            "error": "fal.ai API key not configured",
        }

    try:
        import os
        os.environ["FAL_KEY"] = fal_key

        import fal_client

        result = fal_client.subscribe(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": prompt,
                "num_inference_steps": num_inference_steps,
                "image_size": image_size,
                "num_images": 1,
                "enable_safety_checker": True,
            },
        )

        images = result.get("images", [])
        if images:
            image_url = images[0].get("url")
            return {
                "success": True,
                "data": {
                    "image_url": image_url,
                    "prompt": prompt,
                    "model": "flux-schnell",
                    "seed": result.get("seed"),
                    "timings": result.get("timings"),
                },
                "error": None,
            }
        else:
            return {
                "success": False,
                "data": None,
                "error": f"No images generated for prompt: '{prompt}'",
            }

    except ImportError:
        logger.error("fal-client package not installed")
        return {
            "success": False,
            "data": None,
            "error": "fal-client package not installed",
        }
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        return {
            "success": False,
            "data": None,
            "error": str(e),
        }


async def generate_image_async(
    prompt: str,
    num_inference_steps: int = 4,
    image_size: str = "landscape_4_3",
) -> Dict[str, Any]:
    """
    Async version of generate_image.

    Args:
        prompt: Text description of the image to generate
        num_inference_steps: Number of inference steps
        image_size: Image aspect ratio

    Returns:
        Dictionary with success status, image URL or error
    """
    from app.config import get_settings

    settings = get_settings()
    fal_key = getattr(settings, 'fal_key', '') or getattr(settings, 'FAL_KEY', '')

    if not fal_key:
        return {
            "success": False,
            "data": None,
            "error": "fal.ai API key not configured",
        }

    try:
        import os
        os.environ["FAL_KEY"] = fal_key

        import fal_client

        client = fal_client.AsyncClient()
        result = await client.subscribe(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": prompt,
                "num_inference_steps": num_inference_steps,
                "image_size": image_size,
                "num_images": 1,
                "enable_safety_checker": True,
            },
        )

        images = result.get("images", [])
        if images:
            image_url = images[0].get("url")
            return {
                "success": True,
                "data": {
                    "image_url": image_url,
                    "prompt": prompt,
                    "model": "flux-schnell",
                    "seed": result.get("seed"),
                    "timings": result.get("timings"),
                },
                "error": None,
            }
        else:
            return {
                "success": False,
                "data": None,
                "error": f"No images generated for prompt: '{prompt}'",
            }

    except ImportError:
        logger.error("fal-client package not installed")
        return {
            "success": False,
            "data": None,
            "error": "fal-client package not installed",
        }
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        return {
            "success": False,
            "data": None,
            "error": str(e),
        }
