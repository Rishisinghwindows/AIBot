"""
Dosha Check Node

LangGraph node that handles dosha detection requests.
Checks for Manglik, Kaal Sarp, Sade Sati, and Pitra doshas.
"""

import logging
from typing import Dict, Any

from bot.state import BotState
from bot.tools.dosha_tool import (
    check_all_doshas,
    check_manglik_only,
    check_sade_sati_only,
)
from bot.utils.response_formatter import (
    sanitize_error,
    create_missing_input_response,
    create_service_error_response,
)

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "dosha_check"


async def handle_dosha_check(state: BotState) -> dict:
    """
    Handle dosha check requests.

    Detects doshas based on birth chart:
    - Manglik Dosha (Mars position)
    - Kaal Sarp Dosha (Rahu-Ketu axis)
    - Sade Sati (Saturn transit)
    - Pitra Dosha (Sun affliction)

    Args:
        state: Current bot state with extracted entities

    Returns:
        Updated state dict with response
    """
    entities = state.get("extracted_entities", {})
    specific_dosha = entities.get("specific_dosha")
    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()

    # For Sade Sati, we can check with just Moon sign
    if specific_dosha == "sade_sati":
        # Check if moon sign is provided directly
        moon_sign = entities.get("moon_sign", "").strip()

        if moon_sign:
            # Quick check with moon sign only
            try:
                result = await check_sade_sati_only(moon_sign)
                if result["success"]:
                    return _format_sade_sati_response(result["data"])
            except Exception as e:
                logger.error(f"Sade Sati quick check error: {e}")

    # Check if we have required birth details
    missing = []
    if not birth_date:
        missing.append("birth date (e.g., 15-08-1990)")
    if not birth_time:
        missing.append("birth time (e.g., 10:30 AM)")
    if not birth_place:
        missing.append("birth place (e.g., Delhi)")

    if missing:
        dosha_name = _get_dosha_display_name(specific_dosha)
        example = _get_dosha_example(specific_dosha)

        return create_missing_input_response(
            missing_fields=missing,
            intent=INTENT,
            feature_name=f"{dosha_name} Check",
            example=example
        )

    try:
        # Call the dosha check tool
        result = await check_all_doshas(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            specific_dosha=specific_dosha
        )

        if result["success"]:
            return _format_dosha_response(result["data"], specific_dosha)
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "dosha check")
            dosha_name = _get_dosha_display_name(specific_dosha)
            return {
                "response_text": (
                    f"*{dosha_name} Check*\n\n"
                    f"{user_message}\n\n"
                    "_Please verify your birth details and try again._"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Dosha check handler error: {e}")
        dosha_name = _get_dosha_display_name(specific_dosha)
        return create_service_error_response(
            intent=INTENT,
            feature_name=f"{dosha_name} Check",
            raw_error=str(e)
        )


def _get_dosha_display_name(dosha_type: str) -> str:
    """Get display name for dosha type."""
    names = {
        "manglik": "Manglik Dosha",
        "kaal_sarp": "Kaal Sarp Dosha",
        "sade_sati": "Shani Sade Sati",
        "pitra": "Pitra Dosha",
    }
    return names.get(dosha_type, "Dosha")


def _get_dosha_example(dosha_type: str) -> str:
    """Get example query for dosha type."""
    examples = {
        "manglik": "\"Am I Manglik? Born 15-08-1990 at 10:30 AM in Delhi\"",
        "kaal_sarp": "\"Check Kaal Sarp dosha for 15-08-1990 10:30 AM Delhi\"",
        "sade_sati": "\"Is Sade Sati running for me? DOB 15-08-1990\"",
        "pitra": "\"Check Pitra dosha for 15-08-1990 10:30 AM Delhi\"",
    }
    return examples.get(dosha_type, "\"Check my doshas - 15-08-1990 10:30 AM Delhi\"")


def _format_sade_sati_response(data: dict) -> dict:
    """Format Sade Sati quick check response."""
    sade_sati = data.get("sade_sati", {})
    moon_sign = data.get("moon_sign", "")

    response = "*Shani Sade Sati Check*\n\n"
    response += f"*Moon Sign:* {moon_sign}\n"
    response += f"*Current Saturn:* {sade_sati.get('current_saturn_sign', '')}\n\n"

    if sade_sati.get("is_sade_sati"):
        phase = sade_sati.get("current_phase", "")
        severity = sade_sati.get("severity", "")

        response += f"*Status:* Sade Sati is ACTIVE\n"
        response += f"*Phase:* {phase}\n"
        response += f"*Severity:* {severity}\n\n"

        effects = sade_sati.get("effects", [])
        if effects:
            response += "*Effects:*\n"
            for effect in effects[:4]:
                response += f"- {effect}\n"

        response += "\n*Positive Aspects:*\n"
        positives = sade_sati.get("positive_aspects", [])
        for pos in positives[:3]:
            response += f"- {pos}\n"

    elif sade_sati.get("is_dhaiya"):
        response += f"*Status:* Small Panoti (Dhaiya) is active\n"
        response += f"*Phase:* {sade_sati.get('current_phase', '')}\n\n"

        effects = sade_sati.get("effects", [])
        if effects:
            response += "*Effects:*\n"
            for effect in effects[:3]:
                response += f"- {effect}\n"
    else:
        response += "*Status:* No Sade Sati or Dhaiya currently active\n"
        response += f"*Saturn Position:* {sade_sati.get('current_saturn_sign', '')} (not affecting your Moon sign)\n"

    # Remedies
    remedies = sade_sati.get("remedies", [])
    if remedies:
        response += "\n*Remedies:*\n"
        for remedy in remedies[:5]:
            response += f"- {remedy}\n"

    # Advice
    advice = sade_sati.get("advice", "")
    if advice:
        response += f"\n_{advice}_"

    return {
        "tool_result": data,
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }


def _format_dosha_response(data: dict, specific_dosha: str = None) -> dict:
    """Format dosha check response."""
    person = data.get("person", {})
    chart_summary = data.get("chart_summary", {})

    response = "*Dosha Analysis Report*\n\n"

    # Person info
    if person.get("name"):
        response += f"*Name:* {person['name']}\n"
    response += f"*DOB:* {person.get('dob', '')}\n"
    response += f"*Birth Place:* {person.get('birth_place', '')}\n\n"

    # Chart summary
    response += "*Chart Summary:*\n"
    response += f"- Moon Sign: {chart_summary.get('moon_sign', 'N/A')}\n"
    response += f"- Ascendant: {chart_summary.get('ascendant', 'N/A')}\n"
    response += f"- Nakshatra: {chart_summary.get('moon_nakshatra', 'N/A')}\n\n"

    # Check if single dosha or all doshas
    if specific_dosha and "dosha" in data:
        # Single dosha response
        dosha = data["dosha"]
        response += _format_single_dosha(dosha)
    elif "doshas" in data:
        # All doshas response
        doshas = data["doshas"]
        summary = data.get("summary", {})

        # Summary
        active_count = summary.get("active_count", 0)
        active_doshas = summary.get("active_doshas", [])

        if active_count > 0:
            response += f"*Found {active_count} Active Dosha(s):*\n"
            for ad in active_doshas:
                response += f"  - {ad}\n"
            response += "\n"
        else:
            response += "*No major doshas found in your chart.*\n\n"

        # Detailed breakdown
        response += "─" * 30 + "\n"
        response += "*Detailed Analysis:*\n\n"

        # Manglik
        manglik = doshas.get("manglik", {})
        response += _format_dosha_brief(manglik, "Manglik Dosha")

        # Kaal Sarp
        kaal_sarp = doshas.get("kaal_sarp", {})
        response += _format_dosha_brief(kaal_sarp, "Kaal Sarp Dosha")

        # Sade Sati
        sade_sati = doshas.get("sade_sati", {})
        if sade_sati.get("is_sade_sati") or sade_sati.get("is_dhaiya"):
            response += f"*Shani Sade Sati:* {sade_sati.get('current_phase', 'Active')}\n"
        else:
            response += "*Shani Sade Sati:* Not Active\n"

        # Pitra
        pitra = doshas.get("pitra", {})
        response += _format_dosha_brief(pitra, "Pitra Dosha")

    response += "\n_For personalized remedies, consult a qualified astrologer._"

    return {
        "tool_result": data,
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
        "intent": INTENT,
    }


def _format_single_dosha(dosha: dict) -> str:
    """Format a single dosha's detailed response."""
    dosha_name = dosha.get("dosha_name", "Dosha")
    is_present = dosha.get("is_present", False)
    severity = dosha.get("severity", "None")

    response = f"*{dosha_name}*\n\n"

    if is_present:
        response += f"*Status:* PRESENT\n"
        response += f"*Severity:* {severity}\n\n"

        # Type (for Kaal Sarp)
        if dosha.get("type"):
            response += f"*Type:* {dosha['type']}\n\n"

        # Mars position (for Manglik)
        if dosha.get("mars_sign"):
            response += f"*Mars Sign:* {dosha['mars_sign']}\n"
            response += f"*Mars House from Lagna:* {dosha.get('mars_house_from_lagna', 'N/A')}\n"
            response += f"*Mars House from Moon:* {dosha.get('mars_house_from_moon', 'N/A')}\n\n"

        # Cancellation factors
        cancellations = dosha.get("cancellation_factors", [])
        if cancellations:
            response += "*Cancellation Factors Found:*\n"
            for cf in cancellations:
                response += f"  - {cf}\n"
            response += "\n"

        # Effects
        effects = dosha.get("effects", [])
        if isinstance(effects, list) and effects:
            response += "*Effects:*\n"
            for effect in effects[:5]:
                response += f"- {effect}\n"
            response += "\n"
        elif isinstance(effects, str):
            response += f"*Effects:* {effects}\n\n"

        # Positive aspects (for Kaal Sarp)
        positives = dosha.get("positive_aspects", [])
        if positives:
            response += "*Positive Aspects:*\n"
            for pos in positives[:3]:
                response += f"- {pos}\n"
            response += "\n"

        # Remedies
        remedies = dosha.get("remedies", [])
        if remedies:
            response += "*Remedies:*\n"
            for remedy in remedies[:6]:
                response += f"- {remedy}\n"

    else:
        response += f"*Status:* NOT PRESENT\n"
        if severity and severity != "None":
            response += f"*Note:* {severity}\n"

    # Advice
    advice = dosha.get("advice", "")
    if advice:
        response += f"\n_{advice}_"

    return response


def _format_dosha_brief(dosha: dict, name: str) -> str:
    """Format brief dosha status."""
    is_present = dosha.get("is_present", False)
    severity = dosha.get("severity", "None")

    if is_present:
        return f"*{name}:* Present ({severity})\n"
    else:
        return f"*{name}:* Not Present\n"
