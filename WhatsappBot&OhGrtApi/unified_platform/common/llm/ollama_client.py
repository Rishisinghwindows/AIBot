"""
Ollama client utilities.

Provides interface for local Ollama LLM interactions.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama API interactions."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3-vl:8b",
        timeout: float = 120.0,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL
            model: Default model to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            model: Model to use (uses default if not specified)
            system: System prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        client = await self._get_client()

        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs,
        }

        if system:
            payload["system"] = system

        try:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Chat completion.

        Args:
            messages: List of message dictionaries
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        client = await self._get_client()

        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            **kwargs,
        }

        try:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    async def list_models(self) -> List[str]:
        """
        List available models.

        Returns:
            List of model names
        """
        client = await self._get_client()

        try:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Ollama list models error: {e}")
            return []

    async def is_available(self) -> bool:
        """
        Check if Ollama server is available.

        Returns:
            True if server is responsive
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Module-level client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client(
    base_url: str = "http://localhost:11434",
    model: str = "qwen3-vl:8b",
) -> OllamaClient:
    """
    Get or create Ollama client instance.

    Args:
        base_url: Ollama server URL
        model: Default model

    Returns:
        OllamaClient instance
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient(base_url=base_url, model=model)
    return _ollama_client
