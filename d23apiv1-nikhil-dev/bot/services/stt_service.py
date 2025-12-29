"""
Speech-to-Text Service

Converts audio to text using MLX Whisper (local, free, optimized for Apple Silicon).
"""

import logging
import tempfile
import os
from typing import Optional

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using MLX Whisper (local, no API needed)."""

    def __init__(self, model_name: str = "mlx-community/whisper-large-v3-turbo"):
        """
        Initialize STT service.

        Args:
            model_name: MLX Whisper model to use. Options:
                - mlx-community/whisper-tiny (fastest, least accurate)
                - mlx-community/whisper-base
                - mlx-community/whisper-small
                - mlx-community/whisper-medium
                - mlx-community/whisper-large-v3-turbo (best balance)
                - mlx-community/whisper-large-v3 (most accurate, slowest)
        """
        self.model_name = model_name
        self._model = None
        self._mlx_whisper_available = None

    async def _check_mlx_whisper(self) -> bool:
        """Check if mlx-whisper is available."""
        if self._mlx_whisper_available is None:
            try:
                import mlx_whisper
                self._mlx_whisper_available = True
            except ImportError:
                logger.warning("mlx-whisper not installed. Install with: pip install mlx-whisper")
                self._mlx_whisper_available = False
        return self._mlx_whisper_available

    def _get_model(self):
        """Lazy load the Whisper model."""
        if self._model is None:
            import mlx_whisper
            logger.info(f"Loading MLX Whisper model: {self.model_name}")
            # Model is loaded automatically by mlx_whisper.transcribe
            self._model = True
        return self._model

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
    ) -> Optional[str]:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Audio data (supports MP3, WAV, OGG, M4A, etc.)
            language: Optional language hint (e.g., "hi", "en", "ta")

        Returns:
            Transcribed text or None if failed
        """
        if not await self._check_mlx_whisper():
            return None

        import mlx_whisper

        try:
            # Save audio to temporary file (mlx_whisper requires file path)
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name

            try:
                # Transcribe
                self._get_model()

                # Build options
                options = {}
                if language:
                    options["language"] = language

                result = mlx_whisper.transcribe(
                    temp_path,
                    path_or_hf_repo=self.model_name,
                    **options
                )

                text = result.get("text", "").strip()
                detected_lang = result.get("language", "unknown")

                logger.info(f"STT transcribed ({detected_lang}): {text[:100]}...")
                return text

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"MLX Whisper transcription failed: {e}", exc_info=True)
            return None

    async def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
    ) -> Optional[str]:
        """
        Transcribe audio file to text.

        Args:
            file_path: Path to audio file
            language: Optional language hint

        Returns:
            Transcribed text or None if failed
        """
        if not await self._check_mlx_whisper():
            return None

        import mlx_whisper

        try:
            self._get_model()

            options = {}
            if language:
                options["language"] = language

            result = mlx_whisper.transcribe(
                file_path,
                path_or_hf_repo=self.model_name,
                **options
            )

            text = result.get("text", "").strip()
            detected_lang = result.get("language", "unknown")

            logger.info(f"STT transcribed ({detected_lang}): {text[:100]}...")
            return text

        except Exception as e:
            logger.error(f"MLX Whisper transcription failed: {e}", exc_info=True)
            return None


# Singleton instance
_stt_service: Optional[STTService] = None


def get_stt_service() -> STTService:
    """Get or create STT service singleton."""
    global _stt_service
    if _stt_service is None:
        # Use turbo model for best speed/accuracy balance
        _stt_service = STTService(model_name="mlx-community/whisper-large-v3-turbo")
    return _stt_service
