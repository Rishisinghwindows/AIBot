from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from app.config import Settings
from app.logger import logger


def build_embeddings(settings: Settings) -> Embeddings:
    if settings.openai_api_key:
        logger.info("embedding_client_init", provider="openai", model=settings.openai_model)
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
        )
    logger.info(
        "embedding_client_init",
        server=settings.ollama_server,
        model=settings.ollama_model,
    )
    return OllamaEmbeddings(
        base_url=settings.ollama_server,
        model=settings.ollama_model,
    )


def load_pdf_documents(pdf_path: Path) -> List[Document]:
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    logger.info("pdf_loaded", path=str(pdf_path), pages=len(docs))
    return docs


def chunk_documents(documents: List[Document], chunk_size: int = 800, chunk_overlap: int = 100) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)
    logger.info("pdf_chunked", chunks=len(chunks))
    return chunks
