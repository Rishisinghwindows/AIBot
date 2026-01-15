"""
Database Query Node

Handles natural language queries to a PostgreSQL database.
"""

from whatsapp_bot.state import BotState
from common.tools.db_tool import query_db
from common.i18n.responses import get_phrase
from whatsapp_bot.graph.nodes.chat import handle_chat


def _looks_like_db_query(question: str) -> bool:
    """Return True when the user explicitly asks for database data."""
    text = question.lower()
    db_keywords = [
        "database", "db", "sql", "table", "schema", "query",
        "rows", "records", "entries", "count", "total number",
        "users", "orders", "registered",
    ]
    return any(keyword in text for keyword in db_keywords)


async def handle_db_query(state: BotState) -> dict:
    """
    Node function: Queries the database based on user's natural language question.

    Args:
        state: Current bot state with user's question.

    Returns:
        Updated state with database query results or an error message.
    """
    question = state.get("current_query", "").strip()
    detected_lang = state.get("detected_language", "en")

    if not question:
        return {
            "response_text": """Please provide a question to query the database.

*Example:* How many registered users are there?""",
            "response_type": "text",
            "should_fallback": False,
            "intent": "db_query",
        }

    if not _looks_like_db_query(question):
        return await handle_chat(state)

    try:
        result = await query_db(question)

        if result["success"]:
            data = result["data"]
            response_text = data.get("result", "No results found for your query.")

            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": "db_query",
            }
        else:
            error_text = (result.get("error") or "").lower()
            if "relation" in error_text or "does not exist" in error_text or "schema" in error_text:
                return await handle_chat(state)

            return {
                "tool_result": result,
                "response_text": get_phrase("error_occurred", detected_lang),
                "response_type": "text",
                "should_fallback": False,
                "intent": "db_query",
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": get_phrase("error_occurred", detected_lang),
            "response_type": "text",
            "should_fallback": True,
            "intent": "db_query",
        }
