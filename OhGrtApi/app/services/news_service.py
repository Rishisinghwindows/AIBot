"""
News Service

Fetches news articles from various sources.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.logger import logger


class NewsService:
    """Service for fetching news articles."""

    def __init__(self, api_key: str):
        """
        Initialize the news service.

        Args:
            api_key: API key for the news service
        """
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    async def get_news(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        country: str = "in",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Fetch news articles.

        Args:
            query: Search query for specific news
            category: News category (business, entertainment, general, health, science, sports, technology)
            country: Country code (default: 'in' for India)
            limit: Maximum number of articles to return

        Returns:
            Dictionary with success status and articles or error
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "News API key not configured",
            }

        try:
            params = {
                "apiKey": self.api_key,
                "pageSize": limit,
            }

            if query:
                # Use everything endpoint for search
                url = f"{self.base_url}/everything"
                params["q"] = query
                params["sortBy"] = "publishedAt"
            else:
                # Use top-headlines endpoint
                url = f"{self.base_url}/top-headlines"
                params["country"] = country
                if category:
                    params["category"] = category

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "ok":
                    articles = data.get("articles", [])
                    formatted_articles = [
                        {
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "source": article.get("source", {}).get("name", "Unknown"),
                            "url": article.get("url", ""),
                            "published_at": article.get("publishedAt", ""),
                            "image_url": article.get("urlToImage", ""),
                        }
                        for article in articles
                    ]
                    return {
                        "success": True,
                        "data": {
                            "articles": formatted_articles,
                            "totalResults": data.get("totalResults", len(articles)),
                        },
                    }
                else:
                    error = data.get("message", "Failed to fetch news")
                    logger.warning(f"News API error: {error}")
                    return {
                        "success": False,
                        "error": error,
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"News API HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
            }
        except Exception as e:
            logger.error(f"News service error: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# Factory function for creating the service
_news_service_instance: Optional[NewsService] = None


def get_news_service(api_key: str) -> NewsService:
    """
    Get or create a NewsService instance.

    Args:
        api_key: API key for the news service

    Returns:
        NewsService instance
    """
    global _news_service_instance
    if _news_service_instance is None or _news_service_instance.api_key != api_key:
        _news_service_instance = NewsService(api_key)
    return _news_service_instance
