"""
Birth Chart (Kundli) Tool

LangGraph tool for calculating and interpreting Vedic birth charts.
Follows the production architecture:
1. Validate inputs
2. Calculate deterministic chart data
3. Evaluate Jyotish rules
4. Generate LLM interpretation with guardrails
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field, field_validator
import logging

from common.astro.services.chart_engine import ChartEngine
from common.astro.services.rules_engine import RulesEngine
from common.astro.services.knowledge_layer import KnowledgeLayer
from common.astro.services.interpreter import AstroInterpreter
from common.astro.services.validation import InputValidator, ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class BirthChartInput(BaseModel):
    """Input schema for birth chart calculation."""

    name: Optional[str] = Field(
        default=None,
        description="Person's name (optional)",
        max_length=100
    )
    birth_date: str = Field(
        ...,
        description="Birth date (YYYY-MM-DD, DD-MM-YYYY, or DD/MM/YYYY)",
        examples=["1990-08-15", "15-08-1990", "15/08/1990"]
    )
    birth_time: str = Field(
        ...,
        description="Birth time (HH:MM, HH:MM:SS, or with AM/PM)",
        examples=["10:30", "10:30:00", "10:30 AM"]
    )
    birth_place: str = Field(
        ...,
        description="Birth city/location name",
        examples=["Delhi", "Mumbai", "New York"]
    )
    include_interpretation: bool = Field(
        default=True,
        description="Whether to include LLM interpretation"
    )

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Birth date is required")
        return v.strip()

    @field_validator("birth_time")
    @classmethod
    def validate_birth_time(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Birth time is required")
        return v.strip()

    @field_validator("birth_place")
    @classmethod
    def validate_birth_place(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Birth place is required")
        return v.strip()


class PlanetInfo(BaseModel):
    """Planet position information."""
    planet: str
    sign: str
    sign_hindi: str
    degree: float
    nakshatra: str
    pada: int
    house: int
    dignity: Optional[str] = None
    retrograde: bool = False


class YogaInfo(BaseModel):
    """Yoga information."""
    name: str
    type: str
    description: str
    planets_involved: List[str]
    is_present: bool
    strength: str


class DoshaInfo(BaseModel):
    """Dosha information."""
    name: str
    is_present: bool
    severity: str
    factors: List[str]
    remedies: Optional[List[str]] = None


class DashaInfo(BaseModel):
    """Dasha period information."""
    planet: str
    start_date: str
    end_date: str
    is_current: bool
    sub_period: Optional[str] = None


class BirthChartOutput(BaseModel):
    """Output schema for birth chart calculation."""

    success: bool = Field(..., description="Whether calculation was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    # Basic info
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_place: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

    # Ascendant
    ascendant_sign: Optional[str] = None
    ascendant_degree: Optional[float] = None
    ascendant_nakshatra: Optional[str] = None

    # Key positions
    sun_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    moon_nakshatra: Optional[str] = None

    # Vedic attributes
    varna: Optional[str] = None
    nadi: Optional[str] = None
    yoni: Optional[str] = None
    gana: Optional[str] = None
    vashya: Optional[str] = None

    # Detailed positions
    planets: Optional[List[PlanetInfo]] = None

    # Rules evaluation
    yogas: Optional[List[YogaInfo]] = None
    doshas: Optional[List[DoshaInfo]] = None
    current_dasha: Optional[DashaInfo] = None
    dasha_sequence: Optional[List[DashaInfo]] = None

    # LLM interpretation
    interpretation: Optional[str] = None
    personality_summary: Optional[str] = None
    career_guidance: Optional[str] = None
    relationship_insights: Optional[str] = None

    # Metadata
    calculation_method: str = "Swiss Ephemeris"
    ayanamsa: str = "Lahiri"
    house_system: str = "Whole Sign"


# =============================================================================
# TOOL IMPLEMENTATION
# =============================================================================

async def calculate_birth_chart(
    input_data: BirthChartInput,
    llm=None
) -> BirthChartOutput:
    """
    Calculate a complete Vedic birth chart with interpretation.

    This is the main entry point for birth chart calculations.

    Flow:
    1. Validate all inputs
    2. Calculate chart using Swiss Ephemeris (deterministic)
    3. Evaluate Jyotish rules (deterministic)
    4. Generate LLM interpretation (with guardrails)

    Args:
        input_data: Validated birth chart input
        llm: Optional LLM instance for interpretation

    Returns:
        BirthChartOutput with chart data and interpretation
    """
    try:
        # Initialize services
        validator = InputValidator()
        chart_engine = ChartEngine()
        rules_engine = RulesEngine()
        knowledge_layer = KnowledgeLayer()

        # Step 1: Validate inputs
        validation_result = validator.validate_birth_details(
            name=input_data.name,
            date_str=input_data.birth_date,
            time_str=input_data.birth_time,
            location=input_data.birth_place,
            require_time=True
        )

        if not validation_result.is_valid:
            return BirthChartOutput(
                success=False,
                error=validation_result.error
            )

        validated = validation_result.value
        location = validated["location"]

        # Step 2: Calculate chart (deterministic)
        chart_data = chart_engine.calculate_chart(
            birth_date=validated["date"],
            birth_time=validated["time"],
            latitude=location.latitude,
            longitude=location.longitude,
            timezone=location.timezone
        )

        # Step 3: Evaluate rules (deterministic)
        rules_output = rules_engine.evaluate_chart(chart_data)

        # Step 4: Build output
        output = BirthChartOutput(
            success=True,
            name=validated.get("name"),
            birth_date=str(validated["date"]),
            birth_time=str(validated["time"]),
            birth_place=location.city,
            latitude=location.latitude,
            longitude=location.longitude,
            timezone=location.timezone,
            ascendant_sign=chart_data.ascendant.sign.value if chart_data.ascendant else None,
            ascendant_degree=chart_data.ascendant.degree if chart_data.ascendant else None,
            ascendant_nakshatra=chart_data.ascendant.nakshatra.value if chart_data.ascendant and chart_data.ascendant.nakshatra else None,
            sun_sign=_get_planet_sign(chart_data, "Sun"),
            moon_sign=_get_planet_sign(chart_data, "Moon"),
            moon_nakshatra=_get_planet_nakshatra(chart_data, "Moon"),
            varna=chart_data.varna,
            nadi=chart_data.nadi,
            yoni=chart_data.yoni,
            gana=chart_data.gana,
            vashya=chart_data.vashya,
            planets=_format_planets(chart_data, rules_output),
            yogas=_format_yogas(rules_output, knowledge_layer),
            doshas=_format_doshas(rules_output, knowledge_layer),
            current_dasha=_format_current_dasha(rules_output),
            dasha_sequence=_format_dasha_sequence(rules_output),
        )

        # Step 5: Generate interpretation (if requested and LLM available)
        if input_data.include_interpretation and llm:
            try:
                interpreter = AstroInterpreter(llm=llm)
                interpretation_response = await interpreter.interpret_chart(
                    chart_data=chart_data,
                    rules_output=rules_output,
                    focus_areas=["personality", "career", "relationships"]
                )

                if interpretation_response:
                    output.interpretation = interpretation_response.summary
                    for section in interpretation_response.sections:
                        if section.title.lower() == "personality":
                            output.personality_summary = section.content
                        elif section.title.lower() == "career":
                            output.career_guidance = section.content
                        elif section.title.lower() == "relationships":
                            output.relationship_insights = section.content

            except Exception as e:
                logger.warning(f"Interpretation failed, returning chart data only: {e}")
                # Chart data is still valid, just no interpretation

        return output

    except ValidationError as e:
        return BirthChartOutput(
            success=False,
            error=f"Validation error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Birth chart calculation failed: {e}")
        return BirthChartOutput(
            success=False,
            error=f"Calculation failed: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_planet_sign(chart_data, planet_name: str) -> Optional[str]:
    """Get planet's zodiac sign from chart data."""
    for planet in chart_data.planets:
        if planet.name.value == planet_name:
            return planet.sign.value
    return None


def _get_planet_nakshatra(chart_data, planet_name: str) -> Optional[str]:
    """Get planet's nakshatra from chart data."""
    for planet in chart_data.planets:
        if planet.name.value == planet_name:
            return planet.nakshatra.value if planet.nakshatra else None
    return None


def _format_planets(chart_data, rules_output) -> List[PlanetInfo]:
    """Format planet positions for output."""
    planets = []

    # Sign Hindi names
    sign_hindi = {
        "Aries": "Mesh", "Taurus": "Vrishabh", "Gemini": "Mithun",
        "Cancer": "Kark", "Leo": "Singh", "Virgo": "Kanya",
        "Libra": "Tula", "Scorpio": "Vrishchik", "Sagittarius": "Dhanu",
        "Capricorn": "Makar", "Aquarius": "Kumbh", "Pisces": "Meen"
    }

    # Get dignity info
    dignity_map = {}
    if rules_output and rules_output.dignities:
        for dignity in rules_output.dignities:
            dignity_map[dignity.planet] = dignity.dignity_type

    for planet in chart_data.planets:
        sign_name = planet.sign.value if planet.sign else "Unknown"
        planets.append(PlanetInfo(
            planet=planet.name.value,
            sign=sign_name,
            sign_hindi=sign_hindi.get(sign_name, sign_name),
            degree=round(planet.degree, 2),
            nakshatra=planet.nakshatra.value if planet.nakshatra else "Unknown",
            pada=planet.pada if planet.pada else 1,
            house=planet.house if planet.house else 1,
            dignity=dignity_map.get(planet.name.value),
            retrograde=planet.retrograde if hasattr(planet, 'retrograde') else False
        ))

    return planets


def _format_yogas(rules_output, knowledge_layer) -> List[YogaInfo]:
    """Format yoga results for output."""
    yogas = []

    if not rules_output or not rules_output.yogas:
        return yogas

    for yoga in rules_output.yogas:
        # Get additional info from knowledge layer
        yoga_desc = knowledge_layer.get_yoga_description(yoga.name)

        yogas.append(YogaInfo(
            name=yoga.name,
            type=yoga.yoga_type,
            description=yoga_desc.get("description", yoga.description) if yoga_desc else yoga.description,
            planets_involved=yoga.planets_involved,
            is_present=yoga.is_present,
            strength=yoga.strength.value if hasattr(yoga.strength, 'value') else str(yoga.strength)
        ))

    return yogas


def _format_doshas(rules_output, knowledge_layer) -> List[DoshaInfo]:
    """Format dosha results for output."""
    doshas = []

    if not rules_output or not rules_output.doshas:
        return doshas

    for dosha in rules_output.doshas:
        doshas.append(DoshaInfo(
            name=dosha.name,
            is_present=dosha.is_present,
            severity=dosha.severity.value if hasattr(dosha.severity, 'value') else str(dosha.severity),
            factors=dosha.contributing_factors,
            remedies=dosha.remedies if hasattr(dosha, 'remedies') else None
        ))

    return doshas


def _format_current_dasha(rules_output) -> Optional[DashaInfo]:
    """Format current dasha for output."""
    if not rules_output or not rules_output.dashas:
        return None

    for dasha in rules_output.dashas:
        if dasha.is_current:
            return DashaInfo(
                planet=dasha.planet,
                start_date=str(dasha.start_date),
                end_date=str(dasha.end_date),
                is_current=True,
                sub_period=dasha.sub_period if hasattr(dasha, 'sub_period') else None
            )

    return None


def _format_dasha_sequence(rules_output) -> List[DashaInfo]:
    """Format dasha sequence for output."""
    dashas = []

    if not rules_output or not rules_output.dashas:
        return dashas

    for dasha in rules_output.dashas[:5]:  # Next 5 periods
        dashas.append(DashaInfo(
            planet=dasha.planet,
            start_date=str(dasha.start_date),
            end_date=str(dasha.end_date),
            is_current=dasha.is_current,
            sub_period=dasha.sub_period if hasattr(dasha, 'sub_period') else None
        ))

    return dashas


# =============================================================================
# LANGCHAIN TOOL WRAPPER
# =============================================================================

def get_birth_chart_tool(llm=None):
    """
    Create a LangChain-compatible tool for birth chart calculation.

    Returns a callable tool that can be used in LangGraph workflows.
    """
    from langchain_core.tools import StructuredTool

    async def _run_birth_chart(
        birth_date: str,
        birth_time: str,
        birth_place: str,
        name: str = None,
        include_interpretation: bool = True
    ) -> Dict[str, Any]:
        """Calculate Vedic birth chart (Kundli) with planetary positions and interpretations."""
        input_data = BirthChartInput(
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place,
            include_interpretation=include_interpretation
        )
        result = await calculate_birth_chart(input_data, llm=llm)
        return result.model_dump()

    return StructuredTool.from_function(
        coroutine=_run_birth_chart,
        name="calculate_birth_chart",
        description="""Calculate a complete Vedic birth chart (Kundli) with:
- Planetary positions in signs and nakshatras
- Ascendant (Lagna) details
- Vedic attributes (Varna, Nadi, Yoni, Gana, Vashya)
- Yoga analysis (beneficial combinations)
- Dosha analysis (Manglik, Kaal Sarp)
- Vimshottari Dasha periods
- Personalized interpretation

Required: birth_date, birth_time, birth_place
Optional: name, include_interpretation""",
        args_schema=BirthChartInput
    )
