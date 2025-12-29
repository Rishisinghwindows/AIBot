"""
Production Astrology Nodes

LangGraph nodes that integrate with the production astrology tools.
These replace the old astro_node.py handlers with proper architecture.

Architecture:
1. Node receives state with extracted entities
2. Validates and prepares input
3. Calls deterministic tool
4. Formats response for WhatsApp
5. Returns updated state
"""

from typing import Dict, Any, Optional
import logging

from bot.state import BotState

# Import production tools
from bot.astro.tools.birth_chart import (
    calculate_birth_chart,
    BirthChartInput,
    get_birth_chart_tool
)
from bot.astro.tools.compatibility import (
    calculate_compatibility,
    CompatibilityInput,
    PersonDetails,
    get_compatibility_tool
)
from bot.astro.tools.horoscope import (
    get_daily_horoscope,
    HoroscopeInput,
    HoroscopePeriod,
    get_horoscope_tool,
    RASHI_HINDI
)
from bot.astro.tools.question import (
    answer_astro_question,
    AstroQuestionInput,
    get_question_tool
)
from bot.astro.tools.panchang import (
    get_panchang,
    PanchangInput,
    get_panchang_tool
)

logger = logging.getLogger(__name__)


# =============================================================================
# ZODIAC SIGNS FOR VALIDATION
# =============================================================================

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


# =============================================================================
# 1. HOROSCOPE NODE
# =============================================================================

async def handle_horoscope(state: BotState, llm=None) -> dict:
    """
    Handle horoscope requests.

    Extracts sign and period from state, calls horoscope tool,
    formats response for WhatsApp.
    """
    entities = state.get("extracted_entities", {})
    sign = entities.get("astro_sign", "").strip()
    period_str = entities.get("astro_period", "today").strip().lower()

    # Validate sign is provided
    if not sign:
        signs_list = ", ".join(ZODIAC_SIGNS)
        return {
            "response_text": (
                "*Horoscope*\n\n"
                "Please specify your zodiac sign.\n\n"
                f"*Available signs:*\n{signs_list}\n\n"
                "*Examples:*\n"
                "- \"Aries horoscope\"\n"
                "- \"Leo weekly horoscope\"\n"
                "- \"Scorpio monthly prediction\""
            ),
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        # Map period string to enum
        period_map = {
            "today": HoroscopePeriod.TODAY,
            "tomorrow": HoroscopePeriod.TOMORROW,
            "weekly": HoroscopePeriod.WEEKLY,
            "week": HoroscopePeriod.WEEKLY,
            "monthly": HoroscopePeriod.MONTHLY,
            "month": HoroscopePeriod.MONTHLY,
        }
        period = period_map.get(period_str, HoroscopePeriod.TODAY)

        # Call tool
        input_data = HoroscopeInput(
            sign=sign,
            period=period,
            include_details=True
        )
        result = await get_daily_horoscope(input_data, llm=llm)

        if result.success:
            # Format response
            period_display = period.value.capitalize()
            sign_hindi = RASHI_HINDI.get(result.sign, "")
            sign_display = f"{result.sign} ({sign_hindi})" if sign_hindi else result.sign

            response = f"*{sign_display} {period_display} Horoscope*\n\n"

            if result.overall_theme:
                response += f"*Theme:* {result.overall_theme}\n\n"

            if result.horoscope:
                response += f"{result.horoscope}\n\n"

            # Add detailed sections if available
            if result.love_relationships:
                response += f"*Love:* {result.love_relationships}\n\n"
            if result.career_finance:
                response += f"*Career:* {result.career_finance}\n\n"
            if result.health_wellness:
                response += f"*Health:* {result.health_wellness}\n\n"

            # Lucky elements
            lucky_parts = []
            if result.lucky_number:
                lucky_parts.append(f"Number: {result.lucky_number}")
            if result.lucky_color:
                lucky_parts.append(f"Color: {result.lucky_color}")
            if result.lucky_day:
                lucky_parts.append(f"Day: {result.lucky_day}")

            if lucky_parts:
                response += f"*Lucky:* {' | '.join(lucky_parts)}\n\n"

            if result.advice:
                response += f"*Advice:* {result.advice}\n"

            if result.affirmation:
                response += f"\n_\"{result.affirmation}\"_"

            return {
                "tool_result": result.model_dump(),
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "response_text": f"Sorry, couldn't get the horoscope. {result.error or ''}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        logger.error(f"Horoscope handler error: {e}")
        return {
            "error": str(e),
            "response_text": "An error occurred while fetching the horoscope.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 2. BIRTH CHART (KUNDLI) NODE
# =============================================================================

async def handle_birth_chart(state: BotState, llm=None) -> dict:
    """
    Handle birth chart (Kundli) requests.

    Requires: birth_date, birth_time, birth_place
    Optional: name
    """
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
            "response_text": (
                "*Birth Chart (Kundli)*\n\n"
                "To generate your Kundli, I need:\n\n" +
                "\n".join([f"- {field}" for field in missing]) +
                "\n\n*Example:*\n"
                "\"Kundli for Rahul born on 15-08-1990 at 10:30 AM in Delhi\""
            ),
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        # Call tool
        input_data = BirthChartInput(
            name=name if name else None,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            include_interpretation=llm is not None
        )
        result = await calculate_birth_chart(input_data, llm=llm)

        if result.success:
            # Format response
            response = "*Birth Chart (Kundli)*\n\n"

            if result.name:
                response += f"*Name:* {result.name}\n"
            response += f"*Birth Date:* {result.birth_date}\n"
            response += f"*Birth Time:* {result.birth_time}\n"
            response += f"*Birth Place:* {result.birth_place}\n\n"

            response += f"*Ascendant (Lagna):* {result.ascendant_sign}\n"
            response += f"*Sun Sign:* {result.sun_sign}\n"
            response += f"*Moon Sign:* {result.moon_sign}\n"
            response += f"*Nakshatra:* {result.moon_nakshatra}\n\n"

            response += "*Vedic Details:*\n"
            if result.varna:
                response += f"- Varna: {result.varna}\n"
            if result.nadi:
                response += f"- Nadi: {result.nadi}\n"
            if result.yoni:
                response += f"- Yoni: {result.yoni}\n"
            if result.gana:
                response += f"- Gana: {result.gana}\n"
            if result.vashya:
                response += f"- Vashya: {result.vashya}\n"

            response += "\n*Planetary Positions:*\n"
            if result.planets:
                for planet in result.planets:
                    dignity_str = f" ({planet.dignity})" if planet.dignity else ""
                    response += f"- {planet.planet}: {planet.sign} ({planet.nakshatra}){dignity_str}\n"

            # Add yogas if present
            if result.yogas:
                present_yogas = [y for y in result.yogas if y.is_present]
                if present_yogas:
                    response += "\n*Yogas Found:*\n"
                    for yoga in present_yogas[:5]:  # Limit to 5
                        response += f"- {yoga.name}: {yoga.description[:100]}...\n"

            # Add current dasha
            if result.current_dasha:
                response += f"\n*Current Dasha:* {result.current_dasha.planet} "
                response += f"(until {result.current_dasha.end_date})\n"

            # Add interpretation if available
            if result.interpretation:
                response += f"\n*Interpretation:*\n{result.interpretation[:500]}..."

            return {
                "tool_result": result.model_dump(),
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "response_text": f"Sorry, couldn't generate the birth chart. {result.error or ''}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        logger.error(f"Birth chart handler error: {e}")
        return {
            "error": str(e),
            "response_text": "An error occurred while generating the birth chart.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 3. KUNDLI MATCHING NODE
# =============================================================================

async def handle_kundli_matching(state: BotState, llm=None) -> dict:
    """
    Handle Kundli matching (compatibility) requests.

    Required: DOB for both persons
    Optional: Names, times, places
    """
    entities = state.get("extracted_entities", {})

    person1_name = entities.get("person1_name", "Person 1").strip()
    person1_dob = entities.get("person1_dob", "").strip()
    person1_time = entities.get("person1_time", "12:00").strip()
    person1_place = entities.get("person1_place", "Delhi").strip()

    person2_name = entities.get("person2_name", "Person 2").strip()
    person2_dob = entities.get("person2_dob", "").strip()
    person2_time = entities.get("person2_time", "12:00").strip()
    person2_place = entities.get("person2_place", "Delhi").strip()

    # Check required fields
    missing = []
    if not person1_dob:
        missing.append("First person's date of birth")
    if not person2_dob:
        missing.append("Second person's date of birth")

    if missing:
        return {
            "response_text": (
                "*Kundli Matching*\n\n"
                "To check compatibility, I need:\n\n" +
                "\n".join([f"- {field}" for field in missing]) +
                "\n\n*Example:*\n"
                "\"Match kundli of Rahul (15-08-1990) and Priya (22-03-1992)\"\n\n"
                "Optionally include birth time and place for more accuracy."
            ),
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        # Call tool
        input_data = CompatibilityInput(
            person1=PersonDetails(
                name=person1_name,
                birth_date=person1_dob,
                birth_time=person1_time,
                birth_place=person1_place
            ),
            person2=PersonDetails(
                name=person2_name,
                birth_date=person2_dob,
                birth_time=person2_time,
                birth_place=person2_place
            ),
            include_interpretation=llm is not None
        )
        result = await calculate_compatibility(input_data, llm=llm)

        if result.success:
            # Format response
            response = "*Kundli Matching Report*\n\n"

            response += f"*{result.person1_name}*\n"
            response += f"  Moon Sign: {result.person1_moon_sign} | Nakshatra: {result.person1_nakshatra}\n\n"

            response += f"*{result.person2_name}*\n"
            response += f"  Moon Sign: {result.person2_moon_sign} | Nakshatra: {result.person2_nakshatra}\n\n"

            response += "*Ashtakoot Milan (8 Kootas):*\n"
            if result.koota_scores:
                for koota in result.koota_scores:
                    response += f"- {koota.name}: {koota.score}/{koota.max_score}\n"

            response += f"\n*Total Score:* {result.total_score}/36 ({result.percentage}%)\n"
            response += f"*Verdict:* {result.verdict}\n"

            # Add dosha warnings
            if result.nadi_dosha:
                response += "\n*Nadi Dosha:* Present (same Nadi)\n"
            if result.bhakoot_dosha:
                response += "*Bhakoot Dosha:* Present\n"

            if result.recommendation:
                response += f"\n*Recommendation:*\n{result.recommendation}"

            # Add interpretation if available
            if result.interpretation:
                response += f"\n\n*Analysis:*\n{result.interpretation[:400]}..."

            return {
                "tool_result": result.model_dump(),
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "response_text": f"Sorry, couldn't perform Kundli matching. {result.error or ''}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        logger.error(f"Kundli matching handler error: {e}")
        return {
            "error": str(e),
            "response_text": "An error occurred during Kundli matching.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 4. ASK ASTROLOGER NODE
# =============================================================================

async def handle_ask_astrologer(state: BotState, llm=None) -> dict:
    """
    Handle astrology Q&A requests.

    Uses knowledge layer + optional chart data for answers.
    """
    entities = state.get("extracted_entities", {})
    question = entities.get("astro_question", "").strip()
    user_sign = entities.get("user_sign", "").strip()

    # Get question from current query if not in entities
    if not question:
        question = state.get("current_query", "").strip()

    if not question or len(question) < 5:
        return {
            "response_text": (
                "*Ask the Astrologer*\n\n"
                "I can answer any astrology question!\n\n"
                "*Examples:*\n"
                "- \"What does Saturn return mean?\"\n"
                "- \"Which gemstone is good for Leo?\"\n"
                "- \"What is Manglik dosha?\"\n"
                "- \"How does Mercury retrograde affect us?\""
            ),
            "response_type": "text",
            "should_fallback": False,
        }

    try:
        # Get optional birth details
        birth_date = entities.get("birth_date", "").strip() or None
        birth_time = entities.get("birth_time", "").strip() or None
        birth_place = entities.get("birth_place", "").strip() or None

        # Call tool
        input_data = AstroQuestionInput(
            question=question,
            user_sign=user_sign if user_sign else None,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place
        )
        result = await answer_astro_question(input_data, llm=llm)

        if result.success:
            response = "*Astrologer's Answer*\n\n"

            if result.answer:
                response += result.answer

            # Add key concepts
            if result.key_concepts:
                response += f"\n\n*Key Concepts:* {', '.join(result.key_concepts)}"

            # Add practical advice
            if result.practical_advice:
                response += f"\n\n*Practical Advice:*\n{result.practical_advice}"

            # Add remedies if available
            if result.remedies:
                response += "\n\n*Suggested Remedies:*\n"
                for remedy in result.remedies[:3]:
                    response += f"- {remedy}\n"

            # Add disclaimer
            response += f"\n\n_{result.disclaimer}_"

            return {
                "tool_result": result.model_dump(),
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "response_text": f"Sorry, couldn't answer your question. {result.error or ''}",
                "response_type": "text",
                "should_fallback": False,
            }

    except ValueError as e:
        # Safety validation error
        return {
            "response_text": f"*Note:* {str(e)}",
            "response_type": "text",
            "should_fallback": False,
        }
    except Exception as e:
        logger.error(f"Ask astrologer handler error: {e}")
        return {
            "error": str(e),
            "response_text": "An error occurred while consulting the astrologer.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# 5. PANCHANG NODE
# =============================================================================

async def handle_panchang(state: BotState) -> dict:
    """
    Handle Panchang (daily Vedic calendar) requests.

    Optional: date, location
    """
    entities = state.get("extracted_entities", {})
    date_str = entities.get("date", "").strip() or None
    location = entities.get("location", "").strip() or "Delhi"

    try:
        # Call tool
        input_data = PanchangInput(
            date=date_str,
            location=location
        )
        result = await get_panchang(input_data)

        if result.success:
            response = "*Panchang*\n\n"

            response += f"*Date:* {result.date} ({result.day})\n"
            response += f"*Location:* {result.location}\n\n"

            # Sun/Moon
            if result.sunrise_sunset:
                response += f"*Sunrise:* {result.sunrise_sunset.sunrise}\n"
                response += f"*Sunset:* {result.sunrise_sunset.sunset}\n\n"

            # Five elements
            response += "*Pancha Anga (5 Elements):*\n"

            if result.tithi:
                paksha = result.tithi.paksha
                response += f"- *Tithi:* {result.tithi.name} ({paksha})\n"

            if result.nakshatra:
                response += f"- *Nakshatra:* {result.nakshatra.name} (Pada {result.nakshatra.pada})\n"

            if result.yoga:
                response += f"- *Yoga:* {result.yoga.name} ({result.yoga.nature})\n"

            if result.karan:
                response += f"- *Karan:* {result.karan.name}\n"

            response += f"- *Var:* {result.day} ({result.day_lord})\n"

            # Moon sign
            if result.moon_sign:
                response += f"\n*Moon Sign:* {result.moon_sign}\n"

            # Rahu Kaal
            if result.rahu_kaal:
                response += f"\n*Rahu Kaal:* {result.rahu_kaal.start} - {result.rahu_kaal.end}\n"
                response += f"  _{result.rahu_kaal.avoid}_\n"

            # Auspiciousness
            if result.overall_auspiciousness:
                response += f"\n*Overall:* {result.overall_auspiciousness}\n"

            if result.good_for:
                response += f"*Good For:* {', '.join(result.good_for[:3])}\n"

            if result.avoid and result.avoid[0] != "No major concerns":
                response += f"*Avoid:* {', '.join(result.avoid[:2])}\n"

            return {
                "tool_result": result.model_dump(),
                "response_text": response,
                "response_type": "text",
                "should_fallback": False,
            }
        else:
            return {
                "response_text": f"Sorry, couldn't get the Panchang. {result.error or ''}",
                "response_type": "text",
                "should_fallback": False,
            }

    except Exception as e:
        logger.error(f"Panchang handler error: {e}")
        return {
            "error": str(e),
            "response_text": "An error occurred while fetching the Panchang.",
            "response_type": "text",
            "should_fallback": True,
        }


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================

async def handle_astro(state: BotState, llm=None) -> dict:
    """Legacy handler - redirects to horoscope."""
    return await handle_horoscope(state, llm=llm)


# =============================================================================
# TOOL REGISTRY
# =============================================================================

def get_astrology_tools(llm=None):
    """
    Get all astrology tools for LangGraph agent.

    Returns a list of LangChain StructuredTool objects that can be
    used directly in a LangGraph agent.
    """
    return [
        get_birth_chart_tool(llm=llm),
        get_compatibility_tool(llm=llm),
        get_horoscope_tool(llm=llm),
        get_question_tool(llm=llm),
        get_panchang_tool()
    ]
