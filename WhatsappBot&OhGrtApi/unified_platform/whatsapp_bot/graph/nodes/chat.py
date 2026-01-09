"""
General Chat Node

Handles general conversation using GPT-4o-mini.
Falls back handler when no specific intent is matched.
Supports multi-language responses.
"""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from whatsapp_bot.state import BotState
from whatsapp_bot.config import settings
from common.utils.response_formatter import sanitize_error
from common.i18n.constants import LANGUAGE_NAMES
from common.i18n.responses import get_chat_label

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "chat"


CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful WhatsApp assistant for Indian users, similar to puch.ai.

You can help with:
- Local search (finding places, restaurants, hospitals, businesses)
- Image generation (creating AI images from text prompts)
- Indian Railways PNR status check
- Train running status
- Metro ticket information (Delhi Metro and others)
- Astrology (horoscopes, kundli, predictions)
- Weather updates
- News updates
- General questions and conversation

Guidelines:
- Be friendly, helpful, and concise (WhatsApp has message limits)
- Use simple language that works well on mobile
- If the user asks about something you can do, guide them with examples
- For PNR: "To check PNR status, send: PNR 1234567890"
- For train status: "To check train status, send: Train 12345 status"
- For local search: "To find places, send: restaurants near Connaught Place"
- For image: "To generate an image, send: Generate image of sunset on beach"
- For metro: "For metro info, send: Metro from Dwarka to Rajiv Chowk"

Keep responses short and actionable. Use line breaks for readability.
Avoid using too many emojis - one or two max per message.

IMPORTANT - LANGUAGE INSTRUCTION:
The user's message is in {language_name}. You MUST respond in {language_name} ({language_code}).
If the language is not English, respond entirely in that language using the appropriate script (e.g., Hindi in Devanagari script, Bengali in Bengali script, Tamil in Tamil script, etc.).
Match the user's language naturally and fluently.""",
        ),
        ("human", "{message}"),
    ]
)


# Language code to full name mapping for prompt
def get_language_instruction(lang_code: str) -> tuple:
    """Get language name and code for prompt."""
    lang_info = LANGUAGE_NAMES.get(lang_code, {"en": "English", "native": "English"})
    return lang_info.get("en", "English"), lang_code


def handle_chat(state: BotState) -> dict:
    """
    Node function: Handle general chat messages.
    Responds in the user's detected language.

    Args:
        state: Current bot state

    Returns:
        Updated state with chat response
    """
    user_message = (
        state.get("current_query", "")
        or state["whatsapp_message"].get("text", "")
    )

    # Get detected language (default to English)
    detected_lang = state.get("detected_language", "en")
    language_name, language_code = get_language_instruction(detected_lang)
    logger.info(f"Chat handler using language: {language_name} ({language_code})")

    if not user_message:
        # Return localized welcome message
        welcome_msg = get_chat_label("welcome", detected_lang)
        return {
            "response_text": welcome_msg,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY,
        )
        chain = CHAT_PROMPT | llm

        # Include language info in the prompt
        response = chain.invoke({
            "message": user_message,
            "language_name": language_name,
            "language_code": language_code,
        })

        return {
            "response_text": response.content,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Chat handler error: {e}")
        error_msg = get_chat_label("error", detected_lang)
        fallback_msg = get_chat_label("fallback", detected_lang)
        return {
            "error": str(e),
            "response_text": f"{error_msg}\n\n{fallback_msg}",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }


def handle_fallback(state: BotState) -> dict:
    """
    Fallback node: Called when other nodes fail.
    Returns response in user's detected language.

    Args:
        state: Current bot state with error info

    Returns:
        Updated state with fallback response
    """
    error = state.get("error", "")
    original_intent = state.get("intent", "unknown")
    detected_lang = state.get("detected_language", "en")

    # Log the error for debugging
    if error:
        logger.warning(f"Fallback triggered for intent '{original_intent}': {error}")

    # Get localized fallback message
    response = get_chat_label("fallback", detected_lang)

    return {
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }
