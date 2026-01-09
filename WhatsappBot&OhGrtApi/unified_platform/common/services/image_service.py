"""
Image Generation Service.

Provides image generation using fal.ai.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ImageService:
    """Service for generating images using fal.ai."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://fal.run",
    ):
        """
        Initialize image service.

        Args:
            api_key: fal.ai API key
            base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=120.0,
                headers={
                    "Authorization": f"Key {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def generate_image(
        self,
        prompt: str,
        model: str = "fal-ai/flux/schnell",
        image_size: str = "square_hd",
        num_images: int = 1,
        **kwargs,
    ) -> Optional[str]:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image
            model: Model to use for generation
            image_size: Size preset (square_hd, landscape_4_3, portrait_4_3)
            num_images: Number of images to generate
            **kwargs: Additional model parameters

        Returns:
            URL of the generated image, or None if failed
        """
        if not self.api_key:
            raise ValueError("fal.ai API key not configured")

        client = await self._get_client()

        payload = {
            "prompt": prompt,
            "image_size": image_size,
            "num_images": num_images,
            "enable_safety_checker": True,
            **kwargs,
        }

        try:
            response = await client.post(
                f"{self.base_url}/{model}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            images = data.get("images", [])
            if images:
                return images[0].get("url")
            return None
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            raise

    async def generate_image_with_style(
        self,
        prompt: str,
        style: str = "realistic",
        **kwargs,
    ) -> Optional[str]:
        """
        Generate an image with a specific style.

        Args:
            prompt: Text description
            style: Style preset (realistic, anime, cartoon, artistic)
            **kwargs: Additional parameters

        Returns:
            URL of the generated image
        """
        style_prompts = {
            "realistic": "photorealistic, highly detailed, 8k resolution",
            "anime": "anime style, vibrant colors, studio ghibli inspired",
            "cartoon": "cartoon style, colorful, friendly",
            "artistic": "digital art, trending on artstation, masterpiece",
        }

        enhanced_prompt = f"{prompt}, {style_prompts.get(style, '')}"
        return await self.generate_image(prompt=enhanced_prompt, **kwargs)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Module-level service instance
_image_service: Optional[ImageService] = None


def get_image_service(api_key: Optional[str] = None) -> ImageService:
    """
    Get or create image service instance.

    Args:
        api_key: fal.ai API key

    Returns:
        ImageService instance
    """
    global _image_service
    if _image_service is None and api_key:
        _image_service = ImageService(api_key=api_key)
    elif _image_service is None:
        raise ValueError("Image service not initialized. Provide api_key.")
    return _image_service
