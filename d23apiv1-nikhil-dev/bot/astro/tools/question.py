"""
Astrology Question Answering Tool

LangGraph tool for answering astrology-related questions.
Uses knowledge layer + chart data + LLM with strict guardrails.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import logging

from bot.astro.services.chart_engine import ChartEngine
from bot.astro.services.rules_engine import RulesEngine
from bot.astro.services.knowledge_layer import KnowledgeLayer
from bot.astro.services.interpreter import AstroInterpreter
from bot.astro.services.validation import InputValidator

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class QuestionCategory(str, Enum):
    """Categories of astrology questions."""
    GENERAL = "general"  # General astrology concepts
    PERSONAL = "personal"  # Questions about user's chart
    REMEDIES = "remedies"  # Gemstones, mantras, rituals
    COMPATIBILITY = "compatibility"  # Relationship questions
    TIMING = "timing"  # Muhurta, auspicious timing
    PREDICTION = "prediction"  # Future predictions
    EDUCATION = "education"  # Learning about astrology


# Questions that cannot be answered for safety
BLOCKED_QUESTION_PATTERNS = [
    "when will i die",
    "death date",
    "how will i die",
    "suicide",
    "kill",
    "lottery numbers",
    "stock tips",
    "gambling",
    "winning numbers",
    "curse someone",
    "black magic",
    "harm someone",
]


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class AstroQuestionInput(BaseModel):
    """Input schema for astrology Q&A."""

    question: str = Field(
        ...,
        description="The astrology question to answer",
        min_length=5,
        max_length=1000
    )
    user_sign: Optional[str] = Field(
        default=None,
        description="User's zodiac sign for personalized answers"
    )
    user_nakshatra: Optional[str] = Field(
        default=None,
        description="User's birth nakshatra for personalized answers"
    )
    birth_date: Optional[str] = Field(
        default=None,
        description="User's birth date for chart-based answers"
    )
    birth_time: Optional[str] = Field(
        default=None,
        description="User's birth time for chart-based answers"
    )
    birth_place: Optional[str] = Field(
        default=None,
        description="User's birth place for chart-based answers"
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate question is safe and appropriate."""
        if not v or not v.strip():
            raise ValueError("Question is required")

        question_lower = v.lower()

        # Check for blocked patterns
        for pattern in BLOCKED_QUESTION_PATTERNS:
            if pattern in question_lower:
                raise ValueError(
                    "I cannot answer questions about death, harmful activities, "
                    "or gambling. Please ask about personality, career, relationships, "
                    "or spiritual growth instead."
                )

        return v.strip()


class SourceReference(BaseModel):
    """Reference to source material."""
    type: str  # "text", "rule", "chart_data"
    name: str
    description: Optional[str] = None


class AstroQuestionOutput(BaseModel):
    """Output schema for astrology Q&A."""

    success: bool = Field(..., description="Whether answering was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    # Question details
    question: Optional[str] = None
    category: Optional[str] = None

    # Answer
    answer: Optional[str] = None
    confidence: Optional[str] = None  # HIGH, MEDIUM, LOW

    # Supporting information
    key_concepts: Optional[List[str]] = None
    related_topics: Optional[List[str]] = None

    # Sources (for evidence linking)
    sources: Optional[List[SourceReference]] = None

    # If chart was used
    chart_data_used: bool = False
    user_sign: Optional[str] = None
    user_nakshatra: Optional[str] = None

    # Additional context
    practical_advice: Optional[str] = None
    remedies: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

    # Disclaimer
    disclaimer: str = (
        "This is for educational and entertainment purposes. "
        "Astrology offers perspectives, not guarantees. "
        "For serious life decisions, consult qualified professionals."
    )


# =============================================================================
# TOOL IMPLEMENTATION
# =============================================================================

async def answer_astro_question(
    input_data: AstroQuestionInput,
    llm=None
) -> AstroQuestionOutput:
    """
    Answer an astrology-related question.

    Flow:
    1. Classify question category
    2. Retrieve relevant knowledge
    3. Calculate chart if birth details provided
    4. Generate answer with LLM (with guardrails)
    5. Add evidence/source links

    Args:
        input_data: Validated question input
        llm: LLM instance for answer generation

    Returns:
        AstroQuestionOutput with answer and sources
    """
    try:
        # Initialize services
        knowledge_layer = KnowledgeLayer()
        validator = InputValidator()

        question = input_data.question

        # Step 1: Classify question
        category = _classify_question(question)

        # Step 2: Retrieve relevant knowledge
        relevant_knowledge = _retrieve_knowledge(question, category, knowledge_layer)

        # Step 3: Calculate chart if birth details provided
        chart_data = None
        rules_output = None

        if input_data.birth_date and input_data.birth_time and input_data.birth_place:
            validation_result = validator.validate_birth_details(
                date_str=input_data.birth_date,
                time_str=input_data.birth_time,
                location=input_data.birth_place,
                require_time=True
            )

            if validation_result.is_valid:
                chart_engine = ChartEngine()
                rules_engine = RulesEngine()

                validated = validation_result.value
                location = validated["location"]

                chart_data = chart_engine.calculate_chart(
                    birth_date=validated["date"],
                    birth_time=validated["time"],
                    latitude=location.latitude,
                    longitude=location.longitude,
                    timezone=location.timezone
                )
                rules_output = rules_engine.evaluate_chart(chart_data)

        # Build base output
        output = AstroQuestionOutput(
            success=True,
            question=question,
            category=category.value,
            chart_data_used=chart_data is not None,
            user_sign=input_data.user_sign or (chart_data.moon_sign if chart_data else None),
            user_nakshatra=input_data.user_nakshatra or (chart_data.moon_nakshatra if chart_data else None),
            sources=_build_sources(relevant_knowledge, chart_data is not None)
        )

        # Step 4: Generate answer
        if llm:
            try:
                interpreter = AstroInterpreter(llm=llm)
                answer_response = await interpreter.answer_question(
                    question=question,
                    category=category.value,
                    knowledge=relevant_knowledge,
                    chart_data=chart_data,
                    rules_output=rules_output,
                    user_sign=input_data.user_sign
                )

                if answer_response:
                    output.answer = answer_response.answer
                    output.confidence = answer_response.confidence
                    output.key_concepts = answer_response.key_concepts
                    output.related_topics = answer_response.related_topics
                    output.practical_advice = answer_response.practical_advice
                    output.remedies = answer_response.remedies
                    output.warnings = answer_response.warnings

            except Exception as e:
                logger.warning(f"LLM answer generation failed: {e}")
                output = _generate_template_answer(output, question, category, relevant_knowledge)
        else:
            output = _generate_template_answer(output, question, category, relevant_knowledge)

        return output

    except ValueError as e:
        return AstroQuestionOutput(
            success=False,
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        return AstroQuestionOutput(
            success=False,
            error=f"Failed to answer question: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _classify_question(question: str) -> QuestionCategory:
    """Classify the question into a category."""
    question_lower = question.lower()

    # Check for specific keywords
    if any(word in question_lower for word in ["gemstone", "mantra", "remedy", "worship", "puja"]):
        return QuestionCategory.REMEDIES

    if any(word in question_lower for word in ["match", "compatible", "marriage", "relationship", "partner"]):
        return QuestionCategory.COMPATIBILITY

    if any(word in question_lower for word in ["when", "muhurta", "auspicious", "good time", "best day"]):
        return QuestionCategory.TIMING

    if any(word in question_lower for word in ["will i", "future", "predict", "what will happen"]):
        return QuestionCategory.PREDICTION

    if any(word in question_lower for word in ["my", "me", "i am", "born"]):
        return QuestionCategory.PERSONAL

    if any(word in question_lower for word in ["what is", "explain", "meaning", "learn", "how does"]):
        return QuestionCategory.EDUCATION

    return QuestionCategory.GENERAL


def _retrieve_knowledge(
    question: str,
    category: QuestionCategory,
    knowledge_layer: KnowledgeLayer
) -> Dict[str, Any]:
    """Retrieve relevant knowledge for the question."""
    knowledge = {
        "concepts": [],
        "planets": [],
        "houses": [],
        "nakshatras": [],
        "yogas": []
    }

    question_lower = question.lower()

    # Extract planet mentions
    planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    for planet in planets:
        if planet in question_lower:
            planet_info = knowledge_layer.get_planet_info(planet.title())
            if planet_info:
                knowledge["planets"].append(planet_info)

    # Extract house mentions
    for i in range(1, 13):
        if f"{i}th house" in question_lower or f"{i}st house" in question_lower or f"{i}nd house" in question_lower or f"{i}rd house" in question_lower:
            house_info = knowledge_layer.get_house_info(i)
            if house_info:
                knowledge["houses"].append(house_info)

    # Extract specific concepts
    concepts = [
        ("manglik", "mangal dosha"),
        ("kaal sarp", "kaal sarp dosha"),
        ("sade sati", "saturn transit"),
        ("retrograde", "vakri"),
        ("exalted", "uchcha"),
        ("debilitated", "neecha"),
        ("dasha", "mahadasha"),
        ("nakshatra", "birth star"),
        ("yoga", "planetary combination")
    ]

    for concept, alt in concepts:
        if concept in question_lower or alt in question_lower:
            knowledge["concepts"].append(concept)

    return knowledge


def _build_sources(knowledge: Dict, chart_used: bool) -> List[SourceReference]:
    """Build source references for the answer."""
    sources = []

    # Add knowledge sources
    for planet_info in knowledge.get("planets", []):
        sources.append(SourceReference(
            type="text",
            name=f"Jyotish: {planet_info.get('name', 'Planet')} significations",
            description="Classical Vedic astrology texts"
        ))

    for house_info in knowledge.get("houses", []):
        sources.append(SourceReference(
            type="text",
            name=f"Jyotish: House {house_info.get('number', '')} meanings",
            description="Classical Vedic astrology texts"
        ))

    for concept in knowledge.get("concepts", []):
        sources.append(SourceReference(
            type="rule",
            name=f"Jyotish rule: {concept.title()}",
            description="Traditional Jyotish principles"
        ))

    if chart_used:
        sources.append(SourceReference(
            type="chart_data",
            name="User's birth chart",
            description="Calculated using Swiss Ephemeris with Lahiri Ayanamsa"
        ))

    return sources if sources else None


def _generate_template_answer(
    output: AstroQuestionOutput,
    question: str,
    category: QuestionCategory,
    knowledge: Dict
) -> AstroQuestionOutput:
    """Generate template-based answer when LLM is not available."""

    question_lower = question.lower()

    # Generic answers based on category
    if category == QuestionCategory.REMEDIES:
        output.answer = (
            "Vedic astrology offers various remedies including gemstones, mantras, "
            "and charitable acts. The appropriate remedy depends on your specific chart "
            "and the planetary influences you wish to strengthen or pacify. "
            "Consulting an experienced astrologer with your birth details would provide "
            "personalized recommendations."
        )
        output.practical_advice = "Remedies work best when practiced with faith and consistency."

    elif category == QuestionCategory.COMPATIBILITY:
        output.answer = (
            "Compatibility in Vedic astrology is assessed through Ashtakoot Milan, "
            "which evaluates 8 factors totaling 36 points. Key factors include "
            "Nadi (health), Bhakoot (prosperity), and Gana (temperament). "
            "A score of 18+ is generally considered suitable for marriage."
        )
        output.practical_advice = "Numbers are guides, not guarantees. Understanding and effort matter most."

    elif category == QuestionCategory.TIMING:
        output.answer = (
            "Muhurta (auspicious timing) is an important branch of Jyotish. "
            "The best timings depend on the specific activity, your birth chart, "
            "and current planetary transits. General principles include avoiding "
            "Rahu Kaal, favoring the waxing Moon phase for beginnings, "
            "and considering the day lord's significations."
        )

    elif category == QuestionCategory.PREDICTION:
        output.answer = (
            "Vedic astrology views planetary influences as tendencies, not certainties. "
            "The Dasha system and transits indicate periods of opportunity or challenge "
            "in different life areas. Your response to these influences shapes outcomes. "
            "Free will operates within the framework of karma."
        )
        output.warnings = [
            "Predictions indicate probabilities, not fixed destiny",
            "Personal effort can modify karmic patterns"
        ]

    elif category == QuestionCategory.EDUCATION:
        output.answer = _get_educational_answer(question_lower, knowledge)

    else:
        # General answer
        output.answer = (
            "Jyotish (Vedic astrology) offers insights into personality, life patterns, "
            "and timing through the analysis of planetary positions at birth. "
            "For a detailed answer to your specific question, please provide more context "
            "or your birth details for personalized guidance."
        )

    output.confidence = "MEDIUM"
    output.key_concepts = knowledge.get("concepts", [])[:3]

    return output


def _get_educational_answer(question: str, knowledge: Dict) -> str:
    """Generate educational answer for concept questions."""

    # Check for specific concepts
    if "manglik" in question or "mangal dosha" in question:
        return (
            "Manglik Dosha occurs when Mars is placed in the 1st, 4th, 7th, 8th, or 12th house "
            "from the Ascendant, Moon, or Venus. It's believed to affect marriage harmony. "
            "However, there are many cancellation factors (Mars in own sign, aspects from benefics, "
            "both partners having the dosha, etc.) that reduce or nullify its effects."
        )

    if "kaal sarp" in question:
        return (
            "Kaal Sarp Dosha forms when all planets are hemmed between Rahu and Ketu. "
            "Its effects depend on which houses are occupied and the specific planets involved. "
            "Many successful people have this combination, as it can also indicate "
            "intense focus and eventual achievement after initial struggles."
        )

    if "retrograde" in question:
        return (
            "Retrograde (Vakri) planets appear to move backward due to relative orbital speeds. "
            "In Jyotish, retrograde planets are considered strong and their results are "
            "internalized or delayed. Mercury retrograde affects communication, "
            "while Saturn retrograde may intensify karmic lessons."
        )

    if "dasha" in question:
        return (
            "The Dasha system, particularly Vimshottari Dasha, divides life into planetary periods. "
            "Each planet rules for a specific number of years (Sun: 6, Moon: 10, Mars: 7, etc.). "
            "The results depend on the planet's placement, strength, and yogas in your chart. "
            "Sub-periods (Antardashas) provide more specific timing."
        )

    if "nakshatra" in question:
        return (
            "Nakshatras are the 27 lunar mansions, each spanning 13°20' of the zodiac. "
            "Your Moon Nakshatra (Janma Nakshatra) significantly influences personality, "
            "emotional nature, and life path. Each Nakshatra has a ruling deity, symbol, "
            "and planetary lord that color its expression."
        )

    # Default educational answer
    return (
        "Jyotish is built on foundational concepts including the 9 Grahas (planets), "
        "12 Rashis (signs), 27 Nakshatras (lunar mansions), and 12 Bhavas (houses). "
        "Understanding how these interact in a birth chart reveals life patterns and potentials. "
        "Would you like to learn about a specific concept?"
    )


# =============================================================================
# LANGCHAIN TOOL WRAPPER
# =============================================================================

def get_question_tool(llm=None):
    """Create a LangChain-compatible tool for astrology Q&A."""
    from langchain_core.tools import StructuredTool

    async def _run_question(
        question: str,
        user_sign: str = None,
        birth_date: str = None,
        birth_time: str = None,
        birth_place: str = None
    ) -> Dict[str, Any]:
        """Answer an astrology question."""
        input_data = AstroQuestionInput(
            question=question,
            user_sign=user_sign,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_place=birth_place
        )
        result = await answer_astro_question(input_data, llm=llm)
        return result.model_dump()

    return StructuredTool.from_function(
        coroutine=_run_question,
        name="ask_astrologer",
        description="""Answer astrology-related questions with knowledge-based responses.

Can answer questions about:
- Zodiac signs and their traits
- Planetary influences and significations
- Nakshatras (lunar mansions)
- Doshas (Manglik, Kaal Sarp, etc.)
- Remedies (gemstones, mantras)
- Compatibility concepts
- Vedic astrology principles

Provide birth details for personalized answers.
Cannot answer questions about death dates, lottery numbers, or harmful activities."""
    )
