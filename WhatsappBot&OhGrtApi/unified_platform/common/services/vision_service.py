"""
Vision Service - Image Analysis using Qwen VL

Uses Qwen VL (Vision-Language) model via DashScope API.
Supports image description, OCR, object detection, and more.
"""

import logging
import base64
import httpx
import os
import io
from typing import Optional

from common.i18n.detector import get_language_name

logger = logging.getLogger(__name__)


def resize_image_for_model(image_bytes: bytes, max_size: int = 1024) -> bytes:
    """
    Resize image to fit within max_size while maintaining aspect ratio.
    This prevents Ollama from crashing with large WhatsApp images.

    Args:
        image_bytes: Original image bytes
        max_size: Maximum dimension (width or height)

    Returns:
        Resized image bytes (JPEG format)
    """
    try:
        from PIL import Image

        # Open image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        original_size = img.size

        # Convert to RGB if necessary (e.g., for PNG with transparency)
        if img.mode in ('RGBA', 'P', 'LA'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Check if resize is needed
        width, height = img.size
        if width <= max_size and height <= max_size:
            # Still convert to JPEG for consistency
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            logger.info(f"Image already within size limit: {width}x{height}")
            return output.getvalue()

        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)

        resized_bytes = output.getvalue()
        logger.info(
            f"Image resized: {original_size[0]}x{original_size[1]} -> {new_width}x{new_height}, "
            f"size: {len(image_bytes)} -> {len(resized_bytes)} bytes"
        )
        return resized_bytes

    except ImportError:
        logger.warning("PIL not installed, cannot resize image")
        return image_bytes
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return image_bytes

# DashScope API (Qwen official API)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

# Ollama as fallback
OLLAMA_BASE_URL = "http://localhost:11434"


class VisionService:
    """
    Vision service for image analysis using Qwen VL model.

    Primary: DashScope API (Qwen VL - Alibaba's official API)
    Fallback: Local Ollama models

    Supports:
    - Image description/captioning
    - Text extraction (OCR)
    - Object detection
    - Scene understanding
    - Document analysis
    """

    def __init__(self):
        self.dashscope_api_key = DASHSCOPE_API_KEY
        self.ollama_model = None

    def _get_prompt(self, analysis_type: str, custom_prompt: Optional[str] = None) -> str:
        """Get the appropriate prompt based on analysis type."""
        if custom_prompt:
            return custom_prompt

        prompts = {
            "describe": (
                "Describe this image in detail. Include:\n"
                "- Main subject or scene\n"
                "- Colors, objects, and people visible\n"
                "- Any text visible in the image\n"
                "- Context and setting\n"
                "Be concise but comprehensive."
            ),
            "ocr": (
                "Extract ALL text visible in this image. "
                "Preserve the layout and formatting as much as possible. "
                "If there are multiple text sections, separate them clearly. "
                "Only output the extracted text, no descriptions. "
                "Text may be in regional scripts (e.g., Kannada, Hindi, Tamil)."
            ),
            "objects": (
                "List all objects, items, and elements visible in this image. "
                "Format as a bullet list. Include:\n"
                "- Physical objects\n"
                "- People (if any)\n"
                "- Text/signs (if any)\n"
                "- Background elements"
            ),
            "document": (
                "This appears to be a document. Please:\n"
                "1. Extract all text content\n"
                "2. Identify the type of document\n"
                "3. Summarize key information\n"
                "4. Note any important dates, numbers, or names"
            ),
            "receipt": (
                "This is a receipt/bill. Extract:\n"
                "- Store/vendor name\n"
                "- Date and time\n"
                "- List of items with prices\n"
                "- Subtotal, tax, and total\n"
                "- Payment method (if visible)\n"
                "Format the information clearly."
            ),
            "food": (
                "Identify the food items in this image:\n"
                "- Name each dish/food item\n"
                "- Describe the cuisine type\n"
                "- Estimate portion size\n"
                "- Note any visible ingredients"
            ),
        }
        return prompts.get(analysis_type, prompts["describe"])

    def _apply_language_instruction(
        self,
        prompt: str,
        response_language: Optional[str],
        analysis_type: str,
    ) -> str:
        """Attach language instruction to prompt when appropriate."""
        if not response_language:
            return prompt
        if analysis_type == "ocr":
            return (
                f"{prompt}\n\nDo not translate. Preserve the original text language and formatting."
            )
        language_name = get_language_name(response_language, display_in="en")
        return f"{prompt}\n\nRespond in {language_name}."

    async def _analyze_with_dashscope(
        self, image_bytes: bytes, prompt: str
    ) -> Optional[str]:
        """Analyze image using DashScope Qwen VL API."""
        if not self.dashscope_api_key:
            logger.warning("DASHSCOPE_API_KEY not set")
            return None

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Detect image type from bytes
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            mime_type = "image/jpeg"
        else:
            mime_type = "image/jpeg"  # Default

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    DASHSCOPE_BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.dashscope_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "qwen-vl-plus",
                        "input": {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "image": f"data:{mime_type};base64,{image_base64}"
                                        },
                                        {
                                            "text": prompt
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", [])
                    if result and isinstance(result, list):
                        text_parts = [item.get("text", "") for item in result if "text" in item]
                        return " ".join(text_parts).strip()
                    return str(result).strip() if result else None
                else:
                    logger.error(f"DashScope API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"DashScope vision analysis failed: {e}")
            return None

    async def _analyze_with_ollama(
        self, image_bytes: bytes, prompt: str
    ) -> Optional[str]:
        """Analyze image using local Ollama Qwen VL model."""
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Try to find available vision model
        if not self.ollama_model:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                    if response.status_code == 200:
                        models = [m["name"] for m in response.json().get("models", [])]
                        # Prefer Qwen VL models
                        for m in ["qwen2.5vl:7b", "qwen3-vl:8b", "moondream:latest", "llava"]:
                            if m in models:
                                self.ollama_model = m
                                break
            except Exception as e:
                logger.error(f"Failed to get Ollama models: {e}")
                return None

        if not self.ollama_model:
            logger.error("No vision model available in Ollama")
            return None

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "images": [image_base64],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1024,
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Ollama vision analysis failed: {e}")
            return None

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        analysis_type: str = "describe",
        response_language: Optional[str] = None,
        max_size: int = 1024,
    ) -> Optional[str]:
        """
        Analyze an image and return description/analysis.

        Args:
            image_bytes: Raw image bytes
            prompt: Custom prompt for analysis (optional)
            analysis_type: Type of analysis - describe, ocr, objects, document

        Returns:
            Analysis result text or None if failed
        """
        system_prompt = self._get_prompt(analysis_type, prompt)
        system_prompt = self._apply_language_instruction(
            system_prompt, response_language, analysis_type
        )

        # Resize image to prevent Ollama crashes with large WhatsApp images
        logger.info(f"Original image size: {len(image_bytes)} bytes")
        processed_bytes = resize_image_for_model(image_bytes, max_size=max_size)
        logger.info(f"Processed image size: {len(processed_bytes)} bytes")

        # Try DashScope (Qwen VL API) first
        if self.dashscope_api_key:
            result = await self._analyze_with_dashscope(processed_bytes, system_prompt)
            if result:
                logger.info("Image analyzed with Qwen VL (DashScope)")
                return result

        # Fallback to local Ollama
        result = await self._analyze_with_ollama(processed_bytes, system_prompt)
        if result:
            logger.info(f"Image analyzed with Ollama ({self.ollama_model})")
            return result

        logger.error("All vision backends failed")
        return None

    async def describe_image(self, image_bytes: bytes) -> Optional[str]:
        """Get a detailed description of the image."""
        return await self.analyze_image(image_bytes, analysis_type="describe")

    async def extract_text(self, image_bytes: bytes) -> Optional[str]:
        """Extract text (OCR) from the image."""
        return await self.analyze_image(image_bytes, analysis_type="ocr")

    async def detect_objects(self, image_bytes: bytes) -> Optional[str]:
        """List objects detected in the image."""
        return await self.analyze_image(image_bytes, analysis_type="objects")

    async def analyze_document(self, image_bytes: bytes) -> Optional[str]:
        """Analyze a document image."""
        return await self.analyze_image(image_bytes, analysis_type="document")

    async def analyze_receipt(self, image_bytes: bytes) -> Optional[str]:
        """Extract information from a receipt/bill."""
        return await self.analyze_image(image_bytes, analysis_type="receipt")

    async def identify_food(self, image_bytes: bytes) -> Optional[str]:
        """Identify food items in the image."""
        return await self.analyze_image(image_bytes, analysis_type="food")

    async def custom_query(
        self,
        image_bytes: bytes,
        question: str,
        response_language: Optional[str] = None,
    ) -> Optional[str]:
        """Ask a custom question about the image."""
        prompt = (
            "First, extract any visible text exactly as it appears (no translation). "
            "If no text is present, say 'No visible text found'. "
            f"Then answer the user's question: {question}"
        )
        return await self.analyze_image(
            image_bytes,
            prompt=prompt,
            response_language=response_language,
        )

    async def is_available(self) -> bool:
        """Check if vision service is available."""
        if self.dashscope_api_key:
            return True
        if self.ollama_model:
            return True
        # Try to detect a local Ollama vision model
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    models = [m["name"] for m in response.json().get("models", [])]
                    for m in ["qwen2.5vl:7b", "qwen3-vl:8b", "moondream:latest", "llava"]:
                        if m in models:
                            self.ollama_model = m
                            return True
        except Exception as e:
            logger.warning(f"Vision availability check failed: {e}")
        return False


# Singleton instance
_vision_service: Optional[VisionService] = None


def get_vision_service() -> VisionService:
    """Get or create singleton VisionService instance."""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionService()
    return _vision_service
