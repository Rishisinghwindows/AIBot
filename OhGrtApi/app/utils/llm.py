from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.config import Settings
from app.logger import logger


def build_chat_llm(settings: Settings) -> BaseChatModel:
    """
    Centralized Ollama chat LLM factory.
    """
    if settings.openai_api_key:
        logger.info("openai_llm_init", model=settings.openai_model)
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
        )
    logger.info(
        "ollama_llm_init",
        server=settings.ollama_server,
        model=settings.ollama_model,
    )
    return ChatOllama(
        base_url=settings.ollama_server,
        model=settings.ollama_model,
        temperature=0.1,
    )


def build_embedding_llm(settings: Settings) -> Optional[BaseChatModel]:
    """
    Some tools (e.g., SQL chain) accept chat LLMs. Kept separate
    in case we want a different model for embeddings vs chat.
    """
    return build_chat_llm(settings)
