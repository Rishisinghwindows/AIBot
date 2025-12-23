from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from app.logger import logger
from app.services.rag_service import RAGService


class PDFRagAgent:
    def __init__(self, rag_service: RAGService, llm):
        self.rag_service = rag_service
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(
            """You are a PDF RAG assistant.
Use the provided context to answer the question succinctly.
If the context is empty, say you could not find an answer.

Question: {question}
Context:
{context}
"""
        )

    async def run(self, message: str) -> str:
        results = await self.rag_service.similarity_search(message)
        if not results:
            return "No relevant PDF content found."

        context = "\n\n".join(doc.page_content for doc, _ in results)
        messages = self.prompt.format_messages(question=message, context=context)
        try:
            response = await self.llm.ainvoke(messages)
            logger.info(f"pdf_agent_response: hits={len(results)}")
            return response.content
        except Exception as exc:  # noqa: BLE001
            logger.error(f"pdf_llm_error: {exc}")
            return "PDF agent unavailable (LLM error)."
