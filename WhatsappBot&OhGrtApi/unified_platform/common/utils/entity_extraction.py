"""
Entity Extraction Utilities

Centralized entity extraction functions used across the bot.
Handles extraction of:
- PNR numbers (10-digit Indian Railways)
- Train numbers (4-5 digit)
- Birth details (date, time, place)
- Zodiac signs
- Names
"""

import re
from typing import Optional, NamedTuple
from dataclasses import dataclass


@dataclass
class BirthDetails:
    """Extracted birth details."""
    date: str = ""
    time: str = ""
    place: str = ""
    name: str = ""


class ExtractionResult(NamedTuple):
    """Result of entity extraction with optional error."""
    value: Optional[str]
    raw: Optional[str] = None
    error: Optional[str] = None


# Common non-place words to exclude
EXCLUDE_PLACE_WORDS = frozenset([
    "AM", "PM", "Kundli", "Kundali", "Chart", "Horoscope", "Born",
    "Today", "Tomorrow", "Weekly", "Monthly", "Daily"
])

# Zodiac signs (English)
ZODIAC_SIGNS = frozenset([
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
])

# Hindi/Transliterated zodiac to English mapping
RASHI_TO_ENGLISH = {
    # Hindi script
    "मेष": "aries", "वृषभ": "taurus", "मिथुन": "gemini",
    "कर्क": "cancer", "सिंह": "leo", "कन्या": "virgo",
    "तुला": "libra", "वृश्चिक": "scorpio", "धनु": "sagittarius",
    "मकर": "capricorn", "कुम्भ": "aquarius", "मीन": "pisces",
    # Transliterated Hindi
    "mesh": "aries", "vrishabh": "taurus", "mithun": "gemini",
    "kark": "cancer", "singh": "leo", "simha": "leo", "kanya": "virgo",
    "tula": "libra", "vrishchik": "scorpio", "dhanu": "sagittarius",
    "makar": "capricorn", "kumbh": "aquarius", "meen": "pisces",
}


def extract_pnr(text: str) -> Optional[str]:
    """
    Extract 10-digit PNR number from text.

    Indian Railways PNR numbers are exactly 10 digits.

    Args:
        text: Input text to search

    Returns:
        10-digit PNR string if found, None otherwise

    Examples:
        >>> extract_pnr("Check PNR 1234567890")
        '1234567890'
        >>> extract_pnr("My PNR is 123456789")  # Only 9 digits
        None
    """
    if not text:
        return None
    match = re.search(r"\b(\d{10})\b", text)
    return match.group(1) if match else None


def extract_train_number(text: str) -> Optional[str]:
    """
    Extract train number (4-5 digits) from text.

    Indian Railways train numbers are typically 4-5 digits.

    Args:
        text: Input text to search

    Returns:
        Train number string if found, None otherwise

    Examples:
        >>> extract_train_number("Train 12301 status")
        '12301'
        >>> extract_train_number("Where is 22691")
        '22691'
    """
    if not text:
        return None
    match = re.search(r"\b(\d{4,5})\b", text)
    return match.group(1) if match else None


def extract_birth_date(text: str) -> ExtractionResult:
    """
    Extract birth date from text.

    Supports formats: DD-MM-YYYY, DD/MM/YYYY, DD-MM-YY, DD/MM/YY

    Args:
        text: Input text to search

    Returns:
        ExtractionResult with date string and raw match

    Examples:
        >>> extract_birth_date("born on 15-08-1990")
        ExtractionResult(value='15-08-1990', raw='15-08-1990', error=None)
    """
    if not text:
        return ExtractionResult(None)

    match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", text)
    if match:
        return ExtractionResult(value=match.group(1), raw=match.group(1))
    return ExtractionResult(None)


def extract_birth_time(text: str) -> ExtractionResult:
    """
    Extract birth time from text.

    Supports formats: HH:MM, HH.MM with optional AM/PM

    Args:
        text: Input text to search

    Returns:
        ExtractionResult with normalized time string

    Examples:
        >>> extract_birth_time("at 10:30 AM")
        ExtractionResult(value='10:30 AM', raw='10:30 AM', error=None)
    """
    if not text:
        return ExtractionResult(None)

    match = re.search(r"(?:at\s+)?(\d{1,2}[:.]\d{2})\s*(AM|PM|am|pm)?", text, re.IGNORECASE)
    if match:
        time_str = match.group(1)
        raw = time_str
        if match.group(2):
            time_str += " " + match.group(2).upper()
            raw = match.group(0).strip()
        return ExtractionResult(value=time_str, raw=raw)
    return ExtractionResult(None)


def extract_birth_place(text: str) -> ExtractionResult:
    """
    Extract birth place from text using multiple patterns.

    Patterns tried in order:
    1. After "in/at/from" preposition
    2. After AM/PM time marker
    3. Capitalized word(s) at end of string

    Args:
        text: Input text to search

    Returns:
        ExtractionResult with place name

    Examples:
        >>> extract_birth_place("born in Delhi")
        ExtractionResult(value='Delhi', raw='Delhi', error=None)
        >>> extract_birth_place("10:30 AM Mumbai")
        ExtractionResult(value='Mumbai', raw='Mumbai', error=None)
    """
    if not text:
        return ExtractionResult(None)

    place_str = ""

    # Pattern 1: "in/at/from <place>"
    place_match = re.search(
        r"(?:in|at|from)\s+([A-Za-z][A-Za-z\s]*?)(?:\s*$|\s*,|\s*\d|\s*born)",
        text, re.IGNORECASE
    )
    if place_match:
        place_str = place_match.group(1).strip()
        # Clean up common suffixes
        place_str = re.sub(r"\s+(born|at|on).*$", "", place_str, flags=re.IGNORECASE).strip()

    # Pattern 2: Place after AM/PM (e.g., "10:30 AM Delhi")
    if not place_str:
        place_after_time = re.search(
            r"(?:AM|PM|am|pm)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s*$|\s*,)",
            text
        )
        if place_after_time:
            place_str = place_after_time.group(1).strip()

    # Pattern 3: Capitalized word at end of string
    if not place_str:
        end_place = re.search(r"\s([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$", text)
        if end_place:
            potential = end_place.group(1).strip()
            if potential not in EXCLUDE_PLACE_WORDS:
                place_str = potential

    if place_str:
        return ExtractionResult(value=place_str, raw=place_str)
    return ExtractionResult(None)


def extract_birth_details(text: str) -> BirthDetails:
    """
    Extract all birth details from text.

    Combines date, time, place, and name extraction.

    Args:
        text: Input text to search

    Returns:
        BirthDetails dataclass with all extracted fields

    Examples:
        >>> details = extract_birth_details("Kundli for Rahul born 15-08-1990 10:30 AM Delhi")
        >>> details.date
        '15-08-1990'
        >>> details.place
        'Delhi'
    """
    details = BirthDetails()

    if not text:
        return details

    # Extract date
    date_result = extract_birth_date(text)
    if date_result.value:
        details.date = date_result.value

    # Extract time
    time_result = extract_birth_time(text)
    if time_result.value:
        details.time = time_result.value

    # Extract place
    place_result = extract_birth_place(text)
    if place_result.value:
        details.place = place_result.value

    # Extract name - "for <name>" or "of <name>"
    name_match = re.search(
        r"(?:for|of)\s+([A-Za-z]+)\s+(?:born|dob|\d)",
        text, re.IGNORECASE
    )
    if name_match:
        details.name = name_match.group(1).strip()

    return details


def extract_zodiac_sign(text: str) -> Optional[str]:
    """
    Extract zodiac sign from text (supports English, Hindi, and transliterated).

    Args:
        text: Input text to search

    Returns:
        Capitalized English zodiac sign if found, None otherwise

    Examples:
        >>> extract_zodiac_sign("aries horoscope today")
        'Aries'
        >>> extract_zodiac_sign("leo weekly prediction")
        'Leo'
        >>> extract_zodiac_sign("धनु राशिफल बताओ")
        'Sagittarius'
        >>> extract_zodiac_sign("mesh rashifal")
        'Aries'
    """
    if not text:
        return None

    text_lower = text.lower()

    # First check English signs
    for sign in ZODIAC_SIGNS:
        if sign in text_lower:
            return sign.capitalize()

    # Check Hindi/transliterated names
    for hindi_name, english_sign in RASHI_TO_ENGLISH.items():
        if hindi_name in text or hindi_name.lower() in text_lower:
            return english_sign.capitalize()

    return None


def extract_name(text: str, pattern: str = "default") -> Optional[str]:
    """
    Extract name from text using specified pattern.

    Args:
        text: Input text to search
        pattern: Pattern type - "default", "numerology", "birth_chart"

    Returns:
        Extracted name if found, None otherwise
    """
    if not text:
        return None

    if pattern == "numerology":
        # Pattern: "numerology for <name>" or "numerology of <name>"
        match = re.search(
            r"numerology\s+(?:for|of)\s+([A-Za-z\s]+?)(?:,|\s+born|\s+\d|$)",
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

        # Pattern: "my numerology - <name>"
        match = re.search(
            r"my\s+numerology\s*[-:]\s*([A-Za-z\s]+?)(?:,|\s+born|\s+\d|$)",
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

    elif pattern == "birth_chart":
        # Pattern: "for <name>" or "of <name>" before birth info
        match = re.search(
            r"(?:for|of)\s+([A-Za-z]+)\s+(?:born|dob|\d)",
            text, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()

    else:  # default
        # Generic capitalized name extraction
        match = re.search(r"(?:for|of|name\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        if match:
            return match.group(1).strip()

    return None
