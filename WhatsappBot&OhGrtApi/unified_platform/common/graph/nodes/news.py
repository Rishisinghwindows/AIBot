"""
News Node.

Handles news queries.
"""

import logging
from typing import Dict, Optional

from common.graph.state import BotState
from common.services.news_service import NewsService

logger = logging.getLogger(__name__)

INTENT = "get_news"


async def handle_news(
    state: BotState,
    news_service: Optional[NewsService] = None,
    api_key: Optional[str] = None,
    country: str = "in",
) -> Dict:
    """
    Handle news queries.

    Args:
        state: Current bot state
        news_service: News service instance
        api_key: News API key (if service not provided)
        country: Country code for news

    Returns:
        State update with news response
    """
    entities = state.get("extracted_entities", {})
    category = entities.get("category")
    query = state.get("current_query", "")

    try:
        # Create service if not provided
        if news_service is None:
            if not api_key:
                return {
                    "response_text": "News service is not configured.",
                    "response_type": "text",
                    "should_fallback": True,
                    "intent": INTENT,
                }
            news_service = NewsService(api_key=api_key)

        # Get news
        articles = await news_service.get_top_headlines(
            country=country,
            category=category,
            page_size=5,
        )

        if not articles:
            return {
                "response_text": "No news articles found at the moment.",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
                "route_log": state.get("route_log", []) + ["news:no_articles"],
            }

        # Format response
        response = news_service.format_headlines(articles)

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "tool_result": {
                "articles": [a.model_dump() for a in articles],
                "count": len(articles),
            },
            "route_log": state.get("route_log", []) + ["news:success"],
        }

    except Exception as e:
        logger.error(f"News handler error: {e}")
        return {
            "response_text": "Sorry, I couldn't fetch the news right now. Please try again later.",
            "response_type": "text",
            "should_fallback": True,
            "intent": INTENT,
            "error": str(e),
            "route_log": state.get("route_log", []) + ["news:error"],
        }
