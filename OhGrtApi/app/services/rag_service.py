from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import Settings
from app.logger import logger
from app.utils.embedding import build_embeddings, chunk_documents, load_pdf_documents
from app.utils.errors import ServiceError


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embeddings = build_embeddings(settings)
        self.persist_dir = Path("data/chroma")
        self.collection_name = "pdfs"

    def _vectorstore(self) -> Chroma:
        return Chroma(
            collection_name=self.collection_name,
            persist_directory=str(self.persist_dir),
            embedding_function=self.embeddings,
        )

    async def ingest_pdf(self, path: Path) -> Tuple[int, str]:
        docs = await asyncio.to_thread(load_pdf_documents, path)
        chunks = chunk_documents(docs)
        try:
            store = self._vectorstore()
            await asyncio.to_thread(store.add_documents, chunks)
        except Exception as exc:  # noqa: BLE001
            logger.error("pdf_ingest_error", error=str(exc))
            raise ServiceError(f"Failed to ingest PDF: {exc}") from exc

        return len(chunks), self.collection_name

    async def similarity_search(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
        store = self._vectorstore()
        try:
            results = await asyncio.to_thread(
                store.similarity_search_with_score, query, k=k
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("rag_query_error", error=str(exc))
            raise ServiceError(f"Vector search failed: {exc}") from exc
        logger.info(
            "rag_results",
            query=query,
            results=[{"score": score, "snippet": doc.page_content[:120]} for doc, score in results],
        )
        return results
