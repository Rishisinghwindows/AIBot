"""
Text-to-Speech Service

Converts text to audio using OpenAI TTS API.
Supports multiple languages and voices.
"""

import io
import hashlib
import logging
from typing import Optional, Literal
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

# Voice options for different languages/use cases
VoiceType = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# Language to voice mapping for best results
LANGUAGE_VOICE_MAP = {
    "hi": "nova",      # Hindi - Nova works well for Indian languages
    "ta": "nova",      # Tamil
    "te": "nova",      # Telugu
    "kn": "nova",      # Kannada
    "ml": "nova",      # Malayalam
    "mr": "nova",      # Marathi
    "bn": "nova",      # Bengali
    "gu": "nova",      # Gujarati
    "pa": "nova",      # Punjabi
    "or": "nova",      # Odia
    "en": "alloy",     # English - Alloy is clear and neutral
}


class TTSService:
    """Text-to-Speech service using OpenAI API."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def get_voice_for_language(self, language: str) -> VoiceType:
        """
        Get the best voice for a given language code.

        Args:
            language: ISO 639-1 language code (e.g., 'hi', 'en', 'ta')

        Returns:
            Voice name suitable for the language
        """
        return LANGUAGE_VOICE_MAP.get(language, "nova")

    async def text_to_speech(
        self,
        text: str,
        language: str = "en",
        voice: Optional[VoiceType] = None,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """
        Convert text to speech audio.

        Args:
            text: Text to convert (max 4096 chars)
            language: Language code for voice selection
            voice: Override voice selection
            speed: Speech speed (0.25 to 4.0)

        Returns:
            MP3 audio bytes or None if failed
        """
        if not self.settings.openai_api_key:
            logger.warning("OpenAI API key not configured for TTS")
            return None

        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for TTS")
            return None

        # Truncate if too long (OpenAI limit is 4096)
        text = text[:4096]

        # Select voice
        selected_voice = voice or self.get_voice_for_language(language)

        try:
            response = self.client.audio.speech.create(
                model="tts-1",  # Use tts-1-hd for higher quality
                voice=selected_voice,
                input=text,
                speed=speed,
                response_format="mp3",
            )

            # Get audio bytes
            audio_bytes = response.content

            logger.info(
                "tts_generated",
                text_length=len(text),
                language=language,
                voice=selected_voice,
                audio_size=len(audio_bytes),
            )

            return audio_bytes

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    async def text_to_speech_url(
        self,
        text: str,
        language: str = "en",
        voice: Optional[VoiceType] = None,
    ) -> Optional[str]:
        """
        Convert text to speech and upload to get a public URL.

        This is needed for WhatsApp which requires a public URL for audio.
        Uses a temporary file hosting service or cloud storage.

        Args:
            text: Text to convert
            language: Language code
            voice: Override voice

        Returns:
            Public URL to the audio file or None
        """
        audio_bytes = await self.text_to_speech(text, language, voice)

        if not audio_bytes:
            return None

        # Upload to temporary file hosting
        try:
            return await self._upload_audio(audio_bytes)
        except Exception as e:
            logger.error(f"Audio upload failed: {e}")
            return None

    async def _upload_audio(self, audio_bytes: bytes) -> Optional[str]:
        """
        Upload audio bytes to get a public URL.

        Uses file.io for temporary hosting (files expire after 1 download).
        For production, use S3, GCS, or similar.

        Args:
            audio_bytes: MP3 audio data

        Returns:
            Public URL or None
        """
        import httpx

        try:
            # Option 1: Use file.io for temporary hosting
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": ("response.mp3", audio_bytes, "audio/mpeg")}
                response = await client.post(
                    "https://file.io",
                    files=files,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        url = data.get("link")
                        logger.info(f"Audio uploaded to: {url}")
                        return url

                logger.warning(f"file.io upload failed: {response.text}")

        except Exception as e:
            logger.error(f"Audio upload error: {e}")

        # Option 2: If you have S3 configured, use that instead
        # return await self._upload_to_s3(audio_bytes)

        return None


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get or create TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
