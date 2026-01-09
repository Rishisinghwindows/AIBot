"""
Internationalization (i18n) for Indian Languages

Provides multi-language support for:
- 22 scheduled Indian languages
- Auto language detection from user messages
- Response translation
- Astrology-specific vocabulary (zodiac, nakshatra names)

Usage:
    from common.i18n import get_translator, detect_language

    # Detect user's language
    lang = detect_language("मेरी कुंडली बनाओ")  # Returns "hi"

    # Get translated response
    translator = get_translator()
    response = translator.get("horoscope.intro", lang="hi", sign="Aries")
"""

from common.i18n.detector import detect_language, get_language_name
from common.i18n.translator import Translator, get_translator
from common.i18n.constants import (
    SUPPORTED_LANGUAGES,
    LANGUAGE_NAMES,
    ZODIAC_SIGNS,
    NAKSHATRA_NAMES,
    RASHI_NAMES,
)

__all__ = [
    # Detection
    "detect_language",
    "get_language_name",

    # Translation
    "Translator",
    "get_translator",

    # Constants
    "SUPPORTED_LANGUAGES",
    "LANGUAGE_NAMES",
    "ZODIAC_SIGNS",
    "NAKSHATRA_NAMES",
    "RASHI_NAMES",
]
