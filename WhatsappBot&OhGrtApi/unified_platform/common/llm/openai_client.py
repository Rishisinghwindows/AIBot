"""
OpenAI client utilities.

Provides a unified interface for OpenAI API interactions.
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Get a cached OpenAI client instance.

    Args:
        api_key: OpenAI API key (uses env var if not provided)

    Returns:
        OpenAI client instance
    """
    return OpenAI(api_key=api_key) if api_key else OpenAI()


@lru_cache(maxsize=1)
def get_async_openai_client(api_key: Optional[str] = None) -> AsyncOpenAI:
    """
    Get a cached async OpenAI client instance.

    Args:
        api_key: OpenAI API key (uses env var if not provided)

    Returns:
        AsyncOpenAI client instance
    """
    return AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()


async def get_chat_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Get a chat completion from OpenAI.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        api_key: OpenAI API key
        **kwargs: Additional arguments to pass to the API

    Returns:
        Generated text response
    """
    client = get_async_openai_client(api_key)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


async def get_embedding(
    text: str,
    model: str = "text-embedding-3-small",
    api_key: Optional[str] = None,
) -> List[float]:
    """
    Get text embedding from OpenAI.

    Args:
        text: Text to embed
        model: Embedding model to use
        api_key: OpenAI API key

    Returns:
        Embedding vector
    """
    client = get_async_openai_client(api_key)

    try:
        response = await client.embeddings.create(
            model=model,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"OpenAI embedding error: {e}")
        raise


async def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "audio.ogg",
    model: str = "whisper-1",
    api_key: Optional[str] = None,
) -> str:
    """
    Transcribe audio using OpenAI Whisper.

    Args:
        audio_bytes: Audio file bytes
        filename: Filename for the audio
        model: Whisper model to use
        api_key: OpenAI API key

    Returns:
        Transcribed text
    """
    import io

    client = get_openai_client(api_key)

    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        transcription = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
        )
        return transcription.text.strip()
    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        raise
