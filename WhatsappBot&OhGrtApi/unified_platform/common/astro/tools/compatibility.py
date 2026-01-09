"""
Kundli Matching / Compatibility Tool

LangGraph tool for calculating Ashtakoot Milan (36-point compatibility).
All calculations are deterministic using the Rules Engine.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
import logging

from common.astro.services.chart_engine import ChartEngine
from common.astro.services.rules_engine import RulesEngine
from common.astro.services.knowledge_layer import KnowledgeLayer
from common.astro.services.interpreter import AstroInterpreter
from common.astro.services.validation import InputValidator

logger = logging.getLogger(__name__)


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class PersonDetails(BaseModel):
    """Details for one person in compatibility matching."""
    name: str = Field(..., description="Person's name", min_length=1, max_length=100)
    birth_date: str = Field(..., description="Birth date (YYYY-MM-DD or DD-MM-YYYY)")
    birth_time: Optional[str] = Field(default="12:00", description="Birth time (defaults to noon if unknown)")
    birth_place: str = Field(default="Delhi", description="Birth city/location")


class CompatibilityInput(BaseModel):
    """Input schema for compatibility calculation."""

    person1: PersonDetails = Field(..., description="First person's details")
    person2: PersonDetails = Field(..., description="Second person's details")
    include_interpretation: bool = Field(default=True, description="Include LLM interpretation")


class KootaScore(BaseModel):
    """Individual Koota score."""
    name: str
    score: float
    max_score: float
    description: str
    details: Optional[str] = None


class CompatibilityOutput(BaseModel):
    """Output schema for compatibility calculation."""

    success: bool = Field(..., description="Whether calculation was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    # Person 1 details
    person1_name: Optional[str] = None
    person1_moon_sign: Optional[str] = None
    person1_nakshatra: Optional[str] = None
    person1_varna: Optional[str] = None
    person1_nadi: Optional[str] = None

    # Person 2 details
    person2_name: Optional[str] = None
    person2_moon_sign: Optional[str] = None
    person2_nakshatra: Optional[str] = None
    person2_varna: Optional[str] = None
    person2_nadi: Optional[str] = None

    # Ashtakoot scores (8 Kootas)
    koota_scores: Optional[List[KootaScore]] = None

    # Total
    total_score: Optional[float] = None
    max_score: float = 36
    percentage: Optional[float] = None

    # Verdict
    verdict: Optional[str] = None
    compatibility_level: Optional[str] = None  # Excellent, Good, Average, Below Average
    recommendation: Optional[str] = None

    # Special considerations
    nadi_dosha: bool = False
    bhakoot_dosha: bool = False
    dosha_exceptions: Optional[List[str]] = None

    # LLM interpretation
    interpretation: Optional[str] = None
    strengths: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    remedies: Optional[List[str]] = None

    # Metadata
    calculation_method: str = "Ashtakoot Milan (North Indian)"


# =============================================================================
# TOOL IMPLEMENTATION
# =============================================================================

async def calculate_compatibility(
    input_data: CompatibilityInput,
    llm=None
) -> CompatibilityOutput:
    """
    Calculate Ashtakoot Milan compatibility between two people.

    The 8 Kootas (factors) evaluated:
    1. Varna (1 point) - Spiritual compatibility
    2. Vashya (2 points) - Mutual attraction & control
    3. Tara (3 points) - Birth star compatibility
    4. Yoni (4 points) - Physical/sexual compatibility
    5. Graha Maitri (5 points) - Mental compatibility
    6. Gana (6 points) - Temperament matching
    7. Bhakoot (7 points) - Love & family prosperity
    8. Nadi (8 points) - Health & progeny

    Args:
        input_data: Validated compatibility input
        llm: Optional LLM for interpretation

    Returns:
        CompatibilityOutput with scores and interpretation
    """
    try:
        # Initialize services
        validator = InputValidator()
        chart_engine = ChartEngine()
        rules_engine = RulesEngine()
        knowledge_layer = KnowledgeLayer()

        # Validate Person 1
        validation1 = validator.validate_birth_details(
            name=input_data.person1.name,
            date_str=input_data.person1.birth_date,
            time_str=input_data.person1.birth_time or "12:00",
            location=input_data.person1.birth_place,
            require_time=False
        )

        if not validation1.is_valid:
            return CompatibilityOutput(
                success=False,
                error=f"Person 1 validation failed: {validation1.error}"
            )

        # Validate Person 2
        validation2 = validator.validate_birth_details(
            name=input_data.person2.name,
            date_str=input_data.person2.birth_date,
            time_str=input_data.person2.birth_time or "12:00",
            location=input_data.person2.birth_place,
            require_time=False
        )

        if not validation2.is_valid:
            return CompatibilityOutput(
                success=False,
                error=f"Person 2 validation failed: {validation2.error}"
            )

        v1 = validation1.value
        v2 = validation2.value
        loc1 = v1["location"]
        loc2 = v2["location"]

        # Calculate charts
        chart1 = chart_engine.calculate_chart(
            birth_date=v1["date"],
            birth_time=v1.get("time") or datetime.strptime("12:00", "%H:%M").time(),
            latitude=loc1.latitude,
            longitude=loc1.longitude,
            timezone=loc1.timezone
        )

        chart2 = chart_engine.calculate_chart(
            birth_date=v2["date"],
            birth_time=v2.get("time") or datetime.strptime("12:00", "%H:%M").time(),
            latitude=loc2.latitude,
            longitude=loc2.longitude,
            timezone=loc2.timezone
        )

        # Calculate compatibility (deterministic)
        match_result = rules_engine.calculate_compatibility(chart1, chart2)

        # Build output
        output = CompatibilityOutput(
            success=True,
            person1_name=v1.get("name", input_data.person1.name),
            person1_moon_sign=chart1.moon_sign,
            person1_nakshatra=chart1.moon_nakshatra,
            person1_varna=chart1.varna,
            person1_nadi=chart1.nadi,
            person2_name=v2.get("name", input_data.person2.name),
            person2_moon_sign=chart2.moon_sign,
            person2_nakshatra=chart2.moon_nakshatra,
            person2_varna=chart2.varna,
            person2_nadi=chart2.nadi,
            koota_scores=_format_koota_scores(match_result),
            total_score=match_result.total_score,
            percentage=round((match_result.total_score / 36) * 100, 1),
            verdict=_get_verdict(match_result.total_score),
            compatibility_level=_get_compatibility_level(match_result.total_score),
            recommendation=_get_recommendation(match_result),
            nadi_dosha=match_result.scores.get("nadi", 8) == 0,
            bhakoot_dosha=match_result.scores.get("bhakoot", 7) == 0,
            dosha_exceptions=_get_dosha_exceptions(match_result)
        )

        # Generate interpretation if requested
        if input_data.include_interpretation and llm:
            try:
                interpreter = AstroInterpreter(llm=llm)
                interpretation = await interpreter.interpret_compatibility(
                    chart1=chart1,
                    chart2=chart2,
                    match_result=match_result
                )

                if interpretation:
                    output.interpretation = interpretation.summary
                    output.strengths = interpretation.strengths
                    output.challenges = interpretation.challenges
                    output.remedies = interpretation.remedies

            except Exception as e:
                logger.warning(f"Interpretation failed: {e}")

        return output

    except Exception as e:
        logger.error(f"Compatibility calculation failed: {e}")
        return CompatibilityOutput(
            success=False,
            error=f"Calculation failed: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Import datetime for time parsing
from datetime import datetime

def _format_koota_scores(match_result) -> List[KootaScore]:
    """Format individual Koota scores."""
    koota_info = {
        "varna": {"max": 1, "desc": "Spiritual compatibility - work ethic alignment"},
        "vashya": {"max": 2, "desc": "Mutual attraction and influence"},
        "tara": {"max": 3, "desc": "Birth star harmony - health & fortune"},
        "yoni": {"max": 4, "desc": "Physical and intimate compatibility"},
        "graha_maitri": {"max": 5, "desc": "Mental wavelength and friendship"},
        "gana": {"max": 6, "desc": "Temperament and behavior matching"},
        "bhakoot": {"max": 7, "desc": "Love, family prosperity, and finances"},
        "nadi": {"max": 8, "desc": "Health, genes, and progeny welfare"}
    }

    scores = []
    for koota, info in koota_info.items():
        score = match_result.scores.get(koota, 0)
        scores.append(KootaScore(
            name=koota.replace("_", " ").title(),
            score=score,
            max_score=info["max"],
            description=info["desc"],
            details=_get_koota_detail(koota, score, info["max"])
        ))

    return scores


def _get_koota_detail(koota: str, score: float, max_score: float) -> str:
    """Get detailed explanation for a Koota score."""
    ratio = score / max_score if max_score > 0 else 0

    if koota == "nadi":
        if score == 0:
            return "Same Nadi - traditionally considered inauspicious for progeny. Remedies may apply."
        return "Different Nadi - favorable for health of offspring."

    if koota == "bhakoot":
        if score == 0:
            return "6-8 or 2-12 position - may indicate financial or health challenges. Check for exceptions."
        return "Favorable Moon sign relationship."

    if ratio >= 0.8:
        return "Excellent compatibility in this aspect."
    elif ratio >= 0.5:
        return "Good compatibility with minor adjustments."
    elif ratio >= 0.3:
        return "Moderate compatibility - awareness needed."
    else:
        return "Area of potential challenge - understanding required."


def _get_verdict(score: float) -> str:
    """Get compatibility verdict based on total score."""
    if score >= 28:
        return "Highly Compatible"
    elif score >= 25:
        return "Excellent Match"
    elif score >= 21:
        return "Very Good Match"
    elif score >= 18:
        return "Good Match"
    elif score >= 15:
        return "Average Match"
    elif score >= 12:
        return "Below Average"
    else:
        return "Requires Detailed Analysis"


def _get_compatibility_level(score: float) -> str:
    """Get compatibility level category."""
    if score >= 25:
        return "Excellent"
    elif score >= 18:
        return "Good"
    elif score >= 12:
        return "Average"
    else:
        return "Below Average"


def _get_recommendation(match_result) -> str:
    """Generate recommendation based on scores."""
    score = match_result.total_score
    nadi_score = match_result.scores.get("nadi", 8)
    bhakoot_score = match_result.scores.get("bhakoot", 7)

    recommendations = []

    if score >= 25:
        recommendations.append("This is considered an auspicious match according to Ashtakoot Milan.")
    elif score >= 18:
        recommendations.append("This match is suitable with minor adjustments and mutual understanding.")
    elif score >= 12:
        recommendations.append("This match may work with conscious effort and possible remedies.")
    else:
        recommendations.append("Consider consulting an experienced astrologer for detailed analysis.")

    # Add specific dosha recommendations
    if nadi_score == 0:
        recommendations.append(
            "Nadi Dosha is present. Traditional view suggests this may affect progeny. "
            "However, if Moon signs are different, this dosha may be reduced."
        )

    if bhakoot_score == 0:
        recommendations.append(
            "Bhakoot Dosha is present. This traditionally indicates challenges in family prosperity. "
            "Lords of the signs being friends can reduce this dosha."
        )

    return " ".join(recommendations)


def _get_dosha_exceptions(match_result) -> List[str]:
    """Check for dosha exception conditions."""
    exceptions = []

    # These would normally check actual chart positions
    # For now, return general exception conditions
    nadi_score = match_result.scores.get("nadi", 8)
    bhakoot_score = match_result.scores.get("bhakoot", 7)

    if nadi_score == 0:
        exceptions.append(
            "Nadi Dosha Exception: If both have different Moon Rashis (signs), "
            "the dosha effect is reduced."
        )
        exceptions.append(
            "Nadi Dosha Exception: If the same Nakshatra has different Padas, "
            "the dosha is nullified."
        )

    if bhakoot_score == 0:
        exceptions.append(
            "Bhakoot Dosha Exception: If the lords of both Rashis are friends "
            "or same, the dosha is cancelled."
        )

    return exceptions if exceptions else None


# =============================================================================
# LANGCHAIN TOOL WRAPPER
# =============================================================================

def get_compatibility_tool(llm=None):
    """
    Create a LangChain-compatible tool for compatibility calculation.
    """
    from langchain_core.tools import StructuredTool

    async def _run_compatibility(
        person1_name: str,
        person1_birth_date: str,
        person2_name: str,
        person2_birth_date: str,
        person1_birth_time: str = "12:00",
        person1_birth_place: str = "Delhi",
        person2_birth_time: str = "12:00",
        person2_birth_place: str = "Delhi",
        include_interpretation: bool = True
    ) -> Dict[str, Any]:
        """Calculate Kundli matching (Ashtakoot Milan) compatibility between two people."""
        input_data = CompatibilityInput(
            person1=PersonDetails(
                name=person1_name,
                birth_date=person1_birth_date,
                birth_time=person1_birth_time,
                birth_place=person1_birth_place
            ),
            person2=PersonDetails(
                name=person2_name,
                birth_date=person2_birth_date,
                birth_time=person2_birth_time,
                birth_place=person2_birth_place
            ),
            include_interpretation=include_interpretation
        )
        result = await calculate_compatibility(input_data, llm=llm)
        return result.model_dump()

    return StructuredTool.from_function(
        coroutine=_run_compatibility,
        name="calculate_compatibility",
        description="""Calculate Kundli matching (Ashtakoot Milan) compatibility score between two people.

Evaluates 8 Kootas (factors) totaling 36 points:
- Varna (1) - Spiritual compatibility
- Vashya (2) - Mutual attraction
- Tara (3) - Birth star harmony
- Yoni (4) - Physical compatibility
- Graha Maitri (5) - Mental compatibility
- Gana (6) - Temperament matching
- Bhakoot (7) - Love & prosperity
- Nadi (8) - Health & progeny

Required: person1_name, person1_birth_date, person2_name, person2_birth_date
Optional: birth times and places for more accuracy"""
    )
