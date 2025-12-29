"""
News Node

Fetches and displays news articles based on user query.
"""

import logging
from bot.state import BotState
from bot.tools.news_tool import get_news
from bot.utils.response_formatter import sanitize_error, create_service_error_response

logger = logging.getLogger(__name__)

# Intent constant
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
        result = await get_news(query=query, category=category)

        if result["success"]:
            articles = result["data"].get("articles", [])
            if not articles:
                response_text = "I couldn't find any news for your query."
            else:
                response_lines = ["Here are the top news headlines:"]
                for article in articles:
                    response_lines.append(f"\n*{article['title']}*")
                    if article['description']:
                        response_lines.append(f"_{article['description']}_")
                    response_lines.append(f"Source: {article['source']} - {article['url']}")
                response_text = "\n".join(response_lines)
            
            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "news")
            return {
                "tool_result": result,
                "response_text": (
                    "*News*\n\n"
                    f"{user_message}\n\n"
                    "_Try searching for a specific topic like 'tech news' or 'sports news'._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"News handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="News",
            raw_error=str(e)
        )
