"""
Vedic AI Astrologer Module

Production-level astrology implementation following these principles:
1. LLM never calculates charts - all astrology math is deterministic
2. LLM only explains + synthesizes based on computed data
3. Every claim must map to chart data, explicit rule, or cited text
4. If data is missing, say "uncertain"

Architecture:
- Chart Engine: Swiss Ephemeris for planetary calculations
- Rules Engine: Jyotish rules (Yogas, Doshas, Dashas)
- Knowledge Layer: Curated Jyotish text snippets
- LLM Interpretation: Structured JSON output with citations
"""

from common.astro.services.chart_engine import ChartEngine
from common.astro.services.rules_engine import RulesEngine
from common.astro.services.interpreter import AstroInterpreter
from common.astro.services.validation import InputValidator

__all__ = [
    "ChartEngine",
    "RulesEngine",
    "AstroInterpreter",
    "InputValidator",
]
