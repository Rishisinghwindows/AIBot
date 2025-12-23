"""
Internationalization (i18n) for Indian Languages

Provides multi-language support for:
- 22 scheduled Indian languages
- Auto language detection from user messages
- Response translation
- Astrology-specific vocabulary (zodiac, nakshatra names)

Usage:
    from app.i18n import get_translator, detect_language

    # Detect user's language
    lang = detect_language("मेरी कुंडली बनाओ")  # Returns "hi"

    # Get translated response
    translator = get_translator()
    response = translator.get("horoscope.intro", lang="hi", sign="Aries")
"""

from app.i18n.detector import detect_language, get_language_name, is_supported_language
from app.i18n.translator import Translator, get_translator, t, get_zodiac_in_language
from app.i18n.constants import (
    SUPPORTED_LANGUAGES,
    LANGUAGE_NAMES,
    ZODIAC_SIGNS,
    NAKSHATRA_NAMES,
    RASHI_NAMES,
    RASHI_TO_ENGLISH,
    PLANET_NAMES,
)

__all__ = [
    # Detection
    "detect_language",
    "get_language_name",
    "is_supported_language",

    # Translation
    "Translator",
    "get_translator",
    "t",
    "get_zodiac_in_language",

    # Constants
    "SUPPORTED_LANGUAGES",
    "LANGUAGE_NAMES",
    "ZODIAC_SIGNS",
    "NAKSHATRA_NAMES",
    "RASHI_NAMES",
    "RASHI_TO_ENGLISH",
    "PLANET_NAMES",
]
