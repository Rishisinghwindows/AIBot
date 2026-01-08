"""
Horoscope Tool

LangGraph tool for generating daily/weekly/monthly horoscopes.
Uses current planetary transits + knowledge layer for interpretation.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import logging

from common.astro.services.chart_engine import ChartEngine
from common.astro.services.knowledge_layer import KnowledgeLayer
from common.astro.services.interpreter import AstroInterpreter
from common.astro.services.validation import InputValidator

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class HoroscopePeriod(str, Enum):
    """Horoscope time periods."""
    TODAY = "today"
    TOMORROW = "tomorrow"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ZodiacSign(str, Enum):
    """Western zodiac signs (also used in Vedic as Rashi)."""
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


# Hindi/Sanskrit Rashi names (romanized)
RASHI_HINDI = {
    "Aries": "Mesh", "Taurus": "Vrishabh", "Gemini": "Mithun",
    "Cancer": "Kark", "Leo": "Singh", "Virgo": "Kanya",
    "Libra": "Tula", "Scorpio": "Vrishchik", "Sagittarius": "Dhanu",
    "Capricorn": "Makar", "Aquarius": "Kumbh", "Pisces": "Meen"
}

# Hindi script Rashi names
RASHI_HINDI_SCRIPT = {
    "मेष": "Aries", "वृषभ": "Taurus", "मिथुन": "Gemini",
    "कर्क": "Cancer", "सिंह": "Leo", "कन्या": "Virgo",
    "तुला": "Libra", "वृश्चिक": "Scorpio", "धनु": "Sagittarius",
    "मकर": "Capricorn", "कुंभ": "Aquarius", "मीन": "Pisces"
}

# Rashi lords (ruling planets)
RASHI_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class HoroscopeInput(BaseModel):
    """Input schema for horoscope generation."""

    sign: str = Field(
        ...,
        description="Zodiac sign (e.g., Aries, Leo, Mesh, Singh)"
    )
    period: HoroscopePeriod = Field(
        default=HoroscopePeriod.TODAY,
        description="Time period for horoscope"
    )
    include_details: bool = Field(
        default=True,
        description="Include detailed area-wise predictions"
    )
    birth_date: Optional[str] = Field(
        default=None,
        description="Optional birth date for personalized reading"
    )

    @field_validator("sign")
    @classmethod
    def normalize_sign(cls, v: str) -> str:
        """Normalize sign name to standard format."""
        if not v:
            raise ValueError("Zodiac sign is required")

        sign_clean = v.strip()

        # Check Hindi script names first (before title() which doesn't work on Hindi)
        if sign_clean in RASHI_HINDI_SCRIPT:
            return RASHI_HINDI_SCRIPT[sign_clean]

        sign_clean = sign_clean.title()

        # Check English names
        if sign_clean in [s.value for s in ZodiacSign]:
            return sign_clean

        # Check romanized Hindi names
        for eng, hindi in RASHI_HINDI.items():
            if sign_clean.lower() == hindi.lower():
                return eng

        # Try partial match
        for sign in ZodiacSign:
            if sign_clean.lower() in sign.value.lower():
                return sign.value

        raise ValueError(f"Invalid zodiac sign: {v}")


class TransitInfo(BaseModel):
    """Current planetary transit information."""
    planet: str
    current_sign: str
    aspect_to_sign: str  # How it aspects the queried sign
    influence: str  # Positive, Negative, Neutral


class HoroscopeOutput(BaseModel):
    """Output schema for horoscope."""

    success: bool = Field(..., description="Whether generation was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    # Basic info
    sign: Optional[str] = None
    sign_hindi: Optional[str] = None
    ruling_planet: Optional[str] = None
    element: Optional[str] = None
    period: Optional[str] = None
    date_range: Optional[str] = None

    # Main horoscope
    overall_theme: Optional[str] = None
    horoscope: Optional[str] = None

    # Detailed predictions
    love_relationships: Optional[str] = None
    career_finance: Optional[str] = None
    health_wellness: Optional[str] = None
    family_social: Optional[str] = None

    # Lucky elements
    lucky_number: Optional[int] = None
    lucky_color: Optional[str] = None
    lucky_day: Optional[str] = None
    lucky_time: Optional[str] = None

    # Transit influences
    key_transits: Optional[List[TransitInfo]] = None
    moon_phase: Optional[str] = None

    # Guidance
    advice: Optional[str] = None
    affirmation: Optional[str] = None
    caution: Optional[str] = None

    # Ratings (1-5)
    overall_rating: Optional[int] = None
    love_rating: Optional[int] = None
    career_rating: Optional[int] = None
    health_rating: Optional[int] = None

    # Metadata
    generated_at: Optional[str] = None


# =============================================================================
# TOOL IMPLEMENTATION
# =============================================================================

async def get_daily_horoscope(
    input_data: HoroscopeInput,
    llm=None
) -> HoroscopeOutput:
    """
    Generate horoscope for a zodiac sign.

    Uses:
    1. Current planetary transits (deterministic)
    2. Knowledge layer for sign attributes
    3. LLM for natural language generation (with guardrails)

    Args:
        input_data: Validated horoscope input
        llm: LLM instance for text generation

    Returns:
        HoroscopeOutput with predictions
    """
    try:
        # Initialize services
        chart_engine = ChartEngine()
        knowledge_layer = KnowledgeLayer()

        sign = input_data.sign

        # Get sign information
        sign_info = _get_sign_info(sign, knowledge_layer)

        # Calculate current transits
        target_date = _get_target_date(input_data.period)
        transits = chart_engine.calculate_transit_positions(target_date)

        # Analyze transits for this sign
        transit_analysis = _analyze_transits_for_sign(sign, transits)

        # Build base output
        output = HoroscopeOutput(
            success=True,
            sign=sign,
            sign_hindi=RASHI_HINDI.get(sign, sign),
            ruling_planet=RASHI_LORDS.get(sign, "Unknown"),
            element=sign_info.get("element"),
            period=input_data.period.value,
            date_range=_get_date_range(input_data.period, target_date),
            key_transits=transit_analysis.get("key_transits"),
            moon_phase=transit_analysis.get("moon_phase"),
            lucky_number=_calculate_lucky_number(sign, target_date),
            lucky_color=sign_info.get("lucky_color"),
            lucky_day=_get_lucky_day(sign),
            generated_at=datetime.now().isoformat()
        )

        # Generate horoscope text using LLM
        if llm:
            try:
                interpreter = AstroInterpreter(llm=llm)
                horoscope_response = await interpreter.generate_horoscope(
                    sign=sign,
                    period=input_data.period.value,
                    transits=transits,
                    sign_info=sign_info,
                    include_details=input_data.include_details
                )

                if horoscope_response:
                    output.overall_theme = horoscope_response.theme
                    output.horoscope = horoscope_response.main_prediction
                    output.love_relationships = horoscope_response.love
                    output.career_finance = horoscope_response.career
                    output.health_wellness = horoscope_response.health
                    output.family_social = horoscope_response.family
                    output.advice = horoscope_response.advice
                    output.affirmation = horoscope_response.affirmation
                    output.caution = horoscope_response.caution
                    output.overall_rating = horoscope_response.overall_rating
                    output.love_rating = horoscope_response.love_rating
                    output.career_rating = horoscope_response.career_rating
                    output.health_rating = horoscope_response.health_rating

            except Exception as e:
                logger.warning(f"LLM horoscope generation failed: {e}")
                # Fall back to template-based horoscope
                output = _generate_template_horoscope(output, sign_info, transit_analysis)
        else:
            # Generate template-based horoscope without LLM
            output = _generate_template_horoscope(output, sign_info, transit_analysis)

        return output

    except ValueError as e:
        return HoroscopeOutput(
            success=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Horoscope generation failed: {e}")
        return HoroscopeOutput(
            success=False,
            error=f"Failed to generate horoscope: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_sign_info(sign: str, knowledge_layer: KnowledgeLayer) -> Dict[str, Any]:
    """Get detailed information about a zodiac sign."""
    # Element mapping
    elements = {
        "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
        "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
        "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
        "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
    }

    # Quality mapping
    qualities = {
        "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
        "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
        "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable"
    }

    # Lucky colors
    lucky_colors = {
        "Aries": "Red", "Taurus": "Green", "Gemini": "Yellow",
        "Cancer": "Silver", "Leo": "Gold", "Virgo": "Navy Blue",
        "Libra": "Pink", "Scorpio": "Maroon", "Sagittarius": "Purple",
        "Capricorn": "Brown", "Aquarius": "Electric Blue", "Pisces": "Sea Green"
    }

    # Key traits
    traits = {
        "Aries": ["Bold", "Energetic", "Independent", "Pioneering"],
        "Taurus": ["Reliable", "Patient", "Practical", "Sensual"],
        "Gemini": ["Adaptable", "Curious", "Communicative", "Quick-witted"],
        "Cancer": ["Nurturing", "Intuitive", "Protective", "Emotional"],
        "Leo": ["Confident", "Creative", "Generous", "Dramatic"],
        "Virgo": ["Analytical", "Practical", "Diligent", "Modest"],
        "Libra": ["Diplomatic", "Fair", "Social", "Idealistic"],
        "Scorpio": ["Intense", "Passionate", "Resourceful", "Determined"],
        "Sagittarius": ["Optimistic", "Adventurous", "Philosophical", "Freedom-loving"],
        "Capricorn": ["Ambitious", "Disciplined", "Patient", "Responsible"],
        "Aquarius": ["Innovative", "Independent", "Humanitarian", "Original"],
        "Pisces": ["Compassionate", "Artistic", "Intuitive", "Gentle"]
    }

    return {
        "element": elements.get(sign),
        "quality": qualities.get(sign),
        "lucky_color": lucky_colors.get(sign),
        "traits": traits.get(sign, []),
        "ruling_planet": RASHI_LORDS.get(sign)
    }


def _get_target_date(period: HoroscopePeriod) -> date:
    """Get target date for horoscope."""
    today = date.today()

    if period == HoroscopePeriod.TOMORROW:
        return today + timedelta(days=1)
    return today


def _get_date_range(period: HoroscopePeriod, target_date: date) -> str:
    """Get date range string for the period."""
    if period == HoroscopePeriod.TODAY:
        return target_date.strftime("%B %d, %Y")
    elif period == HoroscopePeriod.TOMORROW:
        return target_date.strftime("%B %d, %Y")
    elif period == HoroscopePeriod.WEEKLY:
        week_end = target_date + timedelta(days=6)
        return f"{target_date.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
    else:  # monthly
        return target_date.strftime("%B %Y")


def _analyze_transits_for_sign(sign: str, transits: Dict) -> Dict[str, Any]:
    """Analyze how current transits affect a sign."""
    result = {
        "key_transits": [],
        "overall_energy": "neutral",
        "moon_phase": transits.get("moon_phase", "Unknown")
    }

    sign_index = list(RASHI_LORDS.keys()).index(sign)

    # Analyze each planet's transit
    for planet_name, planet_data in transits.get("planets", {}).items():
        transit_sign = planet_data.get("sign", "")
        transit_index = list(RASHI_LORDS.keys()).index(transit_sign) if transit_sign in RASHI_LORDS else 0

        # Calculate house position from sign (1st house = same sign)
        house_from_sign = ((transit_index - sign_index) % 12) + 1

        # Determine influence based on house
        influence = _get_house_influence(house_from_sign, planet_name)

        if influence != "Neutral" or planet_name in ["Jupiter", "Saturn", "Rahu", "Ketu"]:
            result["key_transits"].append(TransitInfo(
                planet=planet_name,
                current_sign=transit_sign,
                aspect_to_sign=f"{house_from_sign}th house",
                influence=influence
            ))

    return result


def _get_house_influence(house: int, planet: str) -> str:
    """Determine influence of planet in a house."""
    benefic_houses = [1, 5, 9, 11]
    malefic_houses = [6, 8, 12]

    if house in benefic_houses:
        if planet in ["Jupiter", "Venus"]:
            return "Very Positive"
        return "Positive"
    elif house in malefic_houses:
        if planet in ["Saturn", "Mars", "Rahu", "Ketu"]:
            return "Challenging"
        return "Mixed"
    else:
        return "Neutral"


def _calculate_lucky_number(sign: str, target_date: date) -> int:
    """Calculate lucky number for the day."""
    # Base number from sign
    sign_numbers = {
        "Aries": 9, "Taurus": 6, "Gemini": 5, "Cancer": 2,
        "Leo": 1, "Virgo": 5, "Libra": 6, "Scorpio": 9,
        "Sagittarius": 3, "Capricorn": 8, "Aquarius": 8, "Pisces": 3
    }

    base = sign_numbers.get(sign, 1)
    day_number = (target_date.day + target_date.month) % 9

    return ((base + day_number) % 9) + 1


def _get_lucky_day(sign: str) -> str:
    """Get lucky day for a sign."""
    lucky_days = {
        "Aries": "Tuesday", "Taurus": "Friday", "Gemini": "Wednesday",
        "Cancer": "Monday", "Leo": "Sunday", "Virgo": "Wednesday",
        "Libra": "Friday", "Scorpio": "Tuesday", "Sagittarius": "Thursday",
        "Capricorn": "Saturday", "Aquarius": "Saturday", "Pisces": "Thursday"
    }
    return lucky_days.get(sign, "Any day")


def _generate_template_horoscope(
    output: HoroscopeOutput,
    sign_info: Dict,
    transit_analysis: Dict
) -> HoroscopeOutput:
    """Generate template-based horoscope when LLM is not available."""

    # Generic templates based on transit energy
    positive_transit = any(
        t.influence in ["Positive", "Very Positive"]
        for t in (transit_analysis.get("key_transits") or [])
    )

    if positive_transit:
        output.overall_theme = f"A favorable period for {output.sign} natives"
        output.horoscope = (
            f"The planetary alignments indicate a positive phase for you. "
            f"Your ruling planet {output.ruling_planet} is supporting your endeavors. "
            f"This is a good time to take initiative and move forward with your plans. "
            f"Your natural {sign_info['element']} element energy is strong."
        )
        output.overall_rating = 4
    else:
        output.overall_theme = f"A period of growth and learning for {output.sign}"
        output.horoscope = (
            f"Current planetary transits encourage introspection and planning. "
            f"While some challenges may arise, they are opportunities for growth. "
            f"Focus on your strengths as a {output.sign} - being {', '.join(sign_info['traits'][:2])}. "
            f"Patience will be your ally during this period."
        )
        output.overall_rating = 3

    output.advice = (
        f"Trust your {sign_info['element']} element intuition and stay grounded in your values."
    )
    output.affirmation = f"I embrace the energy of {output.sign} and manifest my highest potential."

    return output


# =============================================================================
# LANGCHAIN TOOL WRAPPER
# =============================================================================

def get_horoscope_tool(llm=None):
    """Create a LangChain-compatible tool for horoscope generation."""
    from langchain_core.tools import StructuredTool

    async def _run_horoscope(
        sign: str,
        period: str = "today",
        include_details: bool = True
    ) -> Dict[str, Any]:
        """Generate horoscope for a zodiac sign."""
        input_data = HoroscopeInput(
            sign=sign,
            period=HoroscopePeriod(period) if period in [p.value for p in HoroscopePeriod] else HoroscopePeriod.TODAY,
            include_details=include_details
        )
        result = await get_daily_horoscope(input_data, llm=llm)
        return result.model_dump()

    return StructuredTool.from_function(
        coroutine=_run_horoscope,
        name="get_horoscope",
        description="""Generate daily, weekly, or monthly horoscope for a zodiac sign.

Includes:
- Overall theme and prediction
- Love & Relationships guidance
- Career & Finance insights
- Health & Wellness tips
- Lucky number, color, and day
- Current planetary influences

Signs: Aries, Taurus, Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces
Also accepts Hindi names: Mesh, Vrishabh, Mithun, Kark, Singh, Kanya, Tula, Vrishchik, Dhanu, Makar, Kumbh, Meen

Periods: today, tomorrow, weekly, monthly"""
    )
