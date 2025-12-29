"""
Translator

Provides translation services using:
1. Pre-defined templates (fast, no API calls)
2. Optional Google Translate API (for dynamic content)
"""

import logging
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

from bot.i18n.constants import SUPPORTED_LANGUAGES, ZODIAC_SIGNS, NAKSHATRA_NAMES, PLANET_NAMES

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
    - Optional API translation for dynamic content
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize translator.

        Args:
            api_key: Google Translate API key (optional)
        """
        self.api_key = api_key
        self._templates: Dict[str, Dict[str, str]] = {}
        self._load_templates()

    def _load_templates(self):
        """Load all template files."""
        if not TEMPLATES_DIR.exists():
            logger.warning(f"Templates directory not found: {TEMPLATES_DIR}")
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
            key: Template key (e.g., "horoscope.intro", "flow.birth_date.prompt")
            lang: Target language code
            default: Default if key not found
            **kwargs: Variables to substitute

        Returns:
            Translated string with variables substituted

        Example:
            translator.get("horoscope.intro", lang="hi", sign="Aries")
            # Returns: "आज का मेष राशिफल"
        """
        # Normalize language code
        lang = lang.lower()
        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"

        # Get template
        template = self._get_template(key, lang)
        if not template:
            template = self._get_template(key, "en")  # Fallback to English
        if not template:
            return default or key

        # Substitute variables
        try:
            # Translate any zodiac/nakshatra names in kwargs
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

        # Support nested keys like "horoscope.intro"
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
            if key == "sign" or key == "zodiac" or key == "rashi":
                # Translate zodiac sign
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

    async def translate_text(self, text: str, target_lang: str, source_lang: str = "en") -> str:
        """
        Translate arbitrary text using API (if available).

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code

        Returns:
            Translated text (or original if API unavailable)
        """
        if not self.api_key:
            logger.debug("No translation API key configured")
            return text

        if target_lang == source_lang:
            return text

        try:
            # Use Google Translate API
            from google.cloud import translate_v2 as translate
            client = translate.Client()

            result = client.translate(
                text,
                target_language=target_lang,
                source_language=source_lang
            )
            return result["translatedText"]

        except ImportError:
            logger.warning("google-cloud-translate not installed")
            return text
        except Exception as e:
            logger.error(f"Translation API error: {e}")
            return text

    def has_template(self, key: str, lang: str = "en") -> bool:
        """Check if template exists for key."""
        return self._get_template(key, lang) is not None

    def get_all_keys(self, lang: str = "en") -> list:
        """Get all template keys for a language."""
        if lang not in self._templates:
            return []

        def _flatten_keys(d: dict, prefix: str = "") -> list:
            keys = []
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.extend(_flatten_keys(v, full_key))
                else:
                    keys.append(full_key)
            return keys

        return _flatten_keys(self._templates[lang])


# =============================================================================
# SINGLETON
# =============================================================================

_translator: Optional[Translator] = None


def get_translator() -> Translator:
    """Get singleton Translator instance."""
    global _translator
    if _translator is None:
        from bot.config import settings
        _translator = Translator(api_key=settings.TRANSLATION_API or None)
    return _translator


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def t(key: str, lang: str = "en", **kwargs) -> str:
    """
    Shorthand for translator.get()

    Usage:
        from bot.i18n.translator import t
        message = t("horoscope.intro", lang="hi", sign="Aries")
    """
    return get_translator().get(key, lang, **kwargs)


def get_zodiac_in_language(sign: str, lang: str) -> str:
    """Get zodiac sign name in language."""
    return get_translator().get_zodiac_name(sign, lang)
