"""
Centralized constants for the bot.

Provides:
- Domain and intent keywords
- Response templates
- Configuration values
"""

from bot.constants.intents import (
    DOMAIN_KEYWORDS,
    ASTRO_INTENT_PATTERNS,
    TRAVEL_INTENT_PATTERNS,
    UTILITY_INTENT_PATTERNS,
    STRONG_INTENTS,
    CONTEXT_AWARE_INTENTS,
    DomainType,
)

__all__ = [
    "DOMAIN_KEYWORDS",
    "ASTRO_INTENT_PATTERNS",
    "TRAVEL_INTENT_PATTERNS",
    "UTILITY_INTENT_PATTERNS",
    "STRONG_INTENTS",
    "CONTEXT_AWARE_INTENTS",
    "DomainType",
]
