"""
Translator

Provides translation services using:
1. Pre-defined templates (fast, no API calls)
2. Astrology vocabulary (zodiac, nakshatra names)
"""

import logging
import json
from typing import Optional, Dict
from pathlib import Path

from app.i18n.constants import SUPPORTED_LANGUAGES, ZODIAC_SIGNS, NAKSHATRA_NAMES, PLANET_NAMES

logger = logging.getLogger(__name__)

# Templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


class Translator:
    """
    Multi-language translator for bot responses.

    Features:
    - Template-based translations (pre-defined responses)
    - Variable substitution in templates
    - Fallback to English
    - Astrology vocabulary translation
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize translator.

        Args:
            api_key: Translation API key (optional, for future use)
        """
        self.api_key = api_key
        self._templates: Dict[str, Dict[str, str]] = {}
        self._load_templates()

    def _load_templates(self):
        """Load all template files."""
        if not TEMPLATES_DIR.exists():
            logger.debug(f"Templates directory not found: {TEMPLATES_DIR}")
            return

        for lang_file in TEMPLATES_DIR.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self._templates[lang_code] = json.load(f)
                logger.debug(f"Loaded templates for {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load {lang_file}: {e}")

    def get(
        self,
        key: str,
        lang: str = "en",
        default: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Get translated string by key.

        Args:
            key: Template key (e.g., "horoscope.intro")
            lang: Target language code
            default: Default if key not found
            **kwargs: Variables to substitute

        Returns:
            Translated string with variables substituted
        """
        lang = lang.lower()
        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"

        template = self._get_template(key, lang)
        if not template:
            template = self._get_template(key, "en")
        if not template:
            return default or key

        try:
            translated_kwargs = self._translate_kwargs(kwargs, lang)
            return template.format(**translated_kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable in template {key}: {e}")
            return template
        except Exception as e:
            logger.error(f"Error formatting template {key}: {e}")
            return template

    def _get_template(self, key: str, lang: str) -> Optional[str]:
        """Get template by key from language templates."""
        if lang not in self._templates:
            return None

        parts = key.split(".")
        data = self._templates[lang]

        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return None

        return data if isinstance(data, str) else None

    def _translate_kwargs(self, kwargs: dict, lang: str) -> dict:
        """Translate special values in kwargs (zodiac signs, etc.)."""
        translated = {}

        for key, value in kwargs.items():
            if key in ("sign", "zodiac", "rashi"):
                translated[key] = self.get_zodiac_name(value, lang)
            elif key == "nakshatra":
                translated[key] = self.get_nakshatra_name(value, lang)
            elif key == "planet":
                translated[key] = self.get_planet_name(value, lang)
            else:
                translated[key] = value

        return translated

    def get_zodiac_name(self, sign: str, lang: str = "en") -> str:
        """
        Get zodiac sign name in specified language.

        Args:
            sign: English sign name (e.g., "aries", "Aries")
            lang: Target language

        Returns:
            Translated sign name
        """
        sign_lower = sign.lower()
        if sign_lower in ZODIAC_SIGNS:
            return ZODIAC_SIGNS[sign_lower].get(lang, ZODIAC_SIGNS[sign_lower]["en"])
        return sign

    def get_nakshatra_name(self, nakshatra: str, lang: str = "en") -> str:
        """Get nakshatra name in specified language."""
        nakshatra_lower = nakshatra.lower().replace(" ", "_")
        if nakshatra_lower in NAKSHATRA_NAMES:
            return NAKSHATRA_NAMES[nakshatra_lower].get(lang, NAKSHATRA_NAMES[nakshatra_lower]["en"])
        return nakshatra

    def get_planet_name(self, planet: str, lang: str = "en") -> str:
        """Get planet name in specified language."""
        planet_lower = planet.lower()
        if planet_lower in PLANET_NAMES:
            return PLANET_NAMES[planet_lower].get(lang, PLANET_NAMES[planet_lower]["en"])
        return planet

    def has_template(self, key: str, lang: str = "en") -> bool:
        """Check if template exists for key."""
        return self._get_template(key, lang) is not None


# =============================================================================
# SINGLETON
# =============================================================================

_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Get singleton Translator instance."""
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def t(key: str, lang: str = "en", **kwargs) -> str:
    """
    Shorthand for translator.get()

    Usage:
        from app.i18n.translator import t
        message = t("horoscope.intro", lang="hi", sign="Aries")
    """
    return get_translator().get(key, lang, **kwargs)


def get_zodiac_in_language(sign: str, lang: str) -> str:
    """Get zodiac sign name in language."""
    return get_translator().get_zodiac_name(sign, lang)
