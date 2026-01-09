"""
Astrology Node Handlers

Handles all astrology-related intents:
1. Horoscope (Daily/Weekly/Monthly)
2. Birth Chart (Kundli)
3. Kundli Matching
4. Numerology
5. Tarot Reading
6. Panchang
"""

from app.graph.state import BotState
from app.services.astrology_service import get_astrology_service
from app.logger import logger
from app.i18n.translator import t, get_zodiac_in_language

ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]


# =============================================================================
# 1. HOROSCOPE HANDLER
# =============================================================================

async def handle_horoscope(state: BotState) -> dict:
    """Handle horoscope requests (daily/weekly/monthly)."""
    entities = state.get("extracted_entities", {})
    sign = entities.get("astro_sign", "").strip().lower()
    period = entities.get("astro_period", "today").strip().lower()

    # Get user's language for localized response
    lang = state.get("detected_language", "en")

    if not sign or sign not in ZODIAC_SIGNS:
        # Get zodiac signs in user's language
        signs_list = ", ".join([get_zodiac_in_language(s, lang) for s in ZODIAC_SIGNS])

        if lang == "hi":
            return {
                "response_text": (
                    "*राशिफल*\n\n"
                    "कृपया अपनी राशि बताएं।\n\n"
                    f"*उपलब्ध राशियां:*\n{signs_list}\n\n"
                    "*उदाहरण:*\n"
                    "- मेष राशिफल\n"
                    "- सिंह साप्ताहिक राशिफल\n"
                    "- वृश्चिक मासिक राशिफल"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": "get_horoscope",
            }
        else:
            return {
                "response_text": (
                    "*Horoscope*\n\n"
                    "Please specify your zodiac sign.\n\n"
                    f"*Available signs:*\n{signs_list}\n\n"
                    "*Examples:*\n"
                    "- Aries horoscope\n"
                    "- Leo weekly horoscope\n"
                    "- Scorpio monthly prediction"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": "get_horoscope",
            }

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.get_horoscope(sign=sign, period=period)

        if result.get("success"):
            data = result.get("data", {})
            horoscope = data.get("horoscope", data.get("description", "No prediction available"))

            # Get zodiac sign name in user's language
            sign_localized = get_zodiac_in_language(sign, lang)

            if lang == "hi":
                # Hindi response
                period_map = {"today": "आज का", "weekly": "साप्ताहिक", "monthly": "मासिक"}
                period_display = period_map.get(period, period.title())

                response_text = f"*{sign_localized} {period_display} राशिफल*\n\n{horoscope}"

                if data.get("lucky_number"):
                    response_text += f"\n\n*{t('horoscope.lucky_number', lang)}:* {data['lucky_number']}"
                if data.get("lucky_color"):
                    response_text += f"\n*{t('horoscope.lucky_color', lang)}:* {data['lucky_color']}"
                if data.get("advice"):
                    response_text += f"\n\n*{t('horoscope.advice', lang)}:* {data['advice']}"
            else:
                # English response
                period_display = period.capitalize() if period in ["today", "tomorrow", "yesterday"] else period.title()

                response_text = f"*{sign_localized} {period_display} Horoscope*\n\n{horoscope}"

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
                "intent": "get_horoscope",
            }
        else:
            error_msg = t("errors.general", lang) if lang != "en" else "Sorry, couldn't get the horoscope."
            return {
                "tool_result": result,
                "response_text": f"*{'राशिफल' if lang == 'hi' else 'Horoscope'}*\n\n{error_msg} {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "get_horoscope",
            }

    except Exception as e:
        logger.error(f"Horoscope handler error: {e}")
        error_msg = t("errors.general", lang) if lang != "en" else "An error occurred while fetching the horoscope."
        return {
            "error": str(e),
            "response_text": f"*{'राशिफल' if lang == 'hi' else 'Horoscope'}*\n\n{error_msg}\n\n_{t('common.try_again', lang)}_",
            "response_type": "text",
            "should_fallback": False,
            "intent": "get_horoscope",
        }


# =============================================================================
# 2. BIRTH CHART (KUNDLI) HANDLER
# =============================================================================

async def handle_birth_chart(state: BotState) -> dict:
    """Handle birth chart (Kundli) requests."""
    entities = state.get("extracted_entities", {})
    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()
    name = entities.get("name", "").strip()

    # Also check user_birth_details from state
    user_birth_details = state.get("user_birth_details")
    if user_birth_details and not birth_date:
        birth_date = user_birth_details.get("birth_date", "")
        birth_time = user_birth_details.get("birth_time", "")
        birth_place = user_birth_details.get("birth_place", "")

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
            "response_text": (
                "*Birth Chart (Kundli)*\n\n"
                "To generate your Kundli, I need:\n\n" +
                "\n".join([f"- {field}" for field in missing]) +
                "\n\n*Example:*\n\"Kundli for Rahul born on 15-08-1990 at 10:30 AM in Delhi\""
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "birth_chart",
        }

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.calculate_birth_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            name=name if name else None
        )

        if result.get("success"):
            data = result.get("data", {})

            # Format response
            response = f"*Birth Chart (Kundli)*\n\n"
            if name:
                response += f"*Name:* {name}\n"
            response += f"*Birth Date:* {birth_date}\n"
            response += f"*Birth Time:* {birth_time}\n"
            response += f"*Birth Place:* {birth_place}\n\n"

            response += f"*Sun Sign:* {data.get('sun_sign', 'N/A')}\n"
            response += f"*Moon Sign:* {data.get('moon_sign', 'N/A')}\n"
            response += f"*Nakshatra:* {data.get('moon_nakshatra', 'N/A')}\n"

            if data.get('ascendant'):
                response += f"*Ascendant (Lagna):* {data['ascendant'].get('sign', 'N/A')}\n"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "birth_chart",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Birth Chart*\n\nSorry, couldn't generate birth chart. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "birth_chart",
            }

    except Exception as e:
        logger.error(f"Birth chart handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Birth Chart*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "birth_chart",
        }


# =============================================================================
# 3. NUMEROLOGY HANDLER
# =============================================================================

async def handle_numerology(state: BotState) -> dict:
    """Handle numerology requests."""
    entities = state.get("extracted_entities", {})
    name = entities.get("name", "").strip()
    birth_date = entities.get("birth_date", "").strip()

    # Check user_birth_details
    user_birth_details = state.get("user_birth_details")
    if user_birth_details and not birth_date:
        birth_date = user_birth_details.get("birth_date", "")

    if not name and not birth_date:
        return {
            "response_text": (
                "*Numerology*\n\n"
                "I need your name or birth date for numerology analysis.\n\n"
                "*Examples:*\n"
                "- Numerology for Rahul\n"
                "- My life path number (birth date: 15-08-1990)"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "numerology",
        }

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.calculate_numerology(
            name=name if name else None,
            birth_date=birth_date if birth_date else None
        )

        if result.get("success"):
            data = result.get("data", {})
            response = "*Numerology Analysis*\n\n"

            # Name number
            if data.get("name"):
                response += f"*Name:* {data['name']}\n"
            if data.get("name_number"):
                name_meaning = data.get("name_meaning", {})
                trait = name_meaning.get("trait", "") if isinstance(name_meaning, dict) else str(name_meaning)
                desc = name_meaning.get("description", "") if isinstance(name_meaning, dict) else ""
                response += f"*Expression Number:* {data['name_number']} ({trait})\n"
                if desc:
                    response += f"_{desc}_\n\n"

            # Life path number
            if data.get("life_path_number"):
                lp_meaning = data.get("life_path_meaning", {})
                trait = lp_meaning.get("trait", "") if isinstance(lp_meaning, dict) else str(lp_meaning)
                desc = lp_meaning.get("description", "") if isinstance(lp_meaning, dict) else ""
                response += f"*Life Path Number:* {data['life_path_number']} ({trait})\n"
                if desc:
                    response += f"_{desc}_\n\n"

            if data.get("lucky_numbers"):
                response += f"*Lucky Numbers:* {', '.join(map(str, data['lucky_numbers']))}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "numerology",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Numerology*\n\nSorry, couldn't perform analysis. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "numerology",
            }

    except Exception as e:
        logger.error(f"Numerology handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Numerology*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "numerology",
        }


# =============================================================================
# 4. TAROT READING HANDLER
# =============================================================================

async def handle_tarot(state: BotState) -> dict:
    """Handle tarot reading requests."""
    entities = state.get("extracted_entities", {})
    spread_type = entities.get("spread_type", "three_card")
    question = entities.get("question", "").strip()

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.draw_tarot(
            spread_type=spread_type,
            question=question if question else None
        )

        if result.get("success"):
            data = result.get("data", {})
            cards = data.get("cards", [])

            response = "*Tarot Reading*\n\n"

            if question:
                response += f"*Question:* {question}\n\n"

            for i, card in enumerate(cards, 1):
                position = card.get("position", f"Card {i}")
                card_name = card.get("card", "Unknown Card")  # Key is "card", not "name"
                meaning = card.get("meaning", "")
                is_reversed = card.get("reversed", False)

                response += f"*{position}:* {card_name}"
                if is_reversed:
                    response += " (Reversed)"
                response += "\n"
                if meaning:
                    response += f"_{meaning}_\n\n"

            if data.get("overall_interpretation"):
                response += f"*Overall:* {data['overall_interpretation']}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "tarot_reading",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Tarot Reading*\n\nSorry, couldn't draw cards. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "tarot_reading",
            }

    except Exception as e:
        logger.error(f"Tarot handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Tarot Reading*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "tarot_reading",
        }


# =============================================================================
# 5. PANCHANG HANDLER
# =============================================================================

async def handle_panchang(state: BotState) -> dict:
    """Handle panchang requests."""
    entities = state.get("extracted_entities", {})
    location = entities.get("location", "Delhi")

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.get_panchang(place=location)

        if result.get("success"):
            data = result.get("data", {})

            response = f"*Today's Panchang*\n*Location:* {location}\n\n"

            # Parse tithi (can be string or dict)
            tithi = data.get('tithi', 'N/A')
            if isinstance(tithi, dict):
                paksha = tithi.get('paksha', '')
                response += f"*Tithi:* {tithi.get('name', 'N/A')} ({paksha})\n"
            else:
                response += f"*Tithi:* {tithi}\n"
                if data.get('paksha'):
                    response += f"*Paksha:* {data['paksha']}\n"

            # Parse nakshatra (can be string or dict)
            nakshatra = data.get('nakshatra', 'N/A')
            if isinstance(nakshatra, dict):
                response += f"*Nakshatra:* {nakshatra.get('name', 'N/A')} (Pada {nakshatra.get('pada', '')})\n"
            else:
                response += f"*Nakshatra:* {nakshatra}\n"

            response += f"*Yoga:* {data.get('yoga', 'N/A')}\n"

            # Parse karana (can be string or list)
            karana = data.get('karana') or data.get('karan', 'N/A')
            if isinstance(karana, list):
                response += f"*Karana:* {', '.join(karana)}\n"
            else:
                response += f"*Karana:* {karana}\n"

            if data.get('moon_sign'):
                response += f"*Moon Sign:* {data['moon_sign']}\n"

            response += "\n"
            if data.get('sunrise'):
                response += f"*Sunrise:* {data['sunrise']}\n"
            if data.get('sunset'):
                response += f"*Sunset:* {data['sunset']}\n"

            if data.get('rahu_kaal'):
                response += f"\n*Rahu Kaal:* {data['rahu_kaal']}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "get_panchang",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Panchang*\n\nSorry, couldn't fetch panchang. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "get_panchang",
            }

    except Exception as e:
        logger.error(f"Panchang handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Panchang*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "get_panchang",
        }


# =============================================================================
# 6. DOSHA CHECK HANDLER
# =============================================================================

async def handle_dosha(state: BotState) -> dict:
    """Handle dosha check requests (Manglik, Kaal Sarp, Sade Sati, Pitra)."""
    entities = state.get("extracted_entities", {})
    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()
    dosha_type = entities.get("dosha_type")

    # Check user_birth_details from state
    user_birth_details = state.get("user_birth_details")
    if user_birth_details and not birth_date:
        birth_date = user_birth_details.get("birth_date", "")
        birth_time = user_birth_details.get("birth_time", "")
        birth_place = user_birth_details.get("birth_place", "")

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
            "response_text": (
                "*Dosha Check*\n\n"
                "To check for doshas, I need:\n\n" +
                "\n".join([f"- {field}" for field in missing]) +
                "\n\n*Available Dosha Checks:*\n"
                "- Manglik Dosha\n"
                "- Kaal Sarp Dosha\n"
                "- Sade Sati\n"
                "- Pitra Dosha\n\n"
                "*Example:*\n\"Check manglik dosha for birth on 15-08-1990 at 10:30 AM in Delhi\""
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "check_dosha",
        }

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.check_dosha(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            dosha_type=dosha_type
        )

        if result.get("success"):
            data = result.get("data", {})
            doshas = data.get("doshas", {})

            response = "*Dosha Analysis*\n\n"
            response += f"*Birth:* {birth_date} at {birth_time}\n"
            response += f"*Place:* {birth_place}\n\n"

            for dosha_name, dosha_info in doshas.items():
                dosha_title = dosha_name.replace("_", " ").title()
                if dosha_name == "sade_sati":
                    is_active = dosha_info.get("active", False)
                    response += f"*{dosha_title}:* {'Active' if is_active else 'Not Active'}\n"
                    if is_active and dosha_info.get("phase"):
                        response += f"  Phase: {dosha_info['phase']}\n"
                else:
                    is_present = dosha_info.get("present", False)
                    response += f"*{dosha_title}:* {'Present' if is_present else 'Not Present'}\n"
                    if is_present and dosha_info.get("intensity"):
                        response += f"  Intensity: {dosha_info['intensity']}\n"

                if dosha_info.get("description"):
                    response += f"  _{dosha_info['description']}_\n"
                if dosha_info.get("remedy"):
                    response += f"  *Remedy:* {dosha_info['remedy']}\n"
                response += "\n"

            if data.get("overall_recommendation"):
                response += f"*Note:* _{data['overall_recommendation']}_"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "check_dosha",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Dosha Check*\n\nSorry, couldn't check doshas. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "check_dosha",
            }

    except Exception as e:
        logger.error(f"Dosha handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Dosha Check*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "check_dosha",
        }


# =============================================================================
# 7. KUNDLI MATCHING HANDLER
# =============================================================================

async def handle_kundli_matching(state: BotState) -> dict:
    """Handle kundli matching (compatibility) requests."""
    entities = state.get("extracted_entities", {})

    # Extract details for both persons
    person1_dob = entities.get("person1_dob", "").strip()
    person2_dob = entities.get("person2_dob", "").strip()
    person1_name = entities.get("person1_name", "Person 1").strip()
    person2_name = entities.get("person2_name", "Person 2").strip()

    if not person1_dob or not person2_dob:
        return {
            "response_text": (
                "*Kundli Matching (Gun Milan)*\n\n"
                "To check compatibility, I need birth dates of both persons.\n\n"
                "*Required:*\n"
                "- Person 1's birth date\n"
                "- Person 2's birth date\n\n"
                "*Example:*\n"
                "\"Match kundli for Rahul born 15-08-1990 and Priya born 20-03-1992\""
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "kundli_matching",
        }

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.calculate_kundli_matching(
            person1_dob=person1_dob,
            person2_dob=person2_dob,
            person1_name=person1_name,
            person2_name=person2_name
        )

        if result.get("success"):
            data = result.get("data", {})

            p1 = data.get("person1", {})
            p2 = data.get("person2", {})

            response = "*Kundli Matching (Ashtakoot Milan)*\n\n"
            response += f"*{p1.get('name', 'Person 1')}:* {p1.get('dob', 'N/A')} ({p1.get('moon_sign', 'N/A')})\n"
            response += f"*{p2.get('name', 'Person 2')}:* {p2.get('dob', 'N/A')} ({p2.get('moon_sign', 'N/A')})\n\n"

            # Score breakdown
            scores = data.get("scores", {})
            response += "*Score Breakdown:*\n"
            for koota, info in scores.items():
                koota_name = koota.replace("_", " ").title()
                response += f"• {koota_name}: {info['score']}/{info['max']}\n"

            response += f"\n*Total Score:* {data.get('total_score', 0)}/{data.get('max_score', 36)} "
            response += f"({data.get('percentage', 0)}%)\n\n"

            response += f"*Verdict:* {data.get('verdict', 'N/A')}\n"
            response += f"_{data.get('recommendation', '')}_"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "kundli_matching",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Kundli Matching*\n\nSorry, couldn't perform matching. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "kundli_matching",
            }

    except Exception as e:
        logger.error(f"Kundli matching handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Kundli Matching*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "kundli_matching",
        }


# =============================================================================
# 8. LIFE PREDICTION HANDLER
# =============================================================================

async def handle_life_prediction(state: BotState) -> dict:
    """Handle life prediction requests (career, marriage, health, etc.)."""
    entities = state.get("extracted_entities", {})
    birth_date = entities.get("birth_date", "").strip()
    birth_time = entities.get("birth_time", "").strip()
    birth_place = entities.get("birth_place", "").strip()
    prediction_type = entities.get("prediction_type", "general").strip().lower()

    # Check user_birth_details from state
    user_birth_details = state.get("user_birth_details")
    if user_birth_details and not birth_date:
        birth_date = user_birth_details.get("birth_date", "")
        birth_time = user_birth_details.get("birth_time", "")
        birth_place = user_birth_details.get("birth_place", "")

    # Check required fields
    missing = []
    if not birth_date:
        missing.append("birth date")
    if not birth_time:
        missing.append("birth time")
    if not birth_place:
        missing.append("birth place")

    if missing:
        return {
            "response_text": (
                "*Life Prediction*\n\n"
                "To generate predictions, I need:\n\n" +
                "\n".join([f"- {field}" for field in missing]) +
                "\n\n*Available Predictions:*\n"
                "- General (all areas)\n"
                "- Marriage\n"
                "- Career\n"
                "- Children\n"
                "- Wealth\n"
                "- Health\n"
                "- Foreign Settlement\n\n"
                "*Example:*\n\"Career prediction for birth on 15-08-1990 at 10:30 in Delhi\""
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "life_prediction",
        }

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.get_life_prediction(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            prediction_type=prediction_type
        )

        if result.get("success"):
            data = result.get("data", {})

            if prediction_type == "general":
                predictions = data.get("predictions", {})
                response = "*Life Predictions*\n\n"

                for pred_type, pred_info in predictions.items():
                    title = pred_info.get("title", pred_type.title())
                    response += f"*{title}*\n"
                    for key, value in pred_info.items():
                        if key not in ["title"] and value:
                            if isinstance(value, list):
                                value = ", ".join(map(str, value))
                            key_formatted = key.replace("_", " ").title()
                            response += f"• {key_formatted}: {value}\n"
                    response += "\n"
            else:
                prediction = data.get("prediction", {})
                title = prediction.get("title", prediction_type.title())
                response = f"*{title}*\n\n"

                for key, value in prediction.items():
                    if key not in ["title"] and value:
                        if isinstance(value, list):
                            value = ", ".join(map(str, value))
                        key_formatted = key.replace("_", " ").title()
                        response += f"*{key_formatted}:* {value}\n"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "life_prediction",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Life Prediction*\n\nSorry, couldn't generate prediction. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "life_prediction",
            }

    except Exception as e:
        logger.error(f"Life prediction handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Life Prediction*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "life_prediction",
        }


# =============================================================================
# 9. ASK ASTROLOGER HANDLER
# =============================================================================

async def handle_ask_astrologer(state: BotState) -> dict:
    """Handle general astrology questions."""
    message = state.get("current_message", {})
    text = message.get("text", "").strip()
    entities = state.get("extracted_entities", {})
    user_sign = entities.get("astro_sign", "")

    if not text:
        return {
            "response_text": (
                "*Ask the Astrologer*\n\n"
                "Ask me any astrology question!\n\n"
                "*Popular Topics:*\n"
                "- Mercury retrograde effects\n"
                "- Gemstones for your sign\n"
                "- Manglik dosha explained\n"
                "- Sade Sati meaning\n"
                "- Planetary transits\n\n"
                "*Example:*\n\"What gemstone should a Leo wear?\""
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": "ask_astrologer",
        }

    try:
        astrology_service = get_astrology_service()
        result = await astrology_service.ask_astrologer(
            question=text,
            user_sign=user_sign if user_sign else None
        )

        if result.get("success"):
            data = result.get("data", {})
            answer = data.get("answer", "I couldn't find an answer to that question.")

            response = "*Astrology Insight*\n\n"
            response += f"*Q:* {data.get('question', text)}\n\n"
            response += f"*A:* {answer}"

            return {
                "tool_result": result,
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
                "intent": "ask_astrologer",
            }
        else:
            return {
                "tool_result": result,
                "response_text": f"*Ask Astrologer*\n\nSorry, couldn't answer. {result.get('error', '')}",
                "response_type": "text",
                "should_fallback": False,
                "intent": "ask_astrologer",
            }

    except Exception as e:
        logger.error(f"Ask astrologer handler error: {e}")
        return {
            "error": str(e),
            "response_text": "*Ask Astrologer*\n\nAn error occurred. Please try again.",
            "response_type": "text",
            "should_fallback": False,
            "intent": "ask_astrologer",
        }
