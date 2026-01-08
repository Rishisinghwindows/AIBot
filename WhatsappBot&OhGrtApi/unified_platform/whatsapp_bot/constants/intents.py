"""
Centralized Intent and Domain Keywords

Single source of truth for all intent classification patterns.
Prevents duplicate keyword definitions across the codebase.
"""

from typing import Literal, Dict, List

# =============================================================================
# DOMAIN TYPES
# =============================================================================

DomainType = Literal["astrology", "travel", "utility", "game", "conversation"]


# =============================================================================
# DOMAIN KEYWORDS
# =============================================================================

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "astrology": [
        # Horoscope
        "horoscope", "rashifal", "zodiac", "prediction",
        # Signs
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        # Hindi signs
        "mesh", "vrishabh", "mithun", "kark", "singh", "kanya",
        "tula", "vrishchik", "dhanu", "makar", "kumbh", "meen",
        # Kundli
        "kundli", "kundali", "birth chart", "janam patri", "janam kundali",
        # Matching
        "compatibility", "gun milan", "matching",
        # Doshas
        "manglik", "mangal dosha", "kaal sarp", "sade sati", "pitra dosha",
        # Predictions
        "when will i", "will i get", "marriage prediction", "career prediction",
        # Panchang
        "panchang", "panchangam", "tithi", "nakshatra", "rahu kaal",
        # Numerology & Tarot
        "numerology", "lucky number", "tarot", "card reading",
        # General
        "astrology", "astrologer", "planetary", "dasha", "transit",
        "gemstone", "remedy", "muhurta",
    ],
    "travel": [
        "pnr", "pnr status",
        "train", "train status", "running status", "train number",
        "metro", "metro route", "metro fare",
        "flight", "flight status",
        "bus", "bus booking",
    ],
    "utility": [
        "weather", "temperature", "forecast", "rain", "humidity",
        "news", "headlines", "breaking",
        "generate image", "create image", "draw", "picture", "make image",
        "remind", "reminder", "alarm", "notify",
        "search", "find", "near me", "nearby", "restaurants", "hotels",
        "hospital", "atm", "pharmacy",
    ],
    "game": [
        "game", "play", "word game", "puzzle", "quiz",
        "wordle", "jumble", "trivia",
    ],
}


# =============================================================================
# ASTROLOGY INTENT PATTERNS (Regex)
# =============================================================================

ASTRO_INTENT_PATTERNS: Dict[str, List[str]] = {
    "horoscope": [
        r"horoscope", r"rashifal", r"zodiac.*prediction",
        r"(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces).*(?:today|weekly|monthly|tomorrow)",
        r"(?:today|weekly|monthly).*(?:prediction|forecast)",
    ],
    "birth_chart": [
        r"kundli", r"kundali", r"birth\s*chart", r"janam\s*patri",
        r"planetary\s*position", r"generate.*chart",
    ],
    "kundli_matching": [
        r"match.*kundli", r"kundli.*match", r"compatibility",
        r"gun\s*milan", r"matching", r"compatible",
    ],
    "dosha_check": [
        r"manglik", r"mangal\s*dosha", r"kuja\s*dosha",
        r"kaal\s*sarp", r"kaalsarp",
        r"sade\s*sati", r"sadesati", r"shani\s*sade",
        r"pitra\s*dosha", r"pitru\s*dosha",
        r"dosha\s*check", r"check.*dosha", r"am\s*i\s*manglik",
    ],
    "life_prediction": [
        r"when\s*will\s*i", r"will\s*i\s*get", r"will\s*i\s*have",
        r"marriage\s*prediction", r"career\s*prediction", r"job\s*prediction",
        r"child.*prediction", r"baby", r"conceive",
        r"foreign.*settlement", r"go\s*abroad", r"settle\s*abroad",
        r"become\s*rich", r"wealth\s*prediction", r"financial\s*future",
        r"health\s*prediction", r"my\s*future",
    ],
    "panchang": [
        r"panchang", r"panchangam", r"tithi", r"nakshatra\s*today",
        r"rahu\s*kaal", r"rahu\s*kalam", r"shubh\s*muhurat",
        r"today.*tithi", r"aaj\s*ka\s*panchang",
    ],
    "numerology": [
        r"numerology", r"lucky\s*number", r"name\s*number",
        r"life\s*path\s*number", r"destiny\s*number",
    ],
    "tarot": [
        r"tarot", r"card\s*reading", r"pick\s*a\s*card",
        r"celtic\s*cross", r"three\s*card",
    ],
}


# =============================================================================
# TRAVEL INTENT PATTERNS
# =============================================================================

TRAVEL_INTENT_PATTERNS: Dict[str, List[str]] = {
    "pnr_status": [r"pnr", r"pnr\s*status", r"check\s*pnr"],
    "train_status": [r"train", r"running\s*status", r"train\s*status", r"where\s*is\s*train"],
    "metro_ticket": [r"metro", r"metro\s*route", r"metro\s*fare"],
}


# =============================================================================
# UTILITY INTENT PATTERNS
# =============================================================================

UTILITY_INTENT_PATTERNS: Dict[str, List[str]] = {
    "weather": [r"weather", r"temperature", r"forecast", r"rain", r"humidity"],
    "news": [r"news", r"headlines", r"breaking"],
    "image": [r"generate\s*image", r"create\s*image", r"draw", r"picture"],
    "reminder": [r"remind", r"reminder", r"alarm"],
    "local_search": [r"search", r"find", r"near\s*me", r"nearby"],
    "events": [
        # IPL/Cricket
        r"ipl", r"ipl\s*match", r"cricket\s*match", r"cricket\s*ticket",
        r"rcb", r"csk", r"mi\b", r"kkr", r"dc\b", r"srh", r"rr\b", r"pbks", r"gt\b", r"lsg",
        r"royal\s*challengers", r"chennai\s*super\s*kings", r"mumbai\s*indians",
        r"kolkata\s*knight\s*riders", r"delhi\s*capitals", r"sunrisers",
        r"rajasthan\s*royals", r"punjab\s*kings", r"gujarat\s*titans", r"lucknow\s*super\s*giants",
        # Concerts
        r"concert", r"live\s*show", r"music\s*show", r"arijit", r"coldplay", r"ar\s*rahman",
        # Comedy
        r"comedy\s*show", r"standup", r"stand-up", r"comedian",
        r"zakir\s*khan", r"biswa", r"kenny\s*sebastian",
        # General events
        r"event", r"ticket", r"book\s*ticket", r"show",
        r"football", r"isl\s*match",
    ],
    "fact_check": [
        # English patterns
        r"fact\s*check", r"check\s*fact", r"is\s*this\s+true", r"is\s*this\s+real",
        r"is\s*this\s+correct", r"verify\s*this", r"true\s+or\s+false",
        r"fact\s+or\s+fiction", r"myth\s+or\s+fact", r"fake\s+or\s+real",
        r"is\s*this\s+fake", r"fake\s*news", r"real\s+news", r"verify\s*news",
        r"check\s*if.*true", r"check\s*if.*real", r"check\s*if.*fake",
        r"is\s*it\s+true", r"is\s*it\s+fake", r"is\s*it\s+real",
        # Hindi patterns
        r"sach\s*hai", r"jhooth\s*hai", r"asli\s*hai", r"nakli\s*hai",
        r"fake\s*hai", r"real\s*hai", r"verify\s*karo", r"check\s*karo",
        r"yeh\s*sach\s*hai", r"kya\s*yeh\s*sach", r"kya\s*yeh\s*real",
        # Contextual patterns
        r"can\s*you\s*verify", r"please\s*verify", r"verify\s*claim",
        r"check\s*this\s*claim", r"is\s*this\s*claim\s*true",
    ],
    "help": [
        r"what\s*can\s*you\s*do",
        r"what\s*do\s*you\s*do",
        r"help\s*me",
        r"what\s*are\s*your\s*features",
        r"what\s*services",
        r"how\s*can\s*you\s*help",
        r"what\s*can\s*i\s*ask",
        r"show\s*me\s*what\s*you\s*can\s*do",
        r"features",
    ],
    "subscription": [
        r"subscribe", r"unsubscribe", r"subscription",
        r"daily\s*horoscope", r"stop\s*horoscope", r"stop\s*alerts",
        r"transit\s*alert", r"my\s*subscription",
        r"upcoming\s*transit", r"planetary\s*transit",
    ],
}


# =============================================================================
# CONTEXT BEHAVIOR
# =============================================================================

# Strong intents that ALWAYS create new context (override existing)
STRONG_INTENTS = [
    "get_horoscope", "birth_chart", "kundli_matching",
    "weather", "get_news", "pnr_status", "train_status",
    "image", "local_search", "word_game", "tarot_reading",
    "fact_check", "events",
]

# Intents that may need context continuation
CONTEXT_AWARE_INTENTS = [
    "life_prediction", "dosha_check", "numerology",
    "get_panchang", "get_remedy", "find_muhurta",
]


