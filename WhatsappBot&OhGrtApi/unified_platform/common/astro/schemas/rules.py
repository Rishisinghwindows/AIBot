"""
Rules Engine Output Schemas

Structured output from Jyotish rules evaluation.
Every finding has explicit conditions, evidence, and confidence.
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from enum import Enum

from common.astro.schemas.chart import Planet, ZodiacSign


class ConfidenceLevel(str, Enum):
    """Confidence level for rule findings."""
    HIGH = "high"       # All conditions clearly met
    MEDIUM = "medium"   # Most conditions met
    LOW = "low"         # Some conditions met
    UNCERTAIN = "uncertain"  # Insufficient data


class RuleFinding(BaseModel):
    """Base class for all rule findings."""

    rule_name: str = Field(..., description="Name of the rule applied")
    rule_category: str = Field(..., description="Category: yoga/dosha/dignity/aspect/dasha")
    is_active: bool = Field(..., description="Whether this rule is currently active")

    # Evidence and reasoning
    conditions: List[str] = Field(..., description="Conditions that were checked")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting data from chart")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")

    # Interpretation hints (for LLM)
    general_effect: str = Field(..., description="General effect description")
    specific_context: Optional[str] = Field(None, description="Context-specific notes")

    # Source citation
    source_text: Optional[str] = Field(None, description="Classical text reference if any")


class YogaResult(RuleFinding):
    """Yoga (planetary combination) finding."""

    rule_category: str = "yoga"

    yoga_type: str = Field(..., description="Type: raja_yoga/dhana_yoga/arishta_yoga/etc.")
    forming_planets: List[Planet] = Field(..., description="Planets forming this yoga")
    houses_involved: List[int] = Field(..., description="Houses involved")

    # Strength indicators
    strength_score: float = Field(..., ge=0, le=1, description="Strength of yoga (0-1)")
    benefic_malefic: str = Field(..., description="benefic/malefic/mixed")

    # Timing
    activation_period: Optional[str] = Field(None, description="When yoga activates (dasha/transit)")


class DoshaResult(RuleFinding):
    """Dosha (affliction) finding."""

    rule_category: str = "dosha"

    dosha_type: str = Field(..., description="Type: manglik/kaal_sarp/pitra/etc.")
    severity: str = Field(..., description="mild/moderate/severe")

    # Afflicted areas
    affected_houses: List[int] = Field(default_factory=list)
    affected_planets: List[Planet] = Field(default_factory=list)

    # Remedial information
    can_be_cancelled: bool = Field(default=False, description="Whether dosha has cancellation")
    cancellation_factors: List[str] = Field(default_factory=list)

    # NOTE: We provide factual data, not medical/legal advice
    disclaimer: str = Field(
        default="This is for educational purposes only. Consult a qualified astrologer for detailed analysis.",
        description="Required disclaimer"
    )


class PlanetDignity(BaseModel):
    """Planetary dignity analysis."""

    planet: Planet
    sign: ZodiacSign
    dignity_status: str = Field(..., description="own/exalted/debilitated/mool_trikona/neutral")
    dignity_score: float = Field(..., ge=-2, le=2, description="Score: -2 to +2")

    # Context
    house_placement: int
    house_lordship: List[int] = Field(..., description="Houses this planet rules")
    is_functional_benefic: bool = Field(..., description="Functional benefic for this ascendant")


class DashaResult(BaseModel):
    """Vimshottari Dasha period data."""

    dasha_lord: Planet = Field(..., description="Main period lord")
    antardasha_lord: Optional[Planet] = Field(None, description="Sub-period lord")
    pratyantardasha_lord: Optional[Planet] = Field(None, description="Sub-sub-period lord")

    # Timing
    start_date: date
    end_date: date
    current: bool = Field(default=False, description="Whether this is current period")

    # Analysis
    dasha_lord_strength: float = Field(..., ge=0, le=1)
    houses_activated: List[int] = Field(..., description="Houses activated by this dasha")
    expected_themes: List[str] = Field(..., description="Expected life themes")

    # Balance information
    balance_at_birth: Optional[float] = Field(None, description="Dasha balance at birth (years)")


class CompatibilityScore(BaseModel):
    """Individual koota score for Kundli matching."""

    koota_name: str = Field(..., description="Name: varna/vashya/tara/yoni/maitri/gana/bhakoot/nadi")
    max_points: float
    obtained_points: float
    description: str = Field(..., description="What this koota measures")

    # Details
    person1_value: str
    person2_value: str
    reasoning: str = Field(..., description="Why this score was given")


class KundliMatchResult(BaseModel):
    """Complete Kundli matching (Ashtakoot Milan) result."""

    person1_name: str
    person1_moon_sign: ZodiacSign
    person1_nakshatra: str

    person2_name: str
    person2_moon_sign: ZodiacSign
    person2_nakshatra: str

    # Individual scores
    scores: List[CompatibilityScore] = Field(..., description="All 8 koota scores")

    # Summary
    total_score: float = Field(..., ge=0, le=36)
    max_score: float = Field(default=36)
    percentage: float = Field(..., ge=0, le=100)

    # Verdict with uncertainty
    verdict: str = Field(..., description="Excellent/Good/Average/Below Average")
    recommendation: str

    # Critical checks
    nadi_dosha: bool = Field(..., description="Whether Nadi dosha is present")
    bhakoot_dosha: bool = Field(..., description="Whether Bhakoot dosha is present")
    has_critical_dosha: bool = Field(..., description="Whether any critical dosha present")

    # Disclaimer
    disclaimer: str = Field(
        default="Ashtakoot matching is one factor in compatibility. Personal understanding, family values, and other factors also matter.",
        description="Required disclaimer"
    )


class RulesOutput(BaseModel):
    """
    Complete output from Rules Engine.

    This structured output is passed to LLM for interpretation.
    LLM can only explain what's here - cannot invent new findings.
    """

    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    rules_version: str = Field(default="1.0.0")

    # Findings
    yogas: List[YogaResult] = Field(default_factory=list)
    doshas: List[DoshaResult] = Field(default_factory=list)
    dignities: List[PlanetDignity] = Field(default_factory=list)

    # Dasha analysis
    current_dasha: Optional[DashaResult] = None
    upcoming_dashas: List[DashaResult] = Field(default_factory=list)

    # Compatibility (if applicable)
    compatibility: Optional[KundliMatchResult] = None

    # Uncertainty markers
    uncertainties: List[str] = Field(
        default_factory=list,
        description="List of areas where data is uncertain or analysis is limited"
    )

    # Summary flags for quick reference
    has_raja_yogas: bool = Field(default=False)
    has_dhana_yogas: bool = Field(default=False)
    has_significant_doshas: bool = Field(default=False)
    overall_chart_strength: str = Field(default="moderate", description="strong/moderate/weak")
