"""
General Chat Node

Handles general conversation using GPT-4o-mini.
Falls back handler when no specific intent is matched.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ohgrt_api.graph.state import BotState
from ohgrt_api.config import get_settings
from ohgrt_api.logger import logger

INTENT = "chat"


CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant for Indian users.

You can help with:
- Astrology (horoscope, kundli, predictions, birth chart)
- Travel (PNR status, train tracking)
- Weather updates
- News headlines
- Image generation
- Local search (finding places, restaurants, hospitals)
- General questions and conversation

Guidelines:
- Be friendly, helpful, and concise
- Use simple language that works well on mobile
- Keep responses short and actionable
- Use line breaks for readability
- Avoid too many emojis - one or two max

If asked about something specific, guide users with examples:
- PNR: "Send: PNR 1234567890"
- Train: "Send: Train 12345 status"
- Horoscope: "Send: Aries horoscope"
- Weather: "Send: Weather in Delhi"
- Image: "Send: Generate image of sunset"
"""),
    ("human", "{message}"),
])


def handle_chat(state: BotState) -> dict:
    """
    Node function: Handle general chat messages.

    Args:
        state: Current bot state

    Returns:
        Updated state with chat response
    """
    user_message = (
        state.get("current_query", "")
        or state["whatsapp_message"].get("text", "")
    )

    if not user_message:
        return {
            "response_text": (
                "Hi! I'm your AI assistant.\n\n"
                "I can help you with:\n"
                "• Astrology & Horoscopes\n"
                "• Train/PNR Status\n"
                "• Weather Updates\n"
                "• News Headlines\n"
                "• Image Generation\n"
                "• Local Search\n\n"
                "How can I help you today?"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    try:
        settings = get_settings()

        if not settings.openai_api_key:
            return {
                "response_text": (
                    "I'm here to help!\n\n"
                    "Try asking me about:\n"
                    "• Your horoscope (e.g., 'Aries horoscope')\n"
                    "• PNR status (e.g., 'PNR 1234567890')\n"
                    "• Weather (e.g., 'Weather in Mumbai')\n"
                    "• News (e.g., 'Latest news')"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            api_key=settings.openai_api_key,
        )
        chain = CHAT_PROMPT | llm
        response = chain.invoke({"message": user_message})

        return {
            "response_text": response.content,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Chat handler error: {e}")
        return {
            "error": str(e),
            "response_text": (
                "I encountered an issue processing your message.\n\n"
                "Try one of these:\n"
                "• Weather: 'Weather in Delhi'\n"
                "• Horoscope: 'Aries horoscope'\n"
                "• PNR: 'PNR 1234567890'\n"
                "• News: 'Latest news'"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }


def handle_fallback(state: BotState) -> dict:
    """
    Fallback node: Called when other nodes fail.

    Args:
        state: Current bot state with error info

    Returns:
        Updated state with fallback response
    """
    error = state.get("error", "")
    original_intent = state.get("intent", "unknown")

    if error:
        logger.warning(f"Fallback triggered for intent '{original_intent}': {error}")

    response = (
        "Oops! Something didn't go as planned.\n\n"
        "Let me help with something else:\n\n"
        "Quick Actions:\n"
        "• Weather: 'Weather in Mumbai'\n"
        "• Horoscope: 'Leo horoscope'\n"
        "• PNR: 'PNR 1234567890'\n"
        "• Train: 'Train 12345 status'\n"
        "• News: 'Latest news'\n"
        "• Image: 'Generate image of sunset'\n\n"
        "Or just type your question!"
    )

    return {
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
