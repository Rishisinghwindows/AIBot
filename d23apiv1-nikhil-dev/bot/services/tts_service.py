"""
Text-to-Speech Service

Converts text responses to audio using Edge TTS (free, open-source).
Supports 11+ Indian languages with natural voices.
"""

import logging
import httpx
import asyncio
import tempfile
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


def sanitize_text_for_tts(text: str) -> str:
    """
    Sanitize text for TTS processing.

    Removes emojis and special characters that may cause TTS to fail.
    """
    if not text:
        return ""

    # Remove emojis and special Unicode characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002300-\U000023FF"  # misc technical
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub(" ", text)

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text

# Language to Edge TTS voice mapping
# Edge TTS has excellent Indian language support with natural voices
LANGUAGE_VOICE_MAP = {
    # Indian Languages
    "hi": "hi-IN-SwaraNeural",       # Hindi (Female)
    "hi-male": "hi-IN-MadhurNeural", # Hindi (Male)
    "ta": "ta-IN-PallaviNeural",     # Tamil (Female)
    "ta-male": "ta-IN-ValluvarNeural", # Tamil (Male)
    "te": "te-IN-ShrutiNeural",      # Telugu (Female)
    "te-male": "te-IN-MohanNeural",  # Telugu (Male)
    "bn": "bn-IN-TanishaaNeural",    # Bengali (Female)
    "bn-male": "bn-IN-BashkarNeural", # Bengali (Male)
    "gu": "gu-IN-DhwaniNeural",      # Gujarati (Female)
    "gu-male": "gu-IN-NiranjanNeural", # Gujarati (Male)
    "kn": "kn-IN-SapnaNeural",       # Kannada (Female)
    "kn-male": "kn-IN-GaganNeural",  # Kannada (Male)
    "ml": "ml-IN-SobhanaNeural",     # Malayalam (Female)
    "ml-male": "ml-IN-MidhunNeural", # Malayalam (Male)
    "mr": "mr-IN-AarohiNeural",      # Marathi (Female)
    "mr-male": "mr-IN-ManoharNeural", # Marathi (Male)
    "pa": "pa-IN-GurpreetNeural",    # Punjabi (Male)
    "or": "or-IN-SubhasiniNeural",   # Odia (Female) - Limited availability
    # English variants
    "en": "en-IN-NeerjaNeural",      # Indian English (Female)
    "en-male": "en-IN-PrabhatNeural", # Indian English (Male)
    "en-us": "en-US-JennyNeural",    # US English
    "en-uk": "en-GB-SoniaNeural",    # UK English
    # Default
    "default": "en-IN-NeerjaNeural",
}


class TTSService:
    """Text-to-Speech service using Edge TTS (free, no API key needed)."""

    def __init__(self):
        """Initialize TTS service."""
        self._edge_tts_available = None

    async def _check_edge_tts(self) -> bool:
        """Check if edge-tts is available."""
        if self._edge_tts_available is None:
            try:
                import edge_tts
                self._edge_tts_available = True
            except ImportError:
                logger.warning("edge-tts not installed. Install with: pip install edge-tts")
                self._edge_tts_available = False
        return self._edge_tts_available

    async def text_to_speech(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
        rate: str = "+0%",
    ) -> Optional[bytes]:
        """
        Convert text to speech audio using Edge TTS.

        Args:
            text: Text to convert
            language: Language code for voice selection
            voice: Override voice name (Edge TTS voice ID)
            rate: Speech rate adjustment (e.g., "+10%", "-20%")

        Returns:
            Audio bytes (MP3) or None if failed
        """
        if not await self._check_edge_tts():
            return None

        import edge_tts

        # Sanitize text to remove emojis and special characters
        text = sanitize_text_for_tts(text)

        # Check if text is empty after sanitization
        if not text or len(text.strip()) == 0:
            logger.warning("TTS: Text is empty after sanitization, skipping")
            return None

        # Select voice based on language if not specified
        if voice is None:
            voice = LANGUAGE_VOICE_MAP.get(language, LANGUAGE_VOICE_MAP["default"])

        # Truncate text if too long
        if len(text) > 5000:
            text = text[:5000] + "..."

        logger.info(f"TTS: Generating audio for text ({len(text)} chars): {text[:100]}...")
        logger.info(f"TTS: Using voice: {voice}, rate: {rate}")

        try:
            # Create communicate object
            communicate = edge_tts.Communicate(text, voice, rate=rate)

            # Generate audio to bytes
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])

            if audio_chunks:
                audio_bytes = b"".join(audio_chunks)
                logger.info(f"TTS generated successfully for {len(text)} chars using {voice}")
                return audio_bytes
            else:
                logger.error("No audio generated from Edge TTS")
                return None

        except Exception as e:
            logger.error(f"Edge TTS generation failed: {e}", exc_info=True)
            return None

    async def text_to_speech_file(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> Optional[str]:
        """
        Convert text to speech and save to a temporary file.

        Args:
            text: Text to convert
            language: Language code
            voice: Override voice name

        Returns:
            Path to temporary MP3 file or None
        """
        if not await self._check_edge_tts():
            return None

        import edge_tts

        # Select voice based on language if not specified
        if voice is None:
            voice = LANGUAGE_VOICE_MAP.get(language, LANGUAGE_VOICE_MAP["default"])

        try:
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False, prefix="tts_"
            )
            temp_path = temp_file.name
            temp_file.close()

            # Generate audio
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)

            logger.info(f"TTS saved to {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Edge TTS file generation failed: {e}", exc_info=True)
            return None

    async def text_to_speech_url(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> Optional[str]:
        """
        Convert text to speech and return a public URL.

        Uses a temporary file hosting service to make the audio accessible.

        Args:
            text: Text to convert
            language: Language code
            voice: Override voice name (Edge TTS voice ID)

        Returns:
            Public URL to audio file or None
        """
        # Generate audio using Edge TTS
        audio_bytes = await self.text_to_speech(text, language, voice)
        if not audio_bytes:
            return None

        # Upload to temporary hosting
        return await self._upload_audio(audio_bytes)

    async def _upload_audio(self, audio_bytes: bytes) -> Optional[str]:
        """
        Upload audio to temporary file hosting.

        Tries multiple hosting services for reliability.

        Args:
            audio_bytes: Audio data to upload

        Returns:
            Public URL or None
        """
        # Try catbox.moe first (most reliable for programmatic uploads)
        url = await self._upload_to_catbox(audio_bytes)
        if url:
            return url

        # Fallback to tmpfiles.org
        url = await self._upload_to_tmpfiles(audio_bytes)
        if url:
            return url

        # Try file.io
        url = await self._upload_to_fileio(audio_bytes)
        if url:
            return url

        # Last resort: 0x0.st
        url = await self._upload_to_0x0(audio_bytes)
        if url:
            return url

        logger.error("All file upload services failed")
        return None

    async def _upload_to_catbox(self, audio_bytes: bytes) -> Optional[str]:
        """Upload to catbox.moe (reliable, no rate limits)"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": ("voice.mp3", audio_bytes, "audio/mpeg")},
                )

                if response.status_code == 200:
                    url = response.text.strip()
                    if url.startswith("https://"):
                        logger.info(f"Audio uploaded to catbox.moe: {url}")
                        return url

                logger.warning(f"catbox.moe upload failed: {response.status_code} - {response.text[:100]}")
                return None

        except Exception as e:
            logger.warning(f"catbox.moe upload error: {e}")
            return None

    async def _upload_to_0x0(self, audio_bytes: bytes) -> Optional[str]:
        """Upload to 0x0.st"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://0x0.st",
                    files={"file": ("voice.mp3", audio_bytes, "audio/mpeg")},
                )

                if response.status_code == 200:
                    url = response.text.strip()
                    logger.info(f"Audio uploaded to 0x0.st: {url}")
                    return url

                logger.warning(f"0x0.st upload failed: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"0x0.st upload error: {e}")
            return None

    async def _upload_to_tmpfiles(self, audio_bytes: bytes) -> Optional[str]:
        """Upload to tmpfiles.org"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://tmpfiles.org/api/v1/upload",
                    files={"file": ("voice.mp3", audio_bytes, "audio/mpeg")},
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        # Convert view URL to direct download URL
                        url = data.get("data", {}).get("url", "")
                        if url:
                            # tmpfiles.org returns view URL, convert to direct download
                            direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                            logger.info(f"Audio uploaded to tmpfiles.org: {direct_url}")
                            return direct_url

                logger.warning(f"tmpfiles.org upload failed: {response.text}")
                return None

        except Exception as e:
            logger.warning(f"tmpfiles.org upload error: {e}")
            return None

    async def _upload_to_fileio(self, audio_bytes: bytes) -> Optional[str]:
        """Upload to file.io"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://file.io",
                    files={"file": ("voice_response.mp3", audio_bytes, "audio/mpeg")},
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        url = data.get("link")
                        logger.info(f"Audio uploaded to file.io: {url}")
                        return url

                logger.warning(f"file.io upload failed: {response.text}")
                return None

        except Exception as e:
            logger.warning(f"file.io upload error: {e}")
            return None


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get or create TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
