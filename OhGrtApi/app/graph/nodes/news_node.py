"""
News Node

Fetches and displays news articles based on user query.
Uses the OhGrtApi NewsService.
"""

from app.graph.state import BotState
from app.services.news_service import get_news_service
from app.config import get_settings
from app.logger import logger

INTENT = "get_news"


async def handle_news(state: BotState) -> dict:
    """
    Node function: Fetches news articles and formats them for display.

    Args:
        state: Current bot state with extracted entities for news query.

    Returns:
        Updated state with news articles or an error message.
    """
    entities = state.get("extracted_entities", {})
    query = entities.get("news_query", "").strip()
    category = entities.get("news_category", "").strip()

    if not query and not category:
        # Default to top headlines if no query or category is provided
        category = "general"

    try:
        settings = get_settings()
        news_service = get_news_service(settings.news_api_key)

        result = await news_service.get_news(
            query=query if query else None,
            category=category if category else None,
            limit=5
        )

        if result.get("success"):
            articles = result.get("data", {}).get("articles", [])

            if not articles:
                response_text = (
                    "*News*\n\n"
                    "No news articles found for your query.\n\n"
                    "_Try searching for a specific topic like 'tech news' or 'sports news'._"
                )
            else:
                response_lines = ["*Top News Headlines*\n"]

                for i, article in enumerate(articles[:5], 1):
                    title = article.get("title", "No title")
                    description = article.get("description", "")
                    source = article.get("source", "Unknown")
                    url = article.get("url", "")

                    response_lines.append(f"{i}. *{title}*")
                    if description:
                        # Truncate description if too long
                        desc = description[:150] + "..." if len(description) > 150 else description
                        response_lines.append(f"   _{desc}_")
                    if source:
                        response_lines.append(f"   Source: {source}")
                    response_lines.append("")  # Empty line between articles

                response_text = "\n".join(response_lines)

            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            error = result.get("error", "Unknown error")
            logger.warning(f"News fetch failed: {error}")
            return {
                "tool_result": result,
                "response_text": (
                    "*News*\n\n"
                    "Could not fetch news at the moment.\n\n"
                    "_Please try again later._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"News handler error: {e}")
        return {
            "response_text": (
                "*News*\n\n"
                "An error occurred while fetching news.\n\n"
                "_Please try again later._"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
