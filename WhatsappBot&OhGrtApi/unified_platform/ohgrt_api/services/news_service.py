"""
News Service

Provides news headlines and articles from various sources.
"""

import logging
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class NewsService:
    """Service for fetching news."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"

    async def get_news(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        country: str = "in",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get news headlines.

        Args:
            query: Search query (optional)
            category: News category (business, entertainment, health, science, sports, technology)
            country: Country code (default: in for India)
            limit: Number of articles to return

        Returns:
            List of news articles
        """
        try:
            if self.api_key:
                result = await self._fetch_real_news(query, category, country, limit)
                if result["success"]:
                    return result

            # Return sample news for demo
            return self._generate_demo_news(query, category, limit)

        except Exception as e:
            logger.error(f"News service error: {e}")
            return {"success": False, "error": str(e)}

    async def _fetch_real_news(
        self,
        query: Optional[str],
        category: Optional[str],
        country: str,
        limit: int
    ) -> Dict[str, Any]:
        """Fetch real news from API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "apiKey": self.api_key,
                    "pageSize": limit,
                    "country": country
                }

                if query:
                    params["q"] = query
                    endpoint = f"{self.base_url}/everything"
                else:
                    endpoint = f"{self.base_url}/top-headlines"
                    if category:
                        params["category"] = category

                response = await client.get(endpoint, params=params)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        articles = []
                        for article in data.get("articles", [])[:limit]:
                            articles.append({
                                "title": article.get("title", ""),
                                "description": article.get("description", ""),
                                "source": article.get("source", {}).get("name", ""),
                                "url": article.get("url", ""),
                                "published_at": article.get("publishedAt", ""),
                                "image_url": article.get("urlToImage", "")
                            })
                        return {
                            "success": True,
                            "data": {
                                "query": query,
                                "category": category,
                                "articles": articles,
                                "total_results": data.get("totalResults", len(articles))
                            }
                        }

                return {"success": False, "error": "Could not fetch news"}
        except Exception as e:
            logger.warning(f"Real news API failed: {e}")
            return {"success": False, "error": str(e)}

    def _generate_demo_news(
        self,
        query: Optional[str],
        category: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """Generate demo news articles."""
        demo_articles = {
            "general": [
                {"title": "India Launches New Space Mission", "description": "ISRO announces ambitious new lunar exploration program", "source": "Times of India"},
                {"title": "Stock Markets Hit New High", "description": "Sensex crosses 80,000 mark for the first time", "source": "Economic Times"},
                {"title": "Monsoon Arrives Early This Year", "description": "IMD predicts above-normal rainfall for the season", "source": "Hindustan Times"},
                {"title": "New Education Policy Changes", "description": "Government announces major reforms in higher education", "source": "NDTV"},
                {"title": "Tech Giants Invest in India", "description": "Major investments announced in Indian startup ecosystem", "source": "Business Standard"},
            ],
            "sports": [
                {"title": "India Wins Cricket Series", "description": "Team India clinches decisive victory in the final match", "source": "ESPN Cricinfo"},
                {"title": "Olympics Preparations Underway", "description": "Indian athletes gear up for upcoming Olympics", "source": "Sports Star"},
                {"title": "IPL Season Announced", "description": "BCCI reveals schedule for upcoming IPL season", "source": "Cricbuzz"},
            ],
            "technology": [
                {"title": "AI Revolution in India", "description": "Indian startups lead AI innovation in Asia", "source": "Tech Crunch India"},
                {"title": "5G Expansion Continues", "description": "Telecom operators expand 5G coverage nationwide", "source": "Gadgets 360"},
                {"title": "UPI Transactions Record", "description": "Digital payments cross 10 billion monthly transactions", "source": "Inc42"},
            ],
            "business": [
                {"title": "RBI Policy Update", "description": "Central bank maintains interest rates, announces new measures", "source": "Mint"},
                {"title": "Startup Funding Surge", "description": "Indian startups raise record funding in Q4", "source": "Your Story"},
                {"title": "Manufacturing Growth", "description": "Make in India initiative shows positive results", "source": "Financial Express"},
            ]
        }

        # Select articles based on category
        if category and category.lower() in demo_articles:
            articles = demo_articles[category.lower()][:limit]
        else:
            articles = demo_articles["general"][:limit]

        # Filter by query if provided
        if query:
            query_lower = query.lower()
            articles = [a for a in articles if query_lower in a["title"].lower() or query_lower in a["description"].lower()]

        # Format response
        formatted_articles = []
        for article in articles[:limit]:
            formatted_articles.append({
                "title": article["title"],
                "description": article["description"],
                "source": article["source"],
                "url": f"https://news.example.com/{article['title'].lower().replace(' ', '-')}",
                "published_at": datetime.now().isoformat(),
                "image_url": None
            })

        return {
            "success": True,
            "data": {
                "query": query,
                "category": category,
                "articles": formatted_articles,
                "total_results": len(formatted_articles)
            }
        }


# Singleton instance
_news_service: Optional[NewsService] = None


def get_news_service(api_key: Optional[str] = None) -> NewsService:
    """Get singleton news service instance."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService(api_key)
    return _news_service
