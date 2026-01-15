"""
News Node

Fetches and displays news articles based on user query.
Supports multilingual responses (11+ Indian languages).

UPDATED: Now uses AI for response translation.
"""

import logging
from whatsapp_bot.state import BotState
from whatsapp_bot.config import settings
from common.tools.news_tool import get_news
from common.utils.response_formatter import sanitize_error, create_service_error_response
from common.i18n.responses import get_news_label, get_phrase

# AI Translation Service
try:
    from common.services.ai_language_service import ai_translate_response
    AI_TRANSLATE_AVAILABLE = True
except ImportError:
    AI_TRANSLATE_AVAILABLE = False

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "get_news"


async def handle_news(state: BotState) -> dict:
    """
    Node function: Fetches news articles and formats them for display.
    Returns response in user's detected language using AI translation.

    Args:
        state: Current bot state with extracted entities for news query.

    Returns:
        Updated state with news articles or an error message.
    """
    entities = state.get("extracted_entities", {})
    detected_lang = state.get("detected_language", "en")
    query = entities.get("news_query", "").strip()
    category = entities.get("news_category", "").strip()

    # Also try to get query from current_query if not in entities
    if not query:
        current_query = state.get("current_query", "")
        # Use the normalized query if available (already in English)
        if current_query and "news" not in current_query.lower():
            query = current_query

    logger.info(f"News handler: query={query}, category={category}, lang={detected_lang}")

    if not query and not category:
        # Default to top headlines if no query or category is provided
        category = "general"

    try:
        result = await get_news(query=query, category=category, language=detected_lang)

        if result["success"]:
            articles = result["data"].get("articles", [])
            if not articles:
                response_text = get_news_label("not_found", detected_lang)
            else:
                title = get_news_label("title", detected_lang)
                source_label = get_news_label("source", detected_lang)
                response_lines = [f"📰 *{title}:*"]
                for article in articles:
                    headline = article.get("title", "").strip()
                    url = article.get("url", "").strip()
                    source = article.get("source", "").strip()
                    description = (article.get("description") or "").strip()

                    if headline:
                        response_lines.append(f"\n*{headline}*")
                    if description:
                        response_lines.append(f"_{description}_")
                    if url:
                        response_lines.append(f"{url}")
                    if source:
                        response_lines.append(f"{source_label}: {source}")
                response_text = "\n".join(response_lines)

                # Translate response to user's language using AI
                if detected_lang != "en" and AI_TRANSLATE_AVAILABLE:
                    try:
                        response_text = await ai_translate_response(
                            text=response_text,
                            target_language=detected_lang,
                            openai_api_key=settings.openai_api_key
                        )
                    except Exception as e:
                        logger.warning(f"AI translation failed for news: {e}")

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
