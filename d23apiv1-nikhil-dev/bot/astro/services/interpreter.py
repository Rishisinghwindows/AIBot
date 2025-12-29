"""
LLM Interpretation Service

Generates interpretations from chart data and rule findings.
The LLM ONLY explains/synthesizes - it does NOT calculate.

Key principles:
1. LLM receives chart JSON + rules JSON + knowledge snippets
2. LLM outputs structured JSON (not free text)
3. Every claim must map to provided data
4. Hard guardrails prevent harmful content
5. Probabilistic framing only - no guarantees
"""

import logging
import json
from typing import Optional, List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from bot.config import get_settings
from bot.astro.schemas.chart import ChartData, Planet, Nakshatra
from bot.astro.schemas.rules import RulesOutput, KundliMatchResult
from bot.astro.schemas.interpretation import (
    InterpretationRequest,
    InterpretationResponse,
    Section,
    Timeline,
    SafetyCheck,
    QuestionAnswer,
    HoroscopeResponse,
    InterpretationFocus,
)
from bot.astro.services.knowledge_layer import KnowledgeLayer

logger = logging.getLogger(__name__)


# =============================================================================
# SAFETY GUARDRAILS
# =============================================================================

BLOCKED_PATTERNS = [
    # Medical advice
    "you will die", "you have cancer", "terminal illness", "seek immediate medical",
    "stop taking medication", "cure for", "treatment for disease",
    # Legal/Financial guarantees
    "guaranteed profit", "you will win", "invest all your money",
    "definitely get married", "certainly divorce",
    # Fatalistic language
    "destined to fail", "cursed", "doomed", "no hope",
    "nothing can change", "fate is sealed",
    # Harmful predictions
    "suicide", "kill", "murder", "death of spouse",
    "will never", "impossible for you",
]

REQUIRED_DISCLAIMERS = [
    "Vedic astrology provides insights based on planetary positions and is meant for guidance and self-reflection.",
    "These interpretations should not replace professional advice for medical, legal, or financial matters.",
    "Individual free will and life circumstances play a significant role in shaping outcomes.",
]


class SafetyValidator:
    """Validates generated content for safety."""

    @staticmethod
    def check_content(content: str) -> SafetyCheck:
        """Check content for blocked patterns and safety issues."""
        content_lower = content.lower()
        violations = []

        for pattern in BLOCKED_PATTERNS:
            if pattern in content_lower:
                violations.append(f"Blocked pattern: '{pattern}'")

        # Check for specific issues
        has_medical = any(w in content_lower for w in ["cancer", "disease", "medication", "diagnosis"])
        has_legal = any(w in content_lower for w in ["lawsuit", "legal action", "arrest", "conviction"])
        has_fatalistic = any(w in content_lower for w in ["doomed", "cursed", "destined to fail", "no hope"])
        has_guaranteed = any(w in content_lower for w in ["will definitely", "guaranteed", "certainly will", "100%"])
        has_unfounded = any(w in content_lower for w in ["psychic told me", "spirits say", "magic"])

        return SafetyCheck(
            passed=len(violations) == 0 and not has_medical and not has_fatalistic and not has_guaranteed,
            violations=violations,
            has_medical_advice=has_medical,
            has_legal_advice=has_legal,
            has_fatalistic_language=has_fatalistic,
            has_guaranteed_predictions=has_guaranteed,
            has_unfounded_claims=has_unfounded,
        )


# =============================================================================
# INTERPRETATION PROMPTS
# =============================================================================

CHART_INTERPRETATION_PROMPT = """You are a Vedic astrologer providing interpretations based ONLY on the chart data and rules provided.

CRITICAL RULES:
1. You CANNOT calculate anything - all data is pre-computed
2. You can ONLY explain what the data shows - no new astrological facts
3. Every claim must reference specific data from the chart or rules
4. Use probabilistic language: "suggests", "indicates", "may", "tends to"
5. NEVER use fatalistic language like "doomed", "cursed", "will definitely"
6. NEVER give medical, legal, or financial advice
7. NEVER guarantee outcomes

CHART DATA:
{chart_json}

RULES FINDINGS:
{rules_json}

KNOWLEDGE CONTEXT:
{knowledge_context}

USER QUESTION (if any): {user_question}
FOCUS AREAS: {focus_areas}
DETAIL LEVEL: {detail_level}

Generate an interpretation following this structure:
1. Summary (2-3 sentences overview)
2. Sections for each focus area (reference specific chart features)
3. Key strengths and challenges (from the data)
4. Timelines (only if dasha data provided)
5. Traditional remedies (factual, not medical claims)

Remember: Every statement must be traceable to the provided data."""


HOROSCOPE_PROMPT = """You are creating a {period} horoscope for {sign}.

Use this nakshatra information for the prediction:
{nakshatra_info}

Current transit context:
{transit_info}

Create a horoscope with these sections:
1. Overview (general energy for the period)
2. Love & Relationships
3. Career & Finance
4. Health & Wellness
5. Advice

Rules:
- Use encouraging, balanced language
- Reference the nakshatra characteristics
- Include lucky elements from the data
- Use probabilistic framing ("may experience", "favorable for")
- Keep it concise (150-200 words total)

Output as JSON with keys: overview, love_relationships, career_finance, health_wellness, advice"""


QUESTION_ANSWER_PROMPT = """You are answering an astrology question based on Jyotish principles.

Question: {question}

{chart_context}

Relevant Jyotish Principles:
{knowledge_context}

Rules:
1. Base your answer on classical Jyotish principles
2. If a chart was provided, reference specific placements
3. If no chart, give general guidance
4. Use probabilistic language
5. Never guarantee outcomes
6. Suggest getting a full chart analysis for personalized insight

Provide a clear, educational answer that helps the user understand the astrological perspective."""


COMPATIBILITY_PROMPT = """You are interpreting the Kundli matching (Ashtakoot Milan) results.

MATCHING DATA:
{match_json}

Provide an interpretation covering:
1. Overall compatibility assessment
2. Areas of strength (high-scoring kootas)
3. Areas needing attention (low-scoring kootas)
4. Practical advice for the couple

Rules:
- Be balanced and constructive
- Never say "incompatible" definitively
- Emphasize that matching is one factor among many
- Use encouraging, supportive language
- Acknowledge free will and personal effort matter"""


# =============================================================================
# INTERPRETER CLASS
# =============================================================================

class AstroInterpreter:
    """
    LLM-based interpretation service with safety guardrails.

    The interpreter ONLY synthesizes from provided data.
    It cannot calculate or invent astrological facts.
    """

    def __init__(self):
        """Initialize the interpreter."""
        self.settings = get_settings()
        self.knowledge = KnowledgeLayer()
        self.safety = SafetyValidator()
        self._setup_llm()

    def _setup_llm(self):
        """Setup the LLM with appropriate settings."""
        self.llm = ChatOpenAI(
            model=self.settings.OPENAI_MODEL,
            temperature=0.7,  # Some creativity for natural language
            api_key=self.settings.OPENAI_API_KEY,
        )

    def _prepare_chart_json(self, chart: ChartData) -> str:
        """Prepare chart data as JSON for LLM."""
        # Extract key info (not full object to reduce tokens)
        chart_summary = {
            "birth_details": {
                "name": chart.birth_details.name,
                "date": str(chart.birth_details.date_of_birth),
                "place": chart.birth_details.place_of_birth,
            },
            "ascendant": {
                "sign": chart.ascendant.sign.value,
                "nakshatra": chart.ascendant.nakshatra.name.value,
            },
            "sun_sign": chart.sun_sign.value,
            "moon_sign": chart.moon_sign.value,
            "moon_nakshatra": chart.moon_nakshatra.name.value,
            "planetary_positions": {
                p.value: {
                    "sign": pos.sign.value,
                    "house": pos.house,
                    "nakshatra": pos.nakshatra.name.value,
                    "retrograde": pos.is_retrograde,
                    "combust": pos.is_combust,
                }
                for p, pos in chart.planets.items()
            },
            "vedic_attributes": {
                "varna": chart.varna,
                "nadi": chart.nadi,
                "yoni": chart.yoni,
                "gana": chart.gana,
            },
        }
        return json.dumps(chart_summary, indent=2)

    def _prepare_rules_json(self, rules: RulesOutput) -> str:
        """Prepare rules output as JSON for LLM."""
        rules_summary = {
            "overall_strength": rules.overall_chart_strength,
            "has_raja_yogas": rules.has_raja_yogas,
            "has_dhana_yogas": rules.has_dhana_yogas,
            "has_significant_doshas": rules.has_significant_doshas,
            "yogas": [
                {
                    "name": y.rule_name,
                    "type": y.yoga_type,
                    "effect": y.general_effect,
                    "strength": y.strength_score,
                    "planets": [p.value for p in y.forming_planets],
                }
                for y in rules.yogas if y.is_active
            ],
            "doshas": [
                {
                    "name": d.rule_name,
                    "type": d.dosha_type,
                    "severity": d.severity,
                    "cancelled": not d.is_active,
                    "cancellation_factors": d.cancellation_factors,
                }
                for d in rules.doshas
            ],
            "current_dasha": {
                "lord": rules.current_dasha.dasha_lord.value,
                "start": str(rules.current_dasha.start_date),
                "end": str(rules.current_dasha.end_date),
                "themes": rules.current_dasha.expected_themes,
            } if rules.current_dasha else None,
            "uncertainties": rules.uncertainties,
        }
        return json.dumps(rules_summary, indent=2)

    async def interpret_chart(
        self,
        chart: ChartData,
        rules: RulesOutput,
        request: InterpretationRequest
    ) -> InterpretationResponse:
        """
        Generate interpretation for a birth chart.

        Args:
            chart: Computed chart data
            rules: Evaluated rules output
            request: Interpretation request with focus areas

        Returns:
            Structured interpretation response
        """
        # Prepare data for LLM
        chart_json = self._prepare_chart_json(chart)
        rules_json = self._prepare_rules_json(rules)

        # Build knowledge context
        planets_in_focus = list(chart.planets.keys())[:5]
        knowledge_context = self.knowledge.build_interpretation_context(
            planets=planets_in_focus,
            yogas=[y.rule_name for y in rules.yogas[:3]],
            nakshatras=[chart.moon_nakshatra.name],
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_template(CHART_INTERPRETATION_PROMPT)

        # Generate interpretation
        chain = prompt | self.llm
        result = await chain.ainvoke({
            "chart_json": chart_json,
            "rules_json": rules_json,
            "knowledge_context": knowledge_context,
            "user_question": request.user_question or "None",
            "focus_areas": ", ".join([f.value for f in request.focus_areas]),
            "detail_level": request.detail_level,
        })

        # Parse and structure the response
        interpretation_text = result.content

        # Safety check
        safety_result = self.safety.check_content(interpretation_text)
        if not safety_result.passed:
            logger.warning(f"Safety check failed: {safety_result.violations}")
            interpretation_text = self._sanitize_content(interpretation_text)

        # Build structured response
        sections = self._parse_sections(interpretation_text, request.focus_areas)

        # Build timelines from dasha
        timelines = []
        if rules.current_dasha:
            timelines.append(Timeline(
                period=f"{rules.current_dasha.dasha_lord.value} Dasha until {rules.current_dasha.end_date}",
                themes=rules.current_dasha.expected_themes,
                basis="Vimshottari Dasha calculation",
                likelihood="applicable"
            ))

        # Collect key points
        key_strengths = [y.rule_name for y in rules.yogas if y.is_active and y.benefic_malefic == "benefic"]
        key_challenges = [d.rule_name for d in rules.doshas if d.is_active]

        return InterpretationResponse(
            model_used=self.settings.OPENAI_MODEL,
            summary=self._extract_summary(interpretation_text),
            sections=sections,
            timelines=timelines,
            remedies=self._get_standard_remedies(chart, rules),
            key_strengths=key_strengths[:5],
            key_challenges=key_challenges[:3],
            disclaimers=REQUIRED_DISCLAIMERS,
            areas_of_uncertainty=rules.uncertainties,
            question_answer=interpretation_text if request.user_question else None,
        )

    async def generate_horoscope(
        self,
        sign: str,
        period: str = "today",
        nakshatra: Optional[Nakshatra] = None
    ) -> HoroscopeResponse:
        """
        Generate a horoscope prediction.

        Args:
            sign: Zodiac sign
            period: today/tomorrow/weekly/monthly
            nakshatra: Optional nakshatra for more specific prediction

        Returns:
            Structured horoscope response
        """
        # Get nakshatra info (use default if not provided)
        if nakshatra:
            nakshatra_info = self.knowledge.get_nakshatra_info(nakshatra)
        else:
            # Map sign to primary nakshatra (simplified)
            nakshatra_info = {"description": f"General prediction for {sign}"}

        # Get current transit info (simplified)
        transit_info = "Current planetary positions favor thoughtful action."

        prompt = ChatPromptTemplate.from_template(HOROSCOPE_PROMPT)
        chain = prompt | self.llm

        result = await chain.ainvoke({
            "sign": sign,
            "period": period,
            "nakshatra_info": json.dumps(nakshatra_info),
            "transit_info": transit_info,
        })

        # Parse JSON response
        try:
            horoscope_data = json.loads(result.content)
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            horoscope_data = {
                "overview": result.content[:200],
                "advice": "Stay positive and focused."
            }

        # Safety check
        for key, value in horoscope_data.items():
            if isinstance(value, str):
                safety = self.safety.check_content(value)
                if not safety.passed:
                    horoscope_data[key] = self._sanitize_content(value)

        return HoroscopeResponse(
            sign=sign,
            period=period,
            date_range=self._get_date_range(period),
            overview=horoscope_data.get("overview", ""),
            love_relationships=horoscope_data.get("love_relationships"),
            career_finance=horoscope_data.get("career_finance"),
            health_wellness=horoscope_data.get("health_wellness"),
            lucky_number=nakshatra_info.get("lucky_number", 1),
            lucky_color=nakshatra_info.get("lucky_color", "White"),
            advice=horoscope_data.get("advice", ""),
            based_on=f"Moon transit and {sign} characteristics",
            framing="These are general tendencies, not guaranteed events.",
        )

    async def answer_question(
        self,
        question: str,
        chart: Optional[ChartData] = None,
        user_sign: Optional[str] = None
    ) -> QuestionAnswer:
        """
        Answer a general astrology question.

        Args:
            question: User's question
            chart: Optional birth chart for personalized answer
            user_sign: Optional zodiac sign

        Returns:
            Structured Q&A response
        """
        # Build context
        chart_context = ""
        if chart:
            chart_context = f"User's chart: Ascendant {chart.ascendant.sign.value}, Moon in {chart.moon_sign.value}"

        # Get relevant knowledge
        knowledge_context = self.knowledge.build_interpretation_context(
            planets=[Planet.SUN, Planet.MOON],  # Basic
        )

        prompt = ChatPromptTemplate.from_template(QUESTION_ANSWER_PROMPT)
        chain = prompt | self.llm

        result = await chain.ainvoke({
            "question": question,
            "chart_context": chart_context,
            "knowledge_context": knowledge_context,
        })

        answer = result.content

        # Safety check
        safety = self.safety.check_content(answer)
        if not safety.passed:
            answer = self._sanitize_content(answer)

        return QuestionAnswer(
            question=question,
            answer=answer,
            based_on_principles=["Vedic Astrology", "Classical Jyotish texts"],
            requires_chart=not bool(chart),
            chart_data_used=chart_context if chart else None,
            confidence="medium" if chart else "general",
        )

    async def interpret_compatibility(
        self,
        match_result: KundliMatchResult
    ) -> str:
        """
        Generate interpretation for Kundli matching results.

        Args:
            match_result: Computed matching scores

        Returns:
            Interpretation text
        """
        match_json = json.dumps({
            "person1": match_result.person1_name,
            "person2": match_result.person2_name,
            "total_score": match_result.total_score,
            "percentage": match_result.percentage,
            "verdict": match_result.verdict,
            "scores": [
                {
                    "koota": s.koota_name,
                    "score": s.obtained_points,
                    "max": s.max_points,
                    "description": s.description,
                }
                for s in match_result.scores
            ],
            "nadi_dosha": match_result.nadi_dosha,
            "bhakoot_dosha": match_result.bhakoot_dosha,
        }, indent=2)

        prompt = ChatPromptTemplate.from_template(COMPATIBILITY_PROMPT)
        chain = prompt | self.llm

        result = await chain.ainvoke({"match_json": match_json})

        # Safety check
        interpretation = result.content
        safety = self.safety.check_content(interpretation)
        if not safety.passed:
            interpretation = self._sanitize_content(interpretation)

        return interpretation

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _sanitize_content(self, content: str) -> str:
        """Remove or modify unsafe content."""
        for pattern in BLOCKED_PATTERNS:
            if pattern in content.lower():
                content = content.replace(pattern, "[content moderated]")

        # Add disclaimer if needed
        if not any(d in content for d in ["This is for guidance", "not replace professional"]):
            content += "\n\nNote: This interpretation is for guidance and self-reflection only."

        return content

    def _extract_summary(self, text: str) -> str:
        """Extract summary from interpretation text."""
        lines = text.split('\n')
        for line in lines:
            if line.strip() and len(line) > 50:
                return line[:300]
        return "See detailed interpretation below."

    def _parse_sections(self, text: str, focus_areas: List[InterpretationFocus]) -> List[Section]:
        """Parse text into structured sections."""
        sections = []

        for focus in focus_areas:
            sections.append(Section(
                title=focus.value.title(),
                content=f"Based on your chart analysis for {focus.value}.",
                based_on=["Chart placements", "Yogas identified"],
                rules_applied=[],
                confidence="medium",
            ))

        return sections

    def _get_date_range(self, period: str) -> str:
        """Get date range string for period."""
        from datetime import date, timedelta
        today = date.today()

        if period == "today":
            return str(today)
        elif period == "tomorrow":
            return str(today + timedelta(days=1))
        elif period == "weekly":
            return f"{today} to {today + timedelta(days=7)}"
        elif period == "monthly":
            return f"{today.strftime('%B %Y')}"
        return str(today)

    def _get_standard_remedies(self, chart: ChartData, rules: RulesOutput) -> List[str]:
        """Get standard remedial suggestions based on chart."""
        remedies = []

        # Based on moon nakshatra
        moon_nak = chart.moon_nakshatra.name
        nak_info = self.knowledge.get_nakshatra_info(moon_nak)
        if nak_info:
            remedies.append(f"Wearing {nak_info.get('lucky_color', 'white')} on favorable days may be beneficial.")

        # Based on doshas
        for dosha in rules.doshas:
            if dosha.is_active and dosha.dosha_type == "manglik":
                remedies.append("Traditional remedy: Worship Lord Hanuman on Tuesdays.")

        # General remedies
        remedies.append("Regular meditation and self-reflection support spiritual growth.")

        return remedies[:5]
