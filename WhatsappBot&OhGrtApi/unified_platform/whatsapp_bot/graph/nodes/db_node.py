"""
Database Query Node

Handles natural language queries to a PostgreSQL database.
"""

from whatsapp_bot.state import BotState
from common.tools.db_tool import query_db


async def handle_db_query(state: BotState) -> dict:
    """
    Node function: Queries the database based on user's natural language question.

    Args:
        state: Current bot state with user's question.

    Returns:
        Updated state with database query results or an error message.
    """
    question = state.get("current_query", "").strip()

    if not question:
        return {
            "response_text": """Please provide a question to query the database.

*Example:* How many registered users are there?""",
            "response_type": "text",
            "should_fallback": False,
            "intent": "db_query",
        }

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
            return {
                "tool_result": result,
                "response_text": f"Sorry, I couldn't query the database. {result.get('error')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "db_query",
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": f"An unexpected error occurred while querying the database.",
            "response_type": "text",
            "should_fallback": True,
            "intent": "db_query",
        }
