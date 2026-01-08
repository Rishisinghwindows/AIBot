"""
i18n Constants

Language codes, zodiac names, and astrology vocabulary in Indian languages.
"""

from typing import Dict, List

# =============================================================================
# SUPPORTED LANGUAGES (22 Scheduled Indian Languages + English)
# =============================================================================

SUPPORTED_LANGUAGES = [
    "en",   # English
    "hi",   # Hindi
    "bn",   # Bengali
    "te",   # Telugu
    "mr",   # Marathi
    "ta",   # Tamil
    "gu",   # Gujarati
    "kn",   # Kannada
    "ml",   # Malayalam
    "pa",   # Punjabi
    "or",   # Odia
    "as",   # Assamese
    "mai",  # Maithili
    "sa",   # Sanskrit
    "ur",   # Urdu
    "sd",   # Sindhi
    "kok",  # Konkani
    "ne",   # Nepali
    "mni",  # Manipuri
    "brx",  # Bodo
    "doi",  # Dogri
    "ks",   # Kashmiri
    "sat",  # Santali
    "bho",  # Bhojpuri
]

LANGUAGE_NAMES: Dict[str, Dict[str, str]] = {
    "en": {"en": "English", "native": "English"},
    "hi": {"en": "Hindi", "native": "हिन्दी"},
    "bn": {"en": "Bengali", "native": "বাংলা"},
    "te": {"en": "Telugu", "native": "తెలుగు"},
    "mr": {"en": "Marathi", "native": "मराठी"},
    "ta": {"en": "Tamil", "native": "தமிழ்"},
    "gu": {"en": "Gujarati", "native": "ગુજરાતી"},
    "kn": {"en": "Kannada", "native": "ಕನ್ನಡ"},
    "ml": {"en": "Malayalam", "native": "മലയാളം"},
    "pa": {"en": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    "or": {"en": "Odia", "native": "ଓଡ଼ିଆ"},
    "as": {"en": "Assamese", "native": "অসমীয়া"},
    "mai": {"en": "Maithili", "native": "मैथिली"},
    "sa": {"en": "Sanskrit", "native": "संस्कृतम्"},
    "ur": {"en": "Urdu", "native": "اردو"},
    "sd": {"en": "Sindhi", "native": "سنڌي"},
    "kok": {"en": "Konkani", "native": "कोंकणी"},
    "ne": {"en": "Nepali", "native": "नेपाली"},
    "mni": {"en": "Manipuri", "native": "মণিপুরী"},
    "brx": {"en": "Bodo", "native": "बड़ो"},
    "doi": {"en": "Dogri", "native": "डोगरी"},
    "ks": {"en": "Kashmiri", "native": "کٲشُر"},
    "sat": {"en": "Santali", "native": "ᱥᱟᱱᱛᱟᱲᱤ"},
    "bho": {"en": "Bhojpuri", "native": "भोजपुरी"},
}


# =============================================================================
# ZODIAC SIGNS (Western) in Indian Languages
# =============================================================================

ZODIAC_SIGNS: Dict[str, Dict[str, str]] = {
    "aries": {
        "en": "Aries",
        "hi": "मेष",
        "bn": "মেষ",
        "te": "మేషం",
        "mr": "मेष",
        "ta": "மேஷம்",
        "gu": "મેષ",
        "kn": "ಮೇಷ",
        "ml": "മേടം",
        "pa": "ਮੇਖ",
        "or": "ମେଷ",
        "sa": "मेषः",
    },
    "taurus": {
        "en": "Taurus",
        "hi": "वृषभ",
        "bn": "বৃষ",
        "te": "వృషభం",
        "mr": "वृषभ",
        "ta": "ரிஷபம்",
        "gu": "વૃષભ",
        "kn": "ವೃಷಭ",
        "ml": "ഇടവം",
        "pa": "ਬ੍ਰਿਸ਼",
        "or": "ବୃଷ",
        "sa": "वृषभः",
    },
    "gemini": {
        "en": "Gemini",
        "hi": "मिथुन",
        "bn": "মিথুন",
        "te": "మిథునం",
        "mr": "मिथुन",
        "ta": "மிதுனம்",
        "gu": "મિથુન",
        "kn": "ಮಿಥುನ",
        "ml": "മിഥുനം",
        "pa": "ਮਿਥੁਨ",
        "or": "ମିଥୁନ",
        "sa": "मिथुनम्",
    },
    "cancer": {
        "en": "Cancer",
        "hi": "कर्क",
        "bn": "কর্কট",
        "te": "కర్కాటకం",
        "mr": "कर्क",
        "ta": "கடகம்",
        "gu": "કર્ક",
        "kn": "ಕರ್ಕಾಟಕ",
        "ml": "കർക്കടകം",
        "pa": "ਕਰਕ",
        "or": "କର୍କଟ",
        "sa": "कर्कटः",
    },
    "leo": {
        "en": "Leo",
        "hi": "सिंह",
        "bn": "সিংহ",
        "te": "సింహం",
        "mr": "सिंह",
        "ta": "சிம்மம்",
        "gu": "સિંહ",
        "kn": "ಸಿಂಹ",
        "ml": "ചിങ്ങം",
        "pa": "ਸਿੰਘ",
        "or": "ସିଂହ",
        "sa": "सिंहः",
    },
    "virgo": {
        "en": "Virgo",
        "hi": "कन्या",
        "bn": "কন্যা",
        "te": "కన్య",
        "mr": "कन्या",
        "ta": "கன்னி",
        "gu": "કન્યા",
        "kn": "ಕನ್ಯಾ",
        "ml": "കന്നി",
        "pa": "ਕੰਨਿਆ",
        "or": "କନ୍ୟା",
        "sa": "कन्या",
    },
    "libra": {
        "en": "Libra",
        "hi": "तुला",
        "bn": "তুলা",
        "te": "తుల",
        "mr": "तूळ",
        "ta": "துலாம்",
        "gu": "તુલા",
        "kn": "ತುಲಾ",
        "ml": "തുലാം",
        "pa": "ਤੁਲਾ",
        "or": "ତୁଳା",
        "sa": "तुला",
    },
    "scorpio": {
        "en": "Scorpio",
        "hi": "वृश्चिक",
        "bn": "বৃশ্চিক",
        "te": "వృశ్చికం",
        "mr": "वृश्चिक",
        "ta": "விருச்சிகம்",
        "gu": "વૃશ્ચિક",
        "kn": "ವೃಶ್ಚಿಕ",
        "ml": "വൃശ്ചികം",
        "pa": "ਬ੍ਰਿਸ਼ਚਕ",
        "or": "ବୃଶ୍ଚିକ",
        "sa": "वृश्चिकः",
    },
    "sagittarius": {
        "en": "Sagittarius",
        "hi": "धनु",
        "bn": "ধনু",
        "te": "ధనుస్సు",
        "mr": "धनु",
        "ta": "தனுசு",
        "gu": "ધન",
        "kn": "ಧನು",
        "ml": "ധനു",
        "pa": "ਧਨੁ",
        "or": "ଧନୁ",
        "sa": "धनुः",
    },
    "capricorn": {
        "en": "Capricorn",
        "hi": "मकर",
        "bn": "মকর",
        "te": "మకరం",
        "mr": "मकर",
        "ta": "மகரம்",
        "gu": "મકર",
        "kn": "ಮಕರ",
        "ml": "മകരം",
        "pa": "ਮਕਰ",
        "or": "ମକର",
        "sa": "मकरः",
    },
    "aquarius": {
        "en": "Aquarius",
        "hi": "कुम्भ",
        "bn": "কুম্ভ",
        "te": "కుంభం",
        "mr": "कुंभ",
        "ta": "கும்பம்",
        "gu": "કુંભ",
        "kn": "ಕುಂಭ",
        "ml": "കുംഭം",
        "pa": "ਕੁੰਭ",
        "or": "କୁମ୍ଭ",
        "sa": "कुम्भः",
    },
    "pisces": {
        "en": "Pisces",
        "hi": "मीन",
        "bn": "মীন",
        "te": "మీనం",
        "mr": "मीन",
        "ta": "மீனம்",
        "gu": "મીન",
        "kn": "ಮೀನ",
        "ml": "മീനം",
        "pa": "ਮੀਨ",
        "or": "ମୀନ",
        "sa": "मीनः",
    },
}

# Reverse mapping: Hindi name to English
RASHI_TO_ENGLISH = {
    "मेष": "aries", "mesh": "aries",
    "वृषभ": "taurus", "vrishabh": "taurus",
    "मिथुन": "gemini", "mithun": "gemini",
    "कर्क": "cancer", "kark": "cancer",
    "सिंह": "leo", "singh": "leo", "simha": "leo",
    "कन्या": "virgo", "kanya": "virgo",
    "तुला": "libra", "tula": "libra",
    "वृश्चिक": "scorpio", "vrishchik": "scorpio",
    "धनु": "sagittarius", "dhanu": "sagittarius",
    "मकर": "capricorn", "makar": "capricorn",
    "कुम्भ": "aquarius", "kumbh": "aquarius",
    "मीन": "pisces", "meen": "pisces",
}


# =============================================================================
# RASHI NAMES (Indian zodiac - same as Western but different tradition)
# =============================================================================

RASHI_NAMES = ZODIAC_SIGNS  # Same signs, different naming


# =============================================================================
# NAKSHATRA NAMES (27 Lunar Mansions)
# =============================================================================

NAKSHATRA_NAMES: Dict[str, Dict[str, str]] = {
    "ashwini": {"en": "Ashwini", "hi": "अश्विनी", "sa": "अश्विनी"},
    "bharani": {"en": "Bharani", "hi": "भरणी", "sa": "भरणी"},
    "krittika": {"en": "Krittika", "hi": "कृत्तिका", "sa": "कृत्तिका"},
    "rohini": {"en": "Rohini", "hi": "रोहिणी", "sa": "रोहिणी"},
    "mrigashira": {"en": "Mrigashira", "hi": "मृगशिरा", "sa": "मृगशीर्षा"},
    "ardra": {"en": "Ardra", "hi": "आर्द्रा", "sa": "आर्द्रा"},
    "punarvasu": {"en": "Punarvasu", "hi": "पुनर्वसु", "sa": "पुनर्वसु"},
    "pushya": {"en": "Pushya", "hi": "पुष्य", "sa": "पुष्य"},
    "ashlesha": {"en": "Ashlesha", "hi": "आश्लेषा", "sa": "आश्लेषा"},
    "magha": {"en": "Magha", "hi": "मघा", "sa": "मघा"},
    "purva_phalguni": {"en": "Purva Phalguni", "hi": "पूर्वा फाल्गुनी", "sa": "पूर्वफाल्गुनी"},
    "uttara_phalguni": {"en": "Uttara Phalguni", "hi": "उत्तरा फाल्गुनी", "sa": "उत्तरफाल्गुनी"},
    "hasta": {"en": "Hasta", "hi": "हस्त", "sa": "हस्त"},
    "chitra": {"en": "Chitra", "hi": "चित्रा", "sa": "चित्रा"},
    "swati": {"en": "Swati", "hi": "स्वाति", "sa": "स्वाति"},
    "vishakha": {"en": "Vishakha", "hi": "विशाखा", "sa": "विशाखा"},
    "anuradha": {"en": "Anuradha", "hi": "अनुराधा", "sa": "अनुराधा"},
    "jyeshtha": {"en": "Jyeshtha", "hi": "ज्येष्ठा", "sa": "ज्येष्ठा"},
    "mula": {"en": "Mula", "hi": "मूल", "sa": "मूल"},
    "purva_ashadha": {"en": "Purva Ashadha", "hi": "पूर्वाषाढ़ा", "sa": "पूर्वाषाढा"},
    "uttara_ashadha": {"en": "Uttara Ashadha", "hi": "उत्तराषाढ़ा", "sa": "उत्तराषाढा"},
    "shravana": {"en": "Shravana", "hi": "श्रवण", "sa": "श्रवण"},
    "dhanishta": {"en": "Dhanishta", "hi": "धनिष्ठा", "sa": "धनिष्ठा"},
    "shatabhisha": {"en": "Shatabhisha", "hi": "शतभिषा", "sa": "शतभिषा"},
    "purva_bhadrapada": {"en": "Purva Bhadrapada", "hi": "पूर्वभाद्रपद", "sa": "पूर्वभाद्रपदा"},
    "uttara_bhadrapada": {"en": "Uttara Bhadrapada", "hi": "उत्तरभाद्रपद", "sa": "उत्तरभाद्रपदा"},
    "revati": {"en": "Revati", "hi": "रेवती", "sa": "रेवती"},
}


# =============================================================================
# PLANET NAMES
# =============================================================================

PLANET_NAMES: Dict[str, Dict[str, str]] = {
    "sun": {"en": "Sun", "hi": "सूर्य", "sa": "सूर्यः"},
    "moon": {"en": "Moon", "hi": "चंद्र", "sa": "चन्द्रः"},
    "mars": {"en": "Mars", "hi": "मंगल", "sa": "मङ्गलः"},
    "mercury": {"en": "Mercury", "hi": "बुध", "sa": "बुधः"},
    "jupiter": {"en": "Jupiter", "hi": "गुरु", "sa": "गुरुः"},
    "venus": {"en": "Venus", "hi": "शुक्र", "sa": "शुक्रः"},
    "saturn": {"en": "Saturn", "hi": "शनि", "sa": "शनिः"},
    "rahu": {"en": "Rahu", "hi": "राहु", "sa": "राहुः"},
    "ketu": {"en": "Ketu", "hi": "केतु", "sa": "केतुः"},
}


# =============================================================================
# DAYS OF WEEK
# =============================================================================

WEEKDAY_NAMES: Dict[str, Dict[str, str]] = {
    "sunday": {"en": "Sunday", "hi": "रविवार"},
    "monday": {"en": "Monday", "hi": "सोमवार"},
    "tuesday": {"en": "Tuesday", "hi": "मंगलवार"},
    "wednesday": {"en": "Wednesday", "hi": "बुधवार"},
    "thursday": {"en": "Thursday", "hi": "गुरुवार"},
    "friday": {"en": "Friday", "hi": "शुक्रवार"},
    "saturday": {"en": "Saturday", "hi": "शनिवार"},
}


# =============================================================================
# SCRIPT RANGES (for language detection)
# =============================================================================

SCRIPT_RANGES = {
    "devanagari": (0x0900, 0x097F),    # Hindi, Marathi, Sanskrit, Nepali
    "bengali": (0x0980, 0x09FF),       # Bengali, Assamese
    "gurmukhi": (0x0A00, 0x0A7F),      # Punjabi
    "gujarati": (0x0A80, 0x0AFF),      # Gujarati
    "oriya": (0x0B00, 0x0B7F),         # Odia
    "tamil": (0x0B80, 0x0BFF),         # Tamil
    "telugu": (0x0C00, 0x0C7F),        # Telugu
    "kannada": (0x0C80, 0x0CFF),       # Kannada
    "malayalam": (0x0D00, 0x0D7F),     # Malayalam
    "arabic": (0x0600, 0x06FF),        # Urdu, Kashmiri, Sindhi
    "ol_chiki": (0x1C50, 0x1C7F),      # Santali
}
