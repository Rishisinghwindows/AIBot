"""
News Service.

Provides news articles using NewsAPI.
"""

import logging
from datetime import datetime
from typing import List, Optional

import httpx

from common.models.base import NewsArticle

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching news articles."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://newsapi.org/v2",
    ):
        """
        Initialize news service.

        Args:
            api_key: NewsAPI key
            base_url: API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_top_headlines(
        self,
        country: str = "in",
        category: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 5,
    ) -> List[NewsArticle]:
        """
        Get top news headlines.

        Args:
            country: Country code (e.g., 'in', 'us')
            category: Category (business, entertainment, health, science, sports, technology)
            query: Search query
            page_size: Number of articles to return

        Returns:
            List of NewsArticle objects
        """
        if not self.api_key:
            raise ValueError("News API key not configured")

        client = await self._get_client()

        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": page_size,
        }

        if category:
            params["category"] = category
        if query:
            params["q"] = query

        try:
            response = await client.get(
                f"{self.base_url}/top-headlines",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            articles = []
            for article in data.get("articles", []):
                published_at = None
                if article.get("publishedAt"):
                    try:
                        published_at = datetime.fromisoformat(
                            article["publishedAt"].replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

                articles.append(
                    NewsArticle(
                        title=article.get("title", ""),
                        description=article.get("description"),
                        url=article.get("url", ""),
                        source=article.get("source", {}).get("name", ""),
                        published_at=published_at,
                        image_url=article.get("urlToImage"),
                    )
                )

            return articles
        except Exception as e:
            logger.error(f"News service error: {e}")
            raise

    async def search_news(
        self,
        query: str,
        language: str = "en",
        sort_by: str = "relevancy",
        page_size: int = 5,
    ) -> List[NewsArticle]:
        """
        Search for news articles.

        Args:
            query: Search query
            language: Language code
            sort_by: Sort by (relevancy, popularity, publishedAt)
            page_size: Number of articles

        Returns:
            List of NewsArticle objects
        """
        if not self.api_key:
            raise ValueError("News API key not configured")

        client = await self._get_client()

        params = {
            "apiKey": self.api_key,
            "q": query,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
        }

        try:
            response = await client.get(
                f"{self.base_url}/everything",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            articles = []
            for article in data.get("articles", []):
                published_at = None
                if article.get("publishedAt"):
                    try:
                        published_at = datetime.fromisoformat(
                            article["publishedAt"].replace("Z", "+00:00")
                        )
                    except Exception:
                        pass

                articles.append(
                    NewsArticle(
                        title=article.get("title", ""),
                        description=article.get("description"),
                        url=article.get("url", ""),
                        source=article.get("source", {}).get("name", ""),
                        published_at=published_at,
                        image_url=article.get("urlToImage"),
                    )
                )

            return articles
        except Exception as e:
            logger.error(f"News search error: {e}")
            raise

    def format_headlines(self, articles: List[NewsArticle], limit: int = 5) -> str:
        """
        Format news articles as a readable message.

        Args:
            articles: List of articles
            limit: Max articles to include

        Returns:
            Formatted string
        """
        if not articles:
            return "No news articles found."

        lines = ["*Top Headlines:*\n"]
        for i, article in enumerate(articles[:limit], 1):
            lines.append(f"{i}. *{article.title}*")
            if article.description:
                lines.append(f"   {article.description[:100]}...")
            lines.append(f"   Source: {article.source}")
            lines.append(f"   {article.url}\n")

        return "\n".join(lines)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Module-level service instance
_news_service: Optional[NewsService] = None


def get_news_service(api_key: Optional[str] = None) -> NewsService:
    """
    Get or create news service instance.

    Args:
        api_key: News API key

    Returns:
        NewsService instance
    """
    global _news_service
    if _news_service is None and api_key:
        _news_service = NewsService(api_key=api_key)
    elif _news_service is None:
        raise ValueError("News service not initialized. Provide api_key.")
    return _news_service
