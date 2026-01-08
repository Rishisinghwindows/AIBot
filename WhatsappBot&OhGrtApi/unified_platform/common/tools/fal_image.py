"""
fal.ai Image Generation Tool

Wrapper for fal.ai FLUX.1 schnell model for fast image generation.
"""

from typing import Optional, Union
from common.config.settings import settings, configure_fal
from common.graph.state import ToolResult
import fal_client

def _make_image_generation_request(
    prompt: str,
    num_inference_steps: int = 4,
    image_size: str = "landscape_4_3",
    client: Optional[Union[fal_client, fal_client.AsyncClient]] = None,
) -> ToolResult:
    """
    Generate an image using FLUX.1 schnell model.

    Args:
        prompt: Text description of the image to generate
        num_inference_steps: Number of inference steps (1-4 for schnell)
        image_size: Image aspect ratio (square_hd, landscape_4_3, portrait_4_3, etc.)
        client: Optional fal_client or fal_client.AsyncClient instance

    Returns:
        ToolResult with image URL or error
    """
    if not settings.FAL_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="fal.ai API key not configured",
            tool_name="fal_image",
        )

    # Ensure FAL_KEY is in environment
    configure_fal()

    try:
        if client:
            result = client.subscribe(
                "fal-ai/flux/schnell",
                arguments={
                    "prompt": prompt,
                    "num_inference_steps": num_inference_steps,
                    "image_size": image_size,
                    "num_images": 1,
                    "enable_safety_checker": True,
                },
            )
        else:
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
            return ToolResult(
                success=True,
                data={
                    "image_url": image_url,
                    "prompt": prompt,
                    "model": "flux-schnell",
                    "seed": result.get("seed"),
                    "timings": result.get("timings"),
                },
                error=None,
                tool_name="fal_image",
            )
        else:
            return ToolResult(
                success=False,
                data=None,
                error=f"No images generated for prompt: '{prompt}'",
                tool_name="fal_image",
            )

    except ImportError:
        return ToolResult(
            success=False,
            data=None,
            error="fal-client package not installed",
            tool_name="fal_image",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="fal_image",
        )


def generate_image(
    prompt: str,
    num_inference_steps: int = 4,
    image_size: str = "landscape_4_3",
) -> ToolResult:
    """
    Generate an image using FLUX.1 schnell model.

    Args:
        prompt: Text description of the image to generate
        num_inference_steps: Number of inference steps (1-4 for schnell)
        image_size: Image aspect ratio (square_hd, landscape_4_3, portrait_4_3, etc.)

    Returns:
        ToolResult with image URL or error
    """
    return _make_image_generation_request(
        prompt=prompt,
        num_inference_steps=num_inference_steps,
        image_size=image_size,
    )


async def generate_image_async(
    prompt: str,
    num_inference_steps: int = 4,
    image_size: str = "landscape_4_3",
) -> ToolResult:
    """
    Async version of generate_image.

    Args:
        prompt: Text description of the image to generate
        num_inference_steps: Number of inference steps
        image_size: Image aspect ratio

    Returns:
        ToolResult with image URL or error
    """
    try:
        client = fal_client.AsyncClient()
        return await _make_image_generation_request(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            image_size=image_size,
            client=client,
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="fal_image",
        )
