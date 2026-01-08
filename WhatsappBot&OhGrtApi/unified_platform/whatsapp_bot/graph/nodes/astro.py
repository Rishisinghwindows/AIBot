"""
Astrology Node.

Handles horoscope and astrology queries.
Supports multilingual responses (11+ Indian languages).
"""

import logging
import re
from typing import Dict

from common.graph.state import BotState
from common.i18n.responses import get_horoscope_label, get_zodiac_name, ZODIAC_NAMES

logger = logging.getLogger(__name__)

INTENT = "get_horoscope"

# Zodiac sign mappings (English and Hindi)
ZODIAC_SIGNS = {
    "aries": {"name": "Aries", "hindi": "Mesh", "symbol": ""},
    "taurus": {"name": "Taurus", "hindi": "Vrishabh", "symbol": ""},
    "gemini": {"name": "Gemini", "hindi": "Mithun", "symbol": ""},
    "cancer": {"name": "Cancer", "hindi": "Kark", "symbol": ""},
    "leo": {"name": "Leo", "hindi": "Singh", "symbol": ""},
    "virgo": {"name": "Virgo", "hindi": "Kanya", "symbol": ""},
    "libra": {"name": "Libra", "hindi": "Tula", "symbol": ""},
    "scorpio": {"name": "Scorpio", "hindi": "Vrishchik", "symbol": ""},
    "sagittarius": {"name": "Sagittarius", "hindi": "Dhanu", "symbol": ""},
    "capricorn": {"name": "Capricorn", "hindi": "Makar", "symbol": ""},
    "aquarius": {"name": "Aquarius", "hindi": "Kumbh", "symbol": ""},
    "pisces": {"name": "Pisces", "hindi": "Meen", "symbol": ""},
}

# Hindi to English mapping (romanized and Devanagari script)
HINDI_TO_ENGLISH = {
    # Romanized Hindi
    "mesh": "aries",
    "vrishabh": "taurus",
    "mithun": "gemini",
    "kark": "cancer",
    "singh": "leo",
    "simha": "leo",
    "kanya": "virgo",
    "tula": "libra",
    "vrishchik": "scorpio",
    "dhanu": "sagittarius",
    "makar": "capricorn",
    "kumbh": "aquarius",
    "meen": "pisces",
    # Hindi script (Devanagari)
    "मेष": "aries",
    "वृषभ": "taurus",
    "मिथुन": "gemini",
    "कर्क": "cancer",
    "सिंह": "leo",
    "कन्या": "virgo",
    "तुला": "libra",
    "वृश्चिक": "scorpio",
    "धनु": "sagittarius",
    "मकर": "capricorn",
    "कुंभ": "aquarius",
    "कुम्भ": "aquarius",
    "मीन": "pisces",
}


def extract_zodiac_sign(text: str) -> str:
    """
    Extract zodiac sign from text (supports English, romanized Hindi, and Devanagari script).

    Args:
        text: User message

    Returns:
        Zodiac sign in English or empty string
    """
    text_lower = text.lower()

    # Check English names
    for sign in ZODIAC_SIGNS:
        if sign in text_lower:
            return sign

    # Check Hindi names (both in original text for script, and lowercased for romanized)
    for hindi, english in HINDI_TO_ENGLISH.items():
        # Check in original text (for Devanagari script - doesn't change with lowercase)
        if hindi in text:
            return english
        # Check in lowercased text (for romanized Hindi)
        if hindi in text_lower:
            return english

    return ""


async def get_horoscope(sign: str, api_key: str) -> Dict:
    """
    Fetch horoscope from API.

    Args:
        sign: Zodiac sign in English
        api_key: Astrology API key

    Returns:
        Horoscope data
    """
    import httpx

    # Using a sample astrology API structure
    url = "https://aztro.sameerkumar.website/"

    params = {"sign": sign, "day": "today"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, params=params)
        response.raise_for_status()
        return response.json()


def format_horoscope(data: Dict, sign_info: Dict, lang: str = "en") -> str:
    """
    Format horoscope data as a readable message (localized).

    Args:
        data: Horoscope API response
        sign_info: Sign details
        lang: Language code

    Returns:
        Formatted message
    """
    symbol = sign_info.get("symbol", "")
    sign_key = sign_info.get("name", "").lower()

    # Get localized sign name
    localized_name = get_zodiac_name(sign_key, lang)
    title = get_horoscope_label("title", lang)

    lines = [
        f"{symbol} *{localized_name} - {title}* {symbol}",
        "",
    ]

    if data.get("description"):
        lines.append(data["description"])
        lines.append("")

    # Add additional info if available with localized labels
    if data.get("mood"):
        mood_label = get_horoscope_label("mood", lang)
        lines.append(f"*{mood_label}:* {data['mood']}")
    if data.get("color"):
        color_label = get_horoscope_label("lucky_color", lang)
        lines.append(f"*{color_label}:* {data['color']}")
    if data.get("lucky_number"):
        number_label = get_horoscope_label("lucky_number", lang)
        lines.append(f"*{number_label}:* {data['lucky_number']}")
    if data.get("lucky_time"):
        time_label = get_horoscope_label("lucky_time", lang)
        lines.append(f"*{time_label}:* {data['lucky_time']}")
    if data.get("compatibility"):
        compat_label = get_horoscope_label("compatibility", lang)
        lines.append(f"*{compat_label}:* {data['compatibility']}")

    return "\n".join(lines)


# Hindi Devanagari sign info for Hindi responses
ZODIAC_SIGNS_HINDI = {
    "aries": {"name": "मेष", "english": "Aries"},
    "taurus": {"name": "वृषभ", "english": "Taurus"},
    "gemini": {"name": "मिथुन", "english": "Gemini"},
    "cancer": {"name": "कर्क", "english": "Cancer"},
    "leo": {"name": "सिंह", "english": "Leo"},
    "virgo": {"name": "कन्या", "english": "Virgo"},
    "libra": {"name": "तुला", "english": "Libra"},
    "scorpio": {"name": "वृश्चिक", "english": "Scorpio"},
    "sagittarius": {"name": "धनु", "english": "Sagittarius"},
    "capricorn": {"name": "मकर", "english": "Capricorn"},
    "aquarius": {"name": "कुंभ", "english": "Aquarius"},
    "pisces": {"name": "मीन", "english": "Pisces"},
}


async def handle_horoscope(state: BotState) -> Dict:
    """
    Handle horoscope queries (supports Hindi and English).

    Args:
        state: Current bot state

    Returns:
        State update with horoscope
    """
    query = state.get("current_query", "")
    entities = state.get("extracted_entities", {})
    detected_lang = state.get("detected_language", "en")

    # Extract zodiac sign - check both astro_sign (from intent.py) and zodiac_sign
    sign = entities.get("astro_sign") or entities.get("zodiac_sign") or extract_zodiac_sign(query)

    # If sign is in Hindi script, convert to English
    if sign and sign in HINDI_TO_ENGLISH:
        sign = HINDI_TO_ENGLISH[sign]

    if not sign:
        # Ask for sign in user's language (fully localized)
        ask_sign = get_horoscope_label("ask_sign", detected_lang)
        example = get_horoscope_label("example", detected_lang)

        # Build sign list in user's language
        sign_names = []
        for sign_key in list(ZODIAC_NAMES.keys())[:6]:  # Show first 6 signs
            sign_names.append(get_zodiac_name(sign_key, detected_lang))
        signs_list = ", ".join(sign_names) + ", ..."

        response = (
            f"*{ask_sign}*\n\n"
            f"{signs_list}\n\n"
            f"*{example}*"
        )

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "route_log": state.get("route_log", []) + ["horoscope:missing_sign"],
        }

    sign_info = ZODIAC_SIGNS.get(sign, {"name": sign.title(), "hindi": "", "symbol": ""})

    try:
        from whatsapp_bot.config import settings
        api_key = settings.astrology_api_key

        # Fetch horoscope
        data = await get_horoscope(sign, api_key or "")

        # Format response with detected language
        response = format_horoscope(data, sign_info, detected_lang)

        return {
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "tool_result": data,
            "route_log": state.get("route_log", []) + ["horoscope:success"],
        }

    except Exception as e:
        logger.error(f"Horoscope error: {e}")

        try:
            from common.astro.tools.horoscope import HoroscopeInput, HoroscopePeriod, get_daily_horoscope

            fallback_input = HoroscopeInput(
                sign=sign,
                period=HoroscopePeriod.TODAY,
                include_details=False,
            )
            fallback_result = await get_daily_horoscope(fallback_input)
            if fallback_result and fallback_result.success:
                localized_sign = get_zodiac_name(sign, detected_lang)
                title = get_horoscope_label("title", detected_lang)
                color_label = get_horoscope_label("lucky_color", detected_lang)
                number_label = get_horoscope_label("lucky_number", detected_lang)
                love_label = get_horoscope_label("love", detected_lang)
                career_label = get_horoscope_label("career", detected_lang)
                health_label = get_horoscope_label("health", detected_lang)
                sign_key = fallback_result.sign
                sign_specific = {
                    "Aries": {
                        "love": "Keep conversations direct and avoid rushing decisions today.",
                        "career": "Channel your energy into one priority task for best results.",
                        "health": "Short bursts of exercise will lift your mood.",
                    },
                    "Taurus": {
                        "love": "Show care through small, consistent gestures.",
                        "career": "Steady progress beats quick fixes—pace yourself.",
                        "health": "Stick to a simple routine and hydrate well.",
                    },
                    "Gemini": {
                        "love": "Listen fully before responding; clarity helps.",
                        "career": "Organize scattered ideas into a short plan.",
                        "health": "Take short breaks to avoid mental fatigue.",
                    },
                    "Cancer": {
                        "love": "Be open about feelings, but keep expectations realistic.",
                        "career": "Focus on tasks that need empathy and patience.",
                        "health": "Rest and light walks will steady your energy.",
                    },
                    "Leo": {
                        "love": "A warm compliment can shift the mood quickly.",
                        "career": "Lead with confidence, but invite feedback.",
                        "health": "Stretching helps release built-up tension.",
                    },
                    "Virgo": {
                        "love": "Kindness matters more than perfection today.",
                        "career": "Break big tasks into smaller checklists.",
                        "health": "Mindful breathing will calm overthinking.",
                    },
                    "Libra": {
                        "love": "Balance your needs with theirs—clear boundaries help.",
                        "career": "Collaborate, but avoid delaying key decisions.",
                        "health": "A calm routine supports focus.",
                    },
                    "Scorpio": {
                        "love": "Avoid overanalyzing—trust simple signals.",
                        "career": "Go deep on one problem; you’ll uncover answers.",
                        "health": "Slow, steady movement keeps you grounded.",
                    },
                    "Sagittarius": {
                        "love": "Keep things light; humor helps connection.",
                        "career": "A new idea can open doors—note it down.",
                        "health": "Outdoor time boosts your energy.",
                    },
                    "Capricorn": {
                        "love": "Consistency speaks louder than grand gestures.",
                        "career": "Prioritize long-term impact over quick wins.",
                        "health": "Respect your limits; recovery matters.",
                    },
                    "Aquarius": {
                        "love": "Share your thoughts—don’t assume they know.",
                        "career": "Try a different approach to a stuck task.",
                        "health": "Unplug briefly to reset your focus.",
                    },
                    "Pisces": {
                        "love": "Gentle honesty clears confusion.",
                        "career": "Trust intuition but verify the details.",
                        "health": "Quiet time restores your balance.",
                    },
                }
                horoscope_text = (
                    fallback_result.horoscope
                    or fallback_result.overall_theme
                    or get_horoscope_label("generic_prediction", detected_lang)
                )

                lines = [
                    f"✨ *{localized_sign} - {title}* ✨",
                    "",
                    horoscope_text,
                ]
                tips = sign_specific.get(sign_key, {})
                if tips:
                    lines.append("")
                    if tips.get("love"):
                        lines.append(f"💕 *{love_label}:* {tips['love']}")
                    if tips.get("career"):
                        lines.append(f"💼 *{career_label}:* {tips['career']}")
                    if tips.get("health"):
                        lines.append(f"🩺 *{health_label}:* {tips['health']}")
                if fallback_result.lucky_color:
                    lines.append("")
                    lines.append(f"💫 *{color_label}:* {fallback_result.lucky_color}")
                if fallback_result.lucky_number:
                    lines.append(f"🔢 *{number_label}:* {fallback_result.lucky_number}")

                return {
                    "response_text": "\n".join(lines),
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                    "tool_result": fallback_result.model_dump(),
                    "route_log": state.get("route_log", []) + ["horoscope:fallback_template"],
                }
        except Exception as fallback_error:
            logger.warning(f"Template horoscope fallback failed: {fallback_error}")

        # Return a generic horoscope if API fails - fully localized
        localized_sign = get_zodiac_name(sign, detected_lang)
        title = get_horoscope_label("title", detected_lang)
        prediction = get_horoscope_label("generic_prediction", detected_lang)
        color_label = get_horoscope_label("lucky_color", detected_lang)
        number_label = get_horoscope_label("lucky_number", detected_lang)
        love_label = get_horoscope_label("love", detected_lang)
        love_text = get_horoscope_label("good_day_romance", detected_lang)

        generic_response = (
            f"✨ *{localized_sign} - {title}* ✨\n\n"
            f"{prediction}\n\n"
            f"💫 *{color_label}:* Yellow\n"
            f"🔢 *{number_label}:* 7\n"
            f"💕 *{love_label}:* {love_text}"
        )

        return {
            "response_text": generic_response,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
            "route_log": state.get("route_log", []) + ["horoscope:fallback"],
        }
