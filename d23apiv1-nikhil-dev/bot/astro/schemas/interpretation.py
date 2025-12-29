"""
Interpretation Schemas

Structured output for LLM-generated interpretations.
Enforces that every claim maps to chart data or rules.
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class InterpretationFocus(str, Enum):
    """Focus areas for interpretation."""
    GENERAL = "general"
    PERSONALITY = "personality"
    CAREER = "career"
    RELATIONSHIPS = "relationships"
    HEALTH = "health"
    FINANCE = "finance"
    SPIRITUALITY = "spirituality"
    TIMING = "timing"  # Muhurta, favorable periods


class Section(BaseModel):
    """A section of the interpretation."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Main content")

    # Evidence linking - CRITICAL for trust
    based_on: List[str] = Field(
        default_factory=list,
        description="List of chart features this is based on (e.g., 'Moon in Aries', 'Jupiter in 10th house')"
    )
    rules_applied: List[str] = Field(
        default_factory=list,
        description="Rules that informed this section (e.g., 'Gaja Kesari Yoga', 'Manglik Dosha')"
    )

    # Confidence and certainty
    confidence: str = Field(default="medium", description="high/medium/low")
    uncertainty_note: Optional[str] = Field(
        None,
        description="Any uncertainty or caveat for this section"
    )


class Timeline(BaseModel):
    """Time-based prediction or favorable period."""

    period: str = Field(..., description="Time period description")
    themes: List[str] = Field(..., description="Expected themes")
    basis: str = Field(..., description="What this is based on (e.g., 'Jupiter Dasha', 'Saturn Transit')")

    # Probabilistic framing - NEVER guarantees
    likelihood: str = Field(default="possible", description="likely/possible/uncertain")


class InterpretationRequest(BaseModel):
    """Request for interpretation from LLM."""

    # Focus
    focus_areas: List[InterpretationFocus] = Field(
        default=[InterpretationFocus.GENERAL],
        description="Areas to focus interpretation on"
    )

    # Optional user question
    user_question: Optional[str] = Field(
        None,
        description="Specific question from user to address"
    )

    # Context
    language: str = Field(default="en", description="Language for response")
    detail_level: str = Field(default="moderate", description="brief/moderate/detailed")


class InterpretationResponse(BaseModel):
    """
    Structured interpretation output from LLM.

    Every section must have evidence linking back to chart data.
    No free-form predictions without basis.
    """

    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(..., description="LLM model that generated this")

    # Core sections
    summary: str = Field(..., description="Brief overall summary (2-3 sentences)")

    sections: List[Section] = Field(
        ...,
        description="Detailed sections based on requested focus areas"
    )

    # Time-based insights (if applicable)
    timelines: List[Timeline] = Field(
        default_factory=list,
        description="Time-based insights from dasha/transit"
    )

    # Remedial suggestions (factual, not medical)
    remedies: List[str] = Field(
        default_factory=list,
        description="Traditional remedial suggestions"
    )

    # Strengths and challenges
    key_strengths: List[str] = Field(
        default_factory=list,
        description="Identified strengths from chart"
    )
    key_challenges: List[str] = Field(
        default_factory=list,
        description="Potential challenges from chart"
    )

    # Required disclaimers and uncertainty
    disclaimers: List[str] = Field(
        default_factory=list,
        description="Required disclaimers"
    )
    areas_of_uncertainty: List[str] = Field(
        default_factory=list,
        description="Areas where analysis is limited or uncertain"
    )

    # Answer to user's specific question (if asked)
    question_answer: Optional[str] = Field(
        None,
        description="Direct answer to user's question if one was asked"
    )


class SafetyCheck(BaseModel):
    """Safety check results for generated content."""

    passed: bool = Field(..., description="Whether content passed safety checks")
    violations: List[str] = Field(default_factory=list)

    # Specific checks
    has_medical_advice: bool = Field(default=False)
    has_legal_advice: bool = Field(default=False)
    has_fatalistic_language: bool = Field(default=False)
    has_guaranteed_predictions: bool = Field(default=False)
    has_unfounded_claims: bool = Field(default=False)


class QuestionAnswer(BaseModel):
    """
    Structured response for Ask Astrologer feature.

    Answers must be grounded in Jyotish principles.
    """

    question: str
    answer: str

    # Sources
    based_on_principles: List[str] = Field(
        ...,
        description="Jyotish principles this answer is based on"
    )
    classical_references: List[str] = Field(
        default_factory=list,
        description="References to classical texts if applicable"
    )

    # Context
    requires_chart: bool = Field(
        default=False,
        description="Whether a birth chart is needed for more specific answer"
    )
    chart_data_used: Optional[str] = Field(
        None,
        description="If chart was used, what data informed the answer"
    )

    # Confidence
    confidence: str = Field(default="medium")
    disclaimer: str = Field(
        default="This is general information based on Vedic astrology principles. For personalized guidance, provide your birth details."
    )


class HoroscopeResponse(BaseModel):
    """Daily/Weekly/Monthly horoscope response."""

    sign: str
    period: str = Field(..., description="today/tomorrow/weekly/monthly")
    date_range: str = Field(..., description="Date or date range covered")

    # Content
    overview: str
    love_relationships: Optional[str] = None
    career_finance: Optional[str] = None
    health_wellness: Optional[str] = None

    # Lucky elements (from nakshatra data)
    lucky_number: Optional[int] = None
    lucky_color: Optional[str] = None
    lucky_time: Optional[str] = None

    # Advice
    advice: str

    # Basis for predictions
    based_on: str = Field(
        ...,
        description="What this horoscope is based on (e.g., 'Moon transit through nakshatra X')"
    )

    # Framing
    framing: str = Field(
        default="general tendencies",
        description="This represents general tendencies, not guaranteed events"
    )
