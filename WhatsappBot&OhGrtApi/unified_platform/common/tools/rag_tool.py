"""
RAG Tool

A tool for Retrieval-Augmented Generation from PDF documents.
"""

import asyncio
from pathlib import Path
from typing import List, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

from common.config.settings import settings
from common.graph.state import ToolResult


import os

def build_embeddings(openai_api_key: str) -> Embeddings:
    if openai_api_key:
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=openai_api_key,
        )
    raise ValueError("OPENAI_API_KEY is not set.")


def load_pdf_documents(pdf_path: Path) -> List[Document]:
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    return docs


def chunk_documents(documents: List[Document], chunk_size: int = 800, chunk_overlap: int = 100) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)
    return chunks


class RAGService:
    def __init__(self, openai_api_key: str):
        self.embeddings = build_embeddings(openai_api_key)
        self.persist_dir = Path("db/chroma")
        self.collection_name = "pdfs"

    def _vectorstore(self) -> Chroma:
        return Chroma(
            collection_name=self.collection_name,
            persist_directory=str(self.persist_dir),
            embedding_function=self.embeddings,
        )

    async def similarity_search(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        store = self._vectorstore()
        try:
            results = await asyncio.to_thread(
                store.similarity_search_with_score, query, k=k
            )
        except Exception as exc:
            raise Exception(f"Vector search failed: {exc}") from exc
        return results


async def search_rag(query: str) -> ToolResult:
    """
    Perform a similarity search on the RAG vector store.

    Args:
        query: The query to search for.

    Returns:
        A ToolResult with the search results or an error.
    """
    try:
        from common.config.settings import get_settings
        settings = get_settings()
        rag_service = RAGService(settings.OPENAI_API_KEY)
        results = await rag_service.similarity_search(query)
        if not results:
            return ToolResult(
                success=True,
                data={"results": "No relevant PDF content found."},
                error=None,
                tool_name="rag_search",
            )

        context = "\n\n".join(doc.page_content for doc, _ in results)
        return ToolResult(
            success=True,
            data={"context": context},
            error=None,
            tool_name="rag_search",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="rag_search",
        )
