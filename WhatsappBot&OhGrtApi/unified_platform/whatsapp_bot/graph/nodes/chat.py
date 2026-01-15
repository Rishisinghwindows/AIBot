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
from whatsapp_bot.conversation_manager import (
    ConversationState,
    get_conversation_manager,
)
from whatsapp_bot.graph.context_cache import get_context as get_followup_context
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


def _should_use_followup_context(message: str) -> bool:
    """Heuristic check for follow-up queries that need prior context."""
    msg = message.lower().strip()
    if len(msg) <= 60:
        return True
    followup_phrases = [
        "also", "and", "what about", "about", "tell", "more", "details",
        "all", "list", "explain", "pls", "please",
    ]
    return any(phrase in msg for phrase in followup_phrases)


def _is_alternate_route_followup(message: str) -> bool:
    """Detect short follow-ups asking for alternate routes."""
    msg = message.lower().strip()
    phrases = [
        "other route",
        "another route",
        "alternate route",
        "alternative route",
        "different route",
        "second route",
        "aur route",
        "kuch aur route",
        "koi aur route",
        "dusra route",
        "doosra route",
        "aur rasta",
        "kuch aur rasta",
        "koi aur rasta",
        "dusra rasta",
        "doosra rasta",
        "alternate rasta",
        "alternative rasta",
    ]
    return any(phrase in msg for phrase in phrases)


def _is_confirmation(message: str) -> bool:
    msg = message.lower().strip()
    confirmations = {
        "yes", "y", "yeah", "yep", "sure", "ok", "okay", "pls", "please",
        "pls do", "please do", "ha", "haan", "ji", "theek", "thik", "bilkul",
    }
    return msg in confirmations


def _is_full_text_request(message: str) -> bool:
    msg = message.lower().strip()
    triggers = [
        "full text", "complete text", "entire text", "full version",
        "पूरा पाठ", "पूरा टेक्स्ट", "फुल टेक्स्ट", "पूरा",
    ]
    return any(t in msg for t in triggers)


def _is_confirmation(message: str) -> bool:
    msg = message.lower().strip()
    confirmations = {
        "yes", "y", "yeah", "yep", "sure", "ok", "okay", "pls", "please",
        "pls do", "please do", "ha", "haan", "ji", "theek", "thik", "bilkul",
    }
    return msg in confirmations


def _is_hanuman_chalisa_request(text: str) -> bool:
    if not text:
        return False
    return "hanuman chalisa" in text.lower() or "हनुमान चालीसा" in text


def _hanuman_chalisa_response(lang: str) -> str:
    if lang == "hi":
        return (
            "🚩 *हनुमान चालीसा (टेक्स्ट)* 🚩\n"
            "यहाँ पूरा पाठ देखने/कॉपी करने के लिए:\n"
            "https://hi.wikipedia.org/wiki/हनुमान_चालीसा\n\n"
            "श्रीगुरु चरन सरोज रज, निज मन मुकुरु सुधारि।\n"
            "बरनउँ रघुबर बिमल जसु, जो दायकु फल चारि॥\n"
            "बुद्धिहीन तनु जानिके, सुमिरौं पवन कुमार।\n"
            "बल बुद्धि विद्या देहु मोहि, हरहु कलेस विकार॥"
        )
    return (
        "Here is the Hanuman Chalisa text (Hindi):\n"
        "https://hi.wikipedia.org/wiki/हनुमान_चालीसा"
    )


async def handle_chat(state: BotState) -> dict:
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
    phone = state.get("whatsapp_message", {}).get("from_number", "")

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
        last_query = ""
        try:
            manager = get_conversation_manager()
            existing_context = await manager.get_context(phone) if phone else None
            context_data = existing_context.get("data", {}) if existing_context else {}
            last_query = (context_data.get("last_user_query") or "").strip()
        except Exception:
            cached = get_followup_context(phone) if phone else None
            last_query = (cached or {}).get("last_user_query", "").strip()

        if _is_confirmation(user_message) and _is_hanuman_chalisa_request(last_query):
            response_text = _hanuman_chalisa_response(detected_lang)
            if phone:
                await manager.set_context(
                    phone=phone,
                    state=ConversationState.IDLE,
                    data={
                        "last_user_query": user_message,
                        "last_bot_response": response_text,
                    },
                    intent=INTENT,
                )
            return {
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        prompt_message = user_message
        if last_query and _should_use_followup_context(user_message):
            if _is_alternate_route_followup(user_message):
                prompt_message = (
                    f"Previous question: {last_query}\n"
                    f"Current question: {user_message}\n"
                    "Instruction: Provide alternate routes/options for the same trip. "
                    "Do not ask for clarification unless critical details are missing."
                )
            elif _is_confirmation(user_message) or _is_full_text_request(user_message):
                prompt_message = (
                    f"Previous question: {last_query}\n"
                    f"Current question: {user_message}\n"
                    "Instruction: Treat this as a confirmation/follow-up to the previous request. "
                    "Provide the full response without asking extra clarification."
                )
            else:
                prompt_message = (
                    f"Previous question: {last_query}\n"
                    f"Current question: {user_message}"
                )

        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.7,
            api_key=settings.openai_api_key,
        )
        chain = CHAT_PROMPT | llm

        # Include language info in the prompt
        response = chain.invoke({
            "message": prompt_message,
            "language_name": language_name,
            "language_code": language_code,
        })

        if phone:
            await manager.set_context(
                phone=phone,
                state=ConversationState.IDLE,
                data={
                    "last_user_query": user_message,
                    "last_bot_response": response.content,
                },
                intent=INTENT,
            )

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
