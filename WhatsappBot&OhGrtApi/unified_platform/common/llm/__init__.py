"""
LLM client utilities.

Provides unified interfaces for OpenAI and Ollama LLM clients.
"""

from common.llm.openai_client import get_openai_client, get_chat_completion
from common.llm.ollama_client import get_ollama_client

__all__ = [
    "get_openai_client",
    "get_chat_completion",
    "get_ollama_client",
]
