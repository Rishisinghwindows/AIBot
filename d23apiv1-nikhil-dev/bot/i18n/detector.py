"""
Language Detector

Auto-detects the language of user messages based on:
1. Unicode script ranges
2. Common words/patterns
3. User preference (stored)
"""

import re
import logging
from typing import Optional, Tuple
from collections import Counter

from bot.i18n.constants import SCRIPT_RANGES, LANGUAGE_NAMES

logger = logging.getLogger(__name__)


# =============================================================================
# SCRIPT-BASED DETECTION
# =============================================================================

def detect_script(text: str) -> Optional[str]:
    """
    Detect the primary script used in text.

    Args:
        text: Input text

    Returns:
        Script name or None if only ASCII/Latin
    """
    script_counts = Counter()

    for char in text:
        code = ord(char)
        for script_name, (start, end) in SCRIPT_RANGES.items():
            if start <= code <= end:
                script_counts[script_name] += 1
                break

    if not script_counts:
        return None

    return script_counts.most_common(1)[0][0]


def script_to_language(script: str) -> str:
    """
    Map detected script to most likely language.

    Args:
        script: Script name

    Returns:
        Language code
    """
    mapping = {
        "devanagari": "hi",    # Could be Hindi, Marathi, Sanskrit, Nepali
        "bengali": "bn",       # Could be Bengali or Assamese
        "gurmukhi": "pa",      # Punjabi
        "gujarati": "gu",      # Gujarati
        "oriya": "or",         # Odia
        "tamil": "ta",         # Tamil
        "telugu": "te",        # Telugu
        "kannada": "kn",       # Kannada
        "malayalam": "ml",     # Malayalam
        "arabic": "ur",        # Could be Urdu, Kashmiri, Sindhi
        "ol_chiki": "sat",     # Santali
    }
    return mapping.get(script, "en")


# =============================================================================
# KEYWORD-BASED DETECTION
# =============================================================================

# Common words/patterns for each language
LANGUAGE_KEYWORDS = {
    "hi": [
        # Greetings
        "नमस्ते", "नमस्कार", "कैसे", "क्या", "कहाँ", "कब", "क्यों",
        # Common words
        "है", "हैं", "था", "थी", "थे", "हो", "हूँ", "और", "या", "में", "पर", "को",
        "का", "की", "के", "से", "ने", "यह", "वह", "मैं", "तुम", "आप", "हम",
        # Astrology
        "राशि", "कुंडली", "जन्म", "ग्रह", "राशिफल", "भविष्य",
        # Romanized Hindi
        "kya", "kaise", "kahan", "kab", "kyun", "hai", "hain", "mera", "meri",
        "aapka", "tumhara", "namaste", "dhanyavaad", "shukriya",
    ],
    "bn": [
        "নমস্কার", "কেমন", "কি", "কোথায়", "কবে", "কেন",
        "আছে", "আছি", "আছো", "এবং", "বা", "মধ্যে", "উপর",
        "আমি", "তুমি", "আপনি", "সে", "তারা",
        "রাশি", "কুন্ডলী", "জন্ম", "গ্রহ",
    ],
    "ta": [
        "வணக்கம்", "எப்படி", "என்ன", "எங்கே", "எப்போது", "ஏன்",
        "இருக்கிறது", "உள்ளது", "மற்றும்", "அல்லது",
        "நான்", "நீ", "நீங்கள்", "அவன்", "அவள்",
        "ராசி", "ஜாதகம்", "பிறப்பு", "கிரகம்",
    ],
    "te": [
        "నమస్కారం", "ఎలా", "ఏమిటి", "ఎక్కడ", "ఎప్పుడు", "ఎందుకు",
        "ఉంది", "ఉన్నాయి", "మరియు", "లేదా",
        "నేను", "నీవు", "మీరు", "అతను", "ఆమె",
        "రాశి", "జాతకం", "జన్మ", "గ్రహం",
    ],
    "mr": [
        "नमस्कार", "कसे", "काय", "कुठे", "केव्हा", "का",
        "आहे", "आहेत", "होते", "होती", "आणि", "किंवा",
        "मी", "तू", "तुम्ही", "तो", "ती",
        "राशी", "कुंडली", "जन्म", "ग्रह",
    ],
    "gu": [
        "નમસ્તે", "કેમ", "શું", "ક્યાં", "ક્યારે", "કેમ",
        "છે", "છો", "છું", "અને", "અથવા",
        "હું", "તું", "તમે", "તે", "તેણી",
        "રાશી", "કુંડળી", "જન્મ", "ગ્રહ",
    ],
    "kn": [
        "ನಮಸ್ಕಾರ", "ಹೇಗೆ", "ಏನು", "ಎಲ್ಲಿ", "ಯಾವಾಗ", "ಏಕೆ",
        "ಇದೆ", "ಇವೆ", "ಮತ್ತು", "ಅಥವಾ",
        "ನಾನು", "ನೀನು", "ನೀವು", "ಅವನು", "ಅವಳು",
        "ರಾಶಿ", "ಜಾತಕ", "ಜನ್ಮ", "ಗ್ರಹ",
    ],
    "ml": [
        "നമസ്കാരം", "എങ്ങനെ", "എന്ത്", "എവിടെ", "എപ്പോൾ", "എന്തുകൊണ്ട്",
        "ഉണ്ട്", "ഉണ്ടായിരുന്നു", "ഉം", "അല്ലെങ്കിൽ",
        "ഞാൻ", "നീ", "നിങ്ങൾ", "അവൻ", "അവൾ",
        "രാശി", "ജാതകം", "ജനനം", "ഗ്രഹം",
    ],
    "pa": [
        "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "ਕਿਵੇਂ", "ਕੀ", "ਕਿੱਥੇ", "ਕਦੋਂ", "ਕਿਉਂ",
        "ਹੈ", "ਹਨ", "ਸੀ", "ਅਤੇ", "ਜਾਂ",
        "ਮੈਂ", "ਤੂੰ", "ਤੁਸੀਂ", "ਉਹ",
        "ਰਾਸ਼ੀ", "ਕੁੰਡਲੀ", "ਜਨਮ", "ਗ੍ਰਹਿ",
    ],
    "or": [
        "ନମସ୍କାର", "କେମିତି", "କଣ", "କେଉଁଠି", "କେବେ", "କାହିଁକି",
        "ଅଛି", "ଅଛନ୍ତି", "ଏବଂ", "କିମ୍ବା",
        "ମୁଁ", "ତୁ", "ଆପଣ", "ସେ",
        "ରାଶି", "କୁଣ୍ଡଳୀ", "ଜନ୍ମ", "ଗ୍ରହ",
    ],
    "ur": [
        "السلام علیکم", "کیسے", "کیا", "کہاں", "کب", "کیوں",
        "ہے", "ہیں", "تھا", "تھی", "اور", "یا",
        "میں", "تم", "آپ", "وہ",
    ],
    "bho": [
        # Bhojpuri keywords (uses Devanagari script like Hindi)
        "रउआ", "हमार", "तोहार", "काहे", "केकरा", "कइसे",
        "बा", "बाड़े", "रहल", "गइल", "आइल",
        "भोजपुरी", "भैया", "बहिनी",
    ],
}


def detect_by_keywords(text: str) -> Optional[str]:
    """
    Detect language by matching common words.

    Args:
        text: Input text

    Returns:
        Language code or None
    """
    text_lower = text.lower()
    scores = Counter()

    for lang, keywords in LANGUAGE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                scores[lang] += 1

    if not scores:
        return None

    # Return language with highest score (if significant)
    best_lang, best_score = scores.most_common(1)[0]
    if best_score >= 1:  # At least one keyword match
        return best_lang

    return None


# =============================================================================
# MAIN DETECTION FUNCTION
# =============================================================================

def detect_language(text: str, default: str = "en") -> str:
    """
    Detect the language of input text.

    Detection priority:
    1. Script-based detection (most reliable for non-Latin scripts)
    2. Keyword-based detection
    3. Default to English

    Args:
        text: Input text
        default: Default language if detection fails

    Returns:
        Language code (e.g., "hi", "bn", "ta")
    """
    if not text or not text.strip():
        return default

    # Try script-based detection first
    script = detect_script(text)
    if script:
        return script_to_language(script)

    # Try keyword-based detection (for Romanized text)
    keyword_lang = detect_by_keywords(text)
    if keyword_lang:
        return keyword_lang

    return default


def get_language_name(code: str, display_in: str = "en") -> str:
    """
    Get human-readable language name.

    Args:
        code: Language code (e.g., "hi")
        display_in: Language for display ("en" or "native")

    Returns:
        Language name
    """
    if code in LANGUAGE_NAMES:
        key = "native" if display_in == "native" else "en"
        return LANGUAGE_NAMES[code].get(key, code)
    return code


def is_supported_language(code: str) -> bool:
    """Check if language code is supported."""
    from bot.i18n.constants import SUPPORTED_LANGUAGES
    return code in SUPPORTED_LANGUAGES


# =============================================================================
# ADVANCED DETECTION (with confidence)
# =============================================================================

def detect_language_with_confidence(text: str) -> Tuple[str, float]:
    """
    Detect language with confidence score.

    Args:
        text: Input text

    Returns:
        Tuple of (language_code, confidence 0-1)
    """
    if not text or not text.strip():
        return ("en", 0.5)

    # Script detection is highly confident
    script = detect_script(text)
    if script:
        # Count how many characters are in the detected script
        script_chars = 0
        total_chars = 0
        start, end = SCRIPT_RANGES[script]

        for char in text:
            if not char.isspace():
                total_chars += 1
                if start <= ord(char) <= end:
                    script_chars += 1

        confidence = script_chars / total_chars if total_chars > 0 else 0
        return (script_to_language(script), min(0.95, 0.7 + confidence * 0.25))

    # Keyword detection has lower confidence
    keyword_lang = detect_by_keywords(text)
    if keyword_lang:
        return (keyword_lang, 0.6)

    return ("en", 0.4)
