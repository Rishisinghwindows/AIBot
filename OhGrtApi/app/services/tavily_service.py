from __future__ import annotations

from typing import List, Dict
import asyncio

from langchain_tavily import TavilySearch

from app.config import Settings
from app.logger import logger
from app.utils.errors import ExternalServiceUnavailable


class TavilyService:   # ✅ CLASS NAME MUST MATCH
    def __init__(self, settings: Settings):
        self.client = TavilySearch(
            tavily_api_key=settings.tavily_api_key,
            max_results=5,
            search_depth="advanced",
        )

    async def search_places(self, query: str) -> List[Dict[str, str]]:
        logger.info("tavily_search_request", query=query)

        try:
            response = await self.client.ainvoke({"query": query})
        except Exception as exc:  # noqa: BLE001
            logger.error("tavily_search_error", error=str(exc))
            raise ExternalServiceUnavailable("Tavily search failed") from exc

        return [
            {
                "name": r.get("title", ""),
                "address": "",
                "website": r.get("url", ""),
                "snippet": r.get("content", ""),
            }
            for r in response.get("results", [])
        ]
