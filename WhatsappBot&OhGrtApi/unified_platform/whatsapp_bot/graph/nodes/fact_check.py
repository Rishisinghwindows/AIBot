"""
Fact Check Node

Verifies claims and news using multiple sources and AI analysis.
"""

import logging
from whatsapp_bot.state import BotState
from common.tools.fact_check_tool import (
    fact_check,
    VERDICT_EMOJI,
    VERDICT_LABELS,
)
from common.utils.response_formatter import sanitize_error, create_service_error_response
from common.i18n.responses import get_fact_check_label

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "fact_check"


def _format_fact_check_response(data: dict, lang: str = "en") -> str:
    """
    Format fact-check results into a user-friendly message (localized for all 11 languages).

    Args:
        data: Fact-check result data
        lang: Language code for response

    Returns:
        Formatted response string
    """
    claim = data.get("claim", "Unknown claim")
    verdict = data.get("verdict", "UNVERIFIED")
    confidence = data.get("confidence", 0)
    explanation = data.get("explanation", "")
    has_official = data.get("has_official_fact_check", False)
    fact_checks = data.get("fact_check_results", [])
    sources = data.get("sources", [])

    emoji = VERDICT_EMOJI.get(verdict, "❓")
    verdict_label = VERDICT_LABELS.get(verdict, {}).get(lang, verdict)

    # Get localized labels
    title = get_fact_check_label("title", lang)
    claim_label = get_fact_check_label("claim", lang)
    verdict_text = get_fact_check_label("verdict", lang)
    confidence_label = get_fact_check_label("confidence", lang)
    analysis_label = get_fact_check_label("analysis", lang)
    verified_sources = get_fact_check_label("verified_sources", lang)
    references = get_fact_check_label("references", lang)
    disclaimer = get_fact_check_label("disclaimer", lang)

    # Build response
    lines = []

    # Header
    lines.append(f"🔍 *{title}*\n")

    # Claim
    lines.append(f"📝 *{claim_label}:* {claim}\n")

    # Verdict with visual indicator
    lines.append(f"{emoji} *{verdict_text}:* {verdict_label}")

    # Confidence bar
    confidence_bar = _generate_confidence_bar(confidence)
    lines.append(f"📊 *{confidence_label}:* {confidence}% {confidence_bar}\n")

    # Explanation
    if explanation:
        lines.append(f"💬 *{analysis_label}:* {explanation}\n")

    # Official fact checks
    if has_official and fact_checks:
        lines.append(f"📰 *{verified_sources}:*")

        for fc in fact_checks[:2]:
            rating = fc.get("rating", "")
            publisher = fc.get("publisher", "")
            url = fc.get("url", "")
            if publisher and rating:
                lines.append(f"• {publisher}: {rating}")
                if url:
                    lines.append(f"  🔗 {url}")
        lines.append("")

    # Additional sources
    if sources:
        lines.append(f"🔗 *{references}:*")
        for source in sources[:3]:
            lines.append(f"• {source}")
        lines.append("")

    # Disclaimer
    lines.append(f"_⚠️ {disclaimer}_")

    return "\n".join(lines)


def _generate_confidence_bar(confidence: int) -> str:
    """Generate a visual confidence bar."""
    filled = confidence // 10
    empty = 10 - filled

    if confidence >= 80:
        bar_char = "🟢"
    elif confidence >= 60:
        bar_char = "🟡"
    elif confidence >= 40:
        bar_char = "🟠"
    else:
        bar_char = "🔴"

    return bar_char * filled + "⚪" * empty


def _extract_claim_from_state(state: BotState) -> str:
    """
    Extract the claim to verify from state.

    Args:
        state: Bot state

    Returns:
        Claim text
    """
    # Try entities first
    entities = state.get("extracted_entities", {})
    if entities.get("fact_check_claim"):
        return entities["fact_check_claim"]

    # Fall back to current query
    query = state.get("current_query", "")
    return query


async def handle_fact_check(state: BotState) -> dict:
    """
    Node function: Verifies claims using fact-checking sources and AI.
    Returns response in user's detected language.

    Args:
        state: Current bot state with the claim to verify.

    Returns:
        Updated state with fact-check results or an error message.
    """
    query = _extract_claim_from_state(state)
    detected_lang = state.get("detected_language", "en")

    if not query or len(query.strip()) < 5:
        title = get_fact_check_label("title", detected_lang)
        ask_claim = get_fact_check_label("ask_claim", detected_lang)
        return {
            "response_text": f"🔍 *{title}*\n\n{ask_claim}",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    try:
        logger.info(f"Processing fact check request: {query[:100]}...")

        # Call fact-check tool
        result = await fact_check(query, language=detected_lang)

        if result["success"]:
            data = result["data"]
            response_text = _format_fact_check_response(data, detected_lang)

            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "fact_check")
            title = get_fact_check_label("title", detected_lang)
            ask_claim = get_fact_check_label("ask_claim", detected_lang)

            return {
                "tool_result": result,
                "response_text": f"🔍 *{title}*\n\n❌ {user_message}\n\n_{ask_claim}_",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Fact check handler error: {e}")
        error_msg = get_fact_check_label("error", detected_lang)
        return {
            "error": str(e),
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": True,
            "intent": INTENT,
        }
