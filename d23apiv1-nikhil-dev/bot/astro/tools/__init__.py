"""
LangGraph Tools for Vedic Astrology

Production-level tools with structured I/O, proper error handling,
and integration with the deterministic calculation services.

Architecture:
- Tools are thin wrappers around services
- All calculations happen in deterministic services
- LLM only interprets pre-computed data
- Proper validation at input boundaries
"""

from bot.astro.tools.birth_chart import (
    calculate_birth_chart,
    BirthChartInput,
    BirthChartOutput,
)
from bot.astro.tools.compatibility import (
    calculate_compatibility,
    CompatibilityInput,
    CompatibilityOutput,
)
from bot.astro.tools.horoscope import (
    get_daily_horoscope,
    HoroscopeInput,
    HoroscopeOutput,
)
from bot.astro.tools.question import (
    answer_astro_question,
    AstroQuestionInput,
    AstroQuestionOutput,
)
from bot.astro.tools.panchang import (
    get_panchang,
    PanchangInput,
    PanchangOutput,
)

__all__ = [
    # Birth Chart Tool
    "calculate_birth_chart",
    "BirthChartInput",
    "BirthChartOutput",
    # Compatibility Tool
    "calculate_compatibility",
    "CompatibilityInput",
    "CompatibilityOutput",
    # Horoscope Tool
    "get_daily_horoscope",
    "HoroscopeInput",
    "HoroscopeOutput",
    # Question Tool
    "answer_astro_question",
    "AstroQuestionInput",
    "AstroQuestionOutput",
    # Panchang Tool
    "get_panchang",
    "PanchangInput",
    "PanchangOutput",
]
