"""
Utility functions for the bot.

Provides:
- Response formatting for WhatsApp
- Rate limiting
- Entity extraction (PNR, train numbers, birth details)
- Common helper functions
"""

from common.utils.response_formatter import (
    WhatsAppFormatter,
    AstroResponseFormatter,
    format_error_response,
    format_missing_fields_response,
    format_success_response,
    build_astro_response,
)

from common.utils.rate_limiter import (
    RateLimitConfig,
    RateLimitExceeded,
    InMemoryRateLimiter,
    get_rate_limiter,
    rate_limited,
    format_rate_limit_response,
)

from common.utils.entity_extraction import (
    extract_pnr,
    extract_train_number,
    extract_birth_date,
    extract_birth_time,
    extract_birth_place,
    extract_birth_details,
    extract_zodiac_sign,
    extract_name,
    BirthDetails,
    ExtractionResult,
    ZODIAC_SIGNS,
)

__all__ = [
    # Response formatting
    "WhatsAppFormatter",
    "AstroResponseFormatter",
    "format_error_response",
    "format_missing_fields_response",
    "format_success_response",
    "build_astro_response",
    # Rate limiting
    "RateLimitConfig",
    "RateLimitExceeded",
    "InMemoryRateLimiter",
    "get_rate_limiter",
    "rate_limited",
    "format_rate_limit_response",
    # Entity extraction
    "extract_pnr",
    "extract_train_number",
    "extract_birth_date",
    "extract_birth_time",
    "extract_birth_place",
    "extract_birth_details",
    "extract_zodiac_sign",
    "extract_name",
    "BirthDetails",
    "ExtractionResult",
    "ZODIAC_SIGNS",
]
