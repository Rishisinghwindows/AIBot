"""
News API Tool

Wrapper for NewsAPI.org.
"""

import httpx
from typing import Optional, List
from bot.config import get_settings
from bot.state import ToolResult


TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"
EVERYTHING_URL = "https://newsapi.org/v2/everything"


def _parse_articles(data: dict) -> list:
    """Parse articles from API response."""
    articles = []
    for article in data.get("articles", []):
        # Skip articles with [Removed] title (deleted articles)
        title = article.get("title", "")
        if not title or "[Removed]" in title:
            continue
        articles.append({
            "title": title,
            "description": article.get("description"),
            "url": article.get("url"),
            "source": article.get("source", {}).get("name"),
        })
    return articles


async def get_news(query: Optional[str] = None, category: Optional[str] = None, country: str = "in") -> ToolResult:
    """
    Get top news headlines from NewsAPI.

    Args:
        query: Keywords or a phrase to search for.
        category: The category to get news for (e.g., business, entertainment, health, science, sports, technology).
        country: The 2-letter ISO 3166-1 code of the country you want to get headlines for.

    Returns:
        ToolResult with a list of news articles or an error.
    """
    settings = get_settings()
    if not settings.NEWS_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="News API key not configured.",
            tool_name="get_news",
        )

    try:
        async with httpx.AsyncClient() as client:
            articles = []

            # Strategy 1: Try top-headlines first (works for some countries)
            params = {
                "apiKey": settings.NEWS_API_KEY,
                "country": country,
            }
            if category:
                params["category"] = category

            response = await client.get(TOP_HEADLINES_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                articles = _parse_articles(data)

            # Strategy 2: If no articles from top-headlines, use "everything" endpoint
            if not articles:
                # Build search query for India news
                search_query = query or "India"
                if category and category != "general":
                    search_query = f"{search_query} {category}"

                params = {
                    "apiKey": settings.NEWS_API_KEY,
                    "q": search_query,
                    "sortBy": "publishedAt",
                    "language": "en",
                }

                response = await client.get(EVERYTHING_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "ok":
                    articles = _parse_articles(data)

            if not articles:
                return ToolResult(
                    success=True,
                    data={"articles": []},
                    error=None,
                    tool_name="get_news",
                )

            return ToolResult(
                success=True,
                data={"articles": articles[:5]},  # Return top 5 articles
                error=None,
                tool_name="get_news",
            )

    except httpx.HTTPStatusError as e:
        return ToolResult(
            success=False,
            data=None,
            error=f"API request failed with status {e.response.status_code}",
            tool_name="get_news",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="get_news",
        )
