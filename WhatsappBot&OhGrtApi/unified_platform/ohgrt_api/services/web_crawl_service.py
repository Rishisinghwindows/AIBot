from __future__ import annotations

import re

import httpx

from ohgrt_api.logger import logger
from ohgrt_api.utils.errors import ServiceError


class WebCrawlService:
    async def fetch(self, url: str, max_chars: int = 800) -> str:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text
        except Exception as exc:  # noqa: BLE001
            logger.error("web_crawl_error", error=str(exc), url=url)
            raise ServiceError(f"Failed to fetch URL: {exc}") from exc

        # Very simple HTML strip
        cleaned = re.sub("<[^<]+?>", "", text)
        return cleaned[:max_chars]
