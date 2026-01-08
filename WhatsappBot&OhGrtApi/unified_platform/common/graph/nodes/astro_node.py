"""
Astrology Node Handlers

Handles all astrology-related intents using local Vedic calculations:
1. Horoscope (Daily/Weekly/Monthly)
2. Birth Chart (Kundli) - Using Swiss Ephemeris
3. Kundli Matching (Ashtakoot Milan) - 36-point system
4. Ask Astrologer (AI Q&A)
5. Numerology
6. Tarot Reading
"""

from common.graph.state import BotState
from common.tools.astro_tool import (
    get_horoscope,
    calculate_kundli,
    calculate_kundli_milan,
    calculate_numerology,
    draw_tarot,
    ask_astrologer,
    calculate_panchang,
    ZODIAC_SIGNS,
    NAKSHATRAS,
)
from common.i18n.constants import LANGUAGE_NAMES


# =============================================================================
# 1. HOROSCOPE HANDLER
# =============================================================================

async def handle_horoscope(state: BotState) -> dict:
    """Handle horoscope requests (daily/weekly/monthly)."""
    entities = state.get("extracted_entities", {})
    sign = entities.get("astro_sign", "").strip()
    period = entities.get("astro_period", "today").strip().lower()

    # Get detected language for response
    detected_lang = state.get("detected_language", "en")
    lang_info = LANGUAGE_NAMES.get(detected_lang, {"en": "English"})
    language_name = lang_info.get("en", "English")

    if not sign:
        # Show message in user's language
        if detected_lang == "hi":
            signs_hindi = "मेष, वृषभ, मिथुन, कर्क, सिंह, कन्या, तुला, वृश्चिक, धनु, मकर, कुम्भ, मीन"
            return {
                "response_text": f"*राशिफल*\n\nकृपया अपनी राशि बताएं।\n\n*उपलब्ध राशियां:*\n{signs_hindi}\n\n*उदाहरण:*\n- \"मेष राशिफल\"\n- \"सिंह साप्ताहिक राशिफल\"\n- \"धनु मासिक राशिफल\"",
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            signs_list = ", ".join(ZODIAC_SIGNS)
            return {
                "response_text": f"*Horoscope*\n\nPlease specify your zodiac sign.\n\n*Available signs:*\n{signs_list}\n\n*Examples:*\n- \"Aries horoscope\"\n- \"Leo weekly horoscope\"\n- \"Scorpio monthly prediction\"",
                "response_type": "text",
                "should_fallback": False,
            }

    try:
        result = await get_horoscope(sign=sign, period=period, language=language_name)

        if result["success"]:
            data = result["data"]
            horoscope = data.get("horoscope", data.get("description", "No prediction available"))

            period_display = period.capitalize() if period in ["today", "tomorrow", "yesterday"] else period.title()

            response_text = f"*{sign.capitalize()} {period_display} Horoscope*\n\n{horoscope}"

            if data.get("lucky_number"):
                response_text += f"\n\n*Lucky Number:* {data['lucky_number']}"
            if data.get("lucky_color"):
                response_text += f"\n*Lucky Color:* {data['lucky_color']}"
            if data.get("advice"):
                response_text += f"\n\n*Advice:* {data['advice']}"

            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, couldn't get the horoscope. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "An error occurred while fetching the horoscope.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 2. BIRTH CHART (KUNDLI) HANDLER
# =============================================================================

async def handle_birth_chart(state: BotState) -> dict:
    """Handle birth chart (Kundli) requests using Swiss Ephemeris."""
    entities = state.get("extracted_entities", {})
    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()
    name = entities.get("name", "").strip()

    # Check required fields
    missing = []
    if not birth_date:
        missing.append("birth date (e.g., 15-08-1990)")
    if not birth_time:
        missing.append("birth time (e.g., 10:30 AM)")
    if not birth_place:
        missing.append("birth place (e.g., Delhi)")

    if missing:
        return {
            "response_text": f"*Birth Chart (Kundli)*\n\nTo generate your Kundli, I need:\n\n" +
                           "\n".join([f"- {field}" for field in missing]) +
                           "\n\n*Example:*\n\"Kundli for Rahul born on 15-08-1990 at 10:30 AM in Delhi\"",
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        result = await calculate_kundli(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            name=name if name else None
        )

        if result["success"]:
            data = result["data"]

            # Format response
            response = f"*Birth Chart (Kundli)*\n\n"
            if name:
                response += f"*Name:* {name}\n"
            response += f"*Birth Date:* {birth_date}\n"
            response += f"*Birth Time:* {birth_time}\n"
            response += f"*Birth Place:* {birth_place}\n\n"

            response += f"*Ascendant (Lagna):* {data['ascendant']['sign']}\n"
            response += f"*Sun Sign:* {data['sun_sign']}\n"
            response += f"*Moon Sign:* {data['moon_sign']}\n"
            response += f"*Nakshatra:* {data['moon_nakshatra']}\n\n"

            response += f"*Vedic Details:*\n"
            response += f"- Varna: {data['varna']}\n"
            response += f"- Nadi: {data['nadi']}\n"
            response += f"- Yoni: {data['yoni']}\n"
            response += f"- Gana: {data['gana']}\n"
            response += f"- Vashya: {data['vashya']}\n\n"

            response += f"*Planetary Positions:*\n"
            for planet, info in data.get('planetary_positions', {}).items():
                response += f"- {planet}: {info['sign']} ({info['nakshatra']})\n"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, couldn't generate the birth chart. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "An error occurred while generating the birth chart.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 3. KUNDLI MATCHING HANDLER (36-point Ashtakoot Milan)
# =============================================================================

async def handle_kundli_matching(state: BotState) -> dict:
    """Handle Kundli matching (compatibility) using Ashtakoot Milan."""
    entities = state.get("extracted_entities", {})

    person1_name = entities.get("person1_name", "Person 1").strip()
    person1_dob = entities.get("person1_dob", "").strip()
    person1_time = entities.get("person1_time", "12:00:00").strip()
    person1_place = entities.get("person1_place", "Delhi").strip()

    person2_name = entities.get("person2_name", "Person 2").strip()
    person2_dob = entities.get("person2_dob", "").strip()
    person2_time = entities.get("person2_time", "12:00:00").strip()
    person2_place = entities.get("person2_place", "Delhi").strip()

    # Check required fields
    missing = []
    if not person1_dob:
        missing.append("First person's date of birth")
    if not person2_dob:
        missing.append("Second person's date of birth")

    if missing:
        return {
            "response_text": f"*Kundli Matching*\n\nTo check compatibility, I need:\n\n" +
                           "\n".join([f"- {field}" for field in missing]) +
                           "\n\n*Example:*\n\"Match kundli of Rahul (15-08-1990) and Priya (22-03-1992)\"" +
                           "\n\nOptionally include birth time and place for more accuracy.",
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        result = await calculate_kundli_milan(
            person1_name=person1_name,
            person1_dob=person1_dob,
            person1_time=person1_time,
            person1_place=person1_place,
            person2_name=person2_name,
            person2_dob=person2_dob,
            person2_time=person2_time,
            person2_place=person2_place,
        )

        if result["success"]:
            data = result["data"]
            scores = data["scores"]

            response = f"*Kundli Matching Report*\n\n"
            response += f"*{data['person1']['name']}*\n"
            response += f"  DOB: {data['person1']['dob']} | Sign: {data['person1']['moon_sign']}\n\n"
            response += f"*{data['person2']['name']}*\n"
            response += f"  DOB: {data['person2']['dob']} | Sign: {data['person2']['moon_sign']}\n\n"

            response += f"*Ashtakoot Milan (8 Kootas):*\n"
            for koota, info in scores.items():
                koota_name = koota.replace('_', ' ').title()
                response += f"- {koota_name}: {info['score']}/{info['max']}\n"

            response += f"\n*Total Score:* {data['total_score']}/36 ({data['percentage']}%)\n"
            response += f"*Verdict:* {data['verdict']}\n"
            response += f"*Recommendation:* {data['recommendation']}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, couldn't perform Kundli matching. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "An error occurred during Kundli matching.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 4. ASK ASTROLOGER HANDLER
# =============================================================================

async def handle_ask_astrologer(state: BotState) -> dict:
    """Handle astrology Q&A requests."""
    entities = state.get("extracted_entities", {})
    question = entities.get("astro_question", "").strip()
    user_sign = entities.get("user_sign", "").strip()

    if not question:
        question = state.get("current_query", "").strip()

    if not question or len(question) < 5:
        return {
            "response_text": "*Ask the Astrologer*\n\nI can answer any astrology question!\n\n*Examples:*\n" +
                           "- \"What does Saturn return mean?\"\n" +
                           "- \"Which gemstone is good for Leo?\"\n" +
                           "- \"What is Manglik dosha?\"\n" +
                           "- \"How does Mercury retrograde affect us?\"",
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        result = await ask_astrologer(
            question=question,
            user_sign=user_sign if user_sign else None
        )

        if result["success"]:
            data = result["data"]
            answer = data.get("answer", "I couldn't find an answer.")

            response = f"*Astrologer's Answer*\n\n{answer}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, couldn't answer your question. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "An error occurred while consulting the astrologer.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 5. NUMEROLOGY HANDLER
# =============================================================================

async def handle_numerology(state: BotState) -> dict:
    """Handle numerology requests with local calculations."""
    entities = state.get("extracted_entities", {})
    name = entities.get("name", "").strip()
    birth_date = entities.get("birth_date", "").strip()

    if not name:
        return {
            "response_text": "*Numerology Analysis*\n\nPlease provide your name for numerology analysis.\n\n*Examples:*\n" +
                           "- \"Numerology for Rahul Kumar\"\n" +
                           "- \"My numerology - Priya Sharma, born 15-08-1990\"\n\n" +
                           "Adding your birth date gives a more complete reading!",
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        result = await calculate_numerology(
            name=name,
            birth_date=birth_date if birth_date else None
        )

        if result["success"]:
            data = result["data"]

            response = f"*Numerology Report*\n\n"
            response += f"*Name:* {name}\n"
            response += f"*Name Number:* {data['name_number']}\n"

            if data.get("name_meaning"):
                response += f"*Trait:* {data['name_meaning'].get('trait', 'N/A')}\n"
                response += f"*Description:* {data['name_meaning'].get('description', 'N/A')}\n"

            if data.get("life_path_number"):
                response += f"\n*Life Path Number:* {data['life_path_number']}\n"
                if data.get("life_path_meaning"):
                    response += f"*Life Path Trait:* {data['life_path_meaning'].get('trait', 'N/A')}\n"
                    response += f"*Description:* {data['life_path_meaning'].get('description', 'N/A')}\n"

            if data.get("lucky_numbers"):
                response += f"\n*Lucky Numbers:* {', '.join(map(str, data['lucky_numbers']))}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, couldn't generate numerology analysis. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "An error occurred during numerology analysis.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 6. TAROT READING HANDLER
# =============================================================================

async def handle_tarot(state: BotState) -> dict:
    """Handle tarot reading requests."""
    entities = state.get("extracted_entities", {})
    question = entities.get("tarot_question", "").strip()
    spread_type = entities.get("spread_type", "three_card").strip().lower()

    # Check for spread type in query
    original_query = state.get("current_query", "").lower()
    if "single" in original_query or "one card" in original_query:
        spread_type = "single"
    elif "celtic" in original_query or "full" in original_query or "detailed" in original_query:
        spread_type = "celtic_cross"

    # Extract question from query if not in entities
    if not question:
        if "about" in original_query:
            question = original_query.split("about", 1)[-1].strip()
        elif "for" in original_query and "tarot" in original_query:
            question = original_query.split("for", 1)[-1].strip()

    try:
        result = await draw_tarot(
            question=question if question else None,
            spread_type=spread_type
        )

        if result["success"]:
            data = result["data"]

            spread_names = {
                "single": "Single Card Reading",
                "three_card": "Three Card Spread",
                "celtic_cross": "Celtic Cross Spread"
            }
            spread_name = spread_names.get(spread_type, "Tarot Reading")

            response = f"*{spread_name}*\n\n"

            if question:
                response += f"*Question:* {question}\n\n"

            response += "*Cards Drawn:*\n"
            for card_info in data.get("cards", []):
                orientation = "Reversed" if card_info.get("reversed") else "Upright"
                response += f"- *{card_info['position']}:* {card_info['card']} ({orientation})\n"

            response += f"\n*Interpretation:*\n{data.get('interpretation', 'No interpretation available.')}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, couldn't generate tarot reading. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "An error occurred during tarot reading.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 7. PANCHANG HANDLER
# =============================================================================

async def handle_panchang(state: BotState) -> dict:
    """Handle Panchang (daily Vedic calendar) requests."""
    entities = state.get("extracted_entities", {})
    date_str = entities.get("date", "").strip()
    location = entities.get("location", "Delhi").strip()

    try:
        # Use today's date if not specified
        if not date_str:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")

        result = await calculate_panchang(
            date=date_str,
            place=location
        )

        if result["success"]:
            data = result["data"]

            response = f"*Panchang*\n\n"
            response += f"*Date:* {data.get('date', date_str)} ({data.get('day', '')})\n"
            response += f"*Location:* {location}\n\n"

            # Tithi
            tithi = data.get("tithi", {})
            response += f"*Tithi:* {tithi.get('name', 'N/A')} ({tithi.get('paksha', '')})\n"

            # Nakshatra
            nakshatra = data.get("nakshatra", {})
            response += f"*Nakshatra:* {nakshatra.get('name', 'N/A')} (Pada {nakshatra.get('pada', '')})\n"

            # Yoga
            response += f"*Yoga:* {data.get('yoga', 'N/A')}\n"

            # Karan
            karan = data.get("karan", [])
            if karan:
                response += f"*Karan:* {', '.join(karan)}\n"

            # Moon sign
            response += f"\n*Moon Sign:* {data.get('moon_sign', 'N/A')}\n"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"Sorry, couldn't get the Panchang. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "response_text": "An error occurred while fetching the Panchang.",
            "response_type": "text",
            "should_fallback": True,
        }


