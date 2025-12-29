"""
Fact Check Node

Verifies claims and news using multiple sources and AI analysis.
"""

import logging
from bot.state import BotState
from bot.tools.fact_check_tool import (
    fact_check,
    VERDICT_EMOJI,
    VERDICT_LABELS,
)
from bot.utils.response_formatter import sanitize_error, create_service_error_response
from bot.i18n.detector import detect_language

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "fact_check"


def _format_fact_check_response(data: dict, lang: str = "en") -> str:
    """
    Format fact-check results into a user-friendly message.

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

    # Build response
    lines = []

    # Header
    if lang == "hi":
        lines.append("🔍 *फैक्ट चेक रिपोर्ट*\n")
    else:
        lines.append("🔍 *Fact Check Report*\n")

    # Claim
    if lang == "hi":
        lines.append(f"📝 *दावा:* {claim}\n")
    else:
        lines.append(f"📝 *Claim:* {claim}\n")

    # Verdict with visual indicator
    if lang == "hi":
        lines.append(f"{emoji} *फैसला:* {verdict_label}")
    else:
        lines.append(f"{emoji} *Verdict:* {verdict_label}")

    # Confidence bar
    confidence_bar = _generate_confidence_bar(confidence)
    if lang == "hi":
        lines.append(f"📊 *विश्वसनीयता:* {confidence}% {confidence_bar}\n")
    else:
        lines.append(f"📊 *Confidence:* {confidence}% {confidence_bar}\n")

    # Explanation
    if explanation:
        if lang == "hi":
            lines.append(f"💬 *विश्लेषण:* {explanation}\n")
        else:
            lines.append(f"💬 *Analysis:* {explanation}\n")

    # Official fact checks
    if has_official and fact_checks:
        if lang == "hi":
            lines.append("📰 *सत्यापित स्रोत:*")
        else:
            lines.append("📰 *Verified Sources:*")

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
        if lang == "hi":
            lines.append("🔗 *संदर्भ:*")
        else:
            lines.append("🔗 *References:*")
        for source in sources[:3]:
            lines.append(f"• {source}")
        lines.append("")

    # Disclaimer
    if lang == "hi":
        lines.append("_⚠️ यह AI-सहायता प्राप्त विश्लेषण है। महत्वपूर्ण मामलों के लिए कृपया आधिकारिक स्रोतों से सत्यापित करें।_")
    else:
        lines.append("_⚠️ This is AI-assisted analysis. Please verify from official sources for important matters._")

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

    Args:
        state: Current bot state with the claim to verify.

    Returns:
        Updated state with fact-check results or an error message.
    """
    query = _extract_claim_from_state(state)

    if not query or len(query.strip()) < 5:
        return {
            "response_text": (
                "🔍 *Fact Check*\n\n"
                "Please provide a claim to verify.\n\n"
                "_Examples:_\n"
                "• Fact check: Drinking warm water kills coronavirus\n"
                "• Is it true that 5G causes health problems?\n"
                "• Verify: India has the largest population\n\n"
                "_हिंदी में:_\n"
                "• फैक्ट चेक: गर्म पानी पीने से कोरोना मरता है\n"
                "• क्या यह सच है कि 5G से स्वास्थ्य समस्याएं होती हैं?"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    # Detect language for response formatting
    detected_lang = detect_language(query)
    response_lang = "hi" if detected_lang == "hi" else "en"

    try:
        logger.info(f"Processing fact check request: {query[:100]}...")

        # Call fact-check tool
        result = await fact_check(query, language=detected_lang)

        if result["success"]:
            data = result["data"]
            response_text = _format_fact_check_response(data, response_lang)

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

            if response_lang == "hi":
                return {
                    "tool_result": result,
                    "response_text": (
                        "🔍 *फैक्ट चेक*\n\n"
                        f"❌ {user_message}\n\n"
                        "_कृपया एक विशिष्ट दावा प्रदान करें जिसे सत्यापित करना है।_"
                    ),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }
            else:
                return {
                    "tool_result": result,
                    "response_text": (
                        "🔍 *Fact Check*\n\n"
                        f"❌ {user_message}\n\n"
                        "_Please provide a specific claim to verify._"
                    ),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }

    except Exception as e:
        logger.error(f"Fact check handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="Fact Check",
            raw_error=str(e)
        )
