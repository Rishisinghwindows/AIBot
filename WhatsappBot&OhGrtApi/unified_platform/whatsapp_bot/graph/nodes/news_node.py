"""
News Node

Fetches and displays news articles based on user query.
Supports multilingual responses (11+ Indian languages).
"""

import logging
from whatsapp_bot.state import BotState
from common.tools.news_tool import get_news
from common.utils.response_formatter import sanitize_error, create_service_error_response
from common.i18n.responses import get_news_label, get_phrase

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "get_news"


async def handle_news(state: BotState) -> dict:
    """
    Node function: Fetches news articles and formats them for display.
    Returns response in user's detected language.

    Args:
        state: Current bot state with extracted entities for news query.

    Returns:
        Updated state with news articles or an error message.
    """
    entities = state.get("extracted_entities", {})
    detected_lang = state.get("detected_language", "en")
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
                response_text = get_news_label("not_found", detected_lang)
            else:
                title = get_news_label("title", detected_lang)
                source_label = get_news_label("source", detected_lang)
                response_lines = [f"📰 *{title}:*"]
                for article in articles:
                    response_lines.append(f"\n*{article['title']}*")
                    if article['description']:
                        response_lines.append(f"_{article['description']}_")
                    response_lines.append(f"{source_label}: {article['source']} - {article['url']}")
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
            try_topic = get_news_label("try_topic", detected_lang)
            return {
                "tool_result": result,
                "response_text": try_topic,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"News handler error: {e}")
        error_msg = get_phrase("error_occurred", detected_lang)
        return {
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }
