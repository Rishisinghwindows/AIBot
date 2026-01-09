"""
Birth Details Validator

Validates birth date, time, and place for astrology calculations.
"""

import re
from datetime import datetime
from typing import Optional, Tuple, List, NamedTuple


class ValidationResult(NamedTuple):
    """Result of validation."""
    is_valid: bool
    value: Optional[str]  # Normalized value if valid
    error: Optional[str]  # Error message if invalid


# Common date formats
DATE_FORMATS = [
    "%d-%m-%Y",     # 15-08-1990
    "%d/%m/%Y",     # 15/08/1990
    "%d-%m-%y",     # 15-08-90
    "%d/%m/%y",     # 15/08/90
    "%Y-%m-%d",     # 1990-08-15 (ISO)
    "%d %b %Y",     # 15 Aug 1990
    "%d %B %Y",     # 15 August 1990
]

# Time patterns
TIME_PATTERN = re.compile(
    r'^(\d{1,2})[:.](\d{2})\s*(AM|PM|am|pm)?$'
)


def validate_birth_date(date_str: str) -> ValidationResult:
    """
    Validate and normalize birth date string.

    Args:
        date_str: Date string in various formats

    Returns:
        ValidationResult with normalized DD-MM-YYYY format if valid
    """
    if not date_str or not date_str.strip():
        return ValidationResult(False, None, "Birth date is required")

    date_str = date_str.strip()

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(date_str, fmt)

            # Validate year range (reasonable birth years)
            current_year = datetime.now().year
            if dt.year < 1900:
                return ValidationResult(False, None, "Birth year must be 1900 or later")
            if dt.year > current_year:
                return ValidationResult(False, None, "Birth year cannot be in the future")

            # Validate age (not born in future)
            if dt > datetime.now():
                return ValidationResult(False, None, "Birth date cannot be in the future")

            # Normalize to DD-MM-YYYY
            normalized = dt.strftime("%d-%m-%Y")
            return ValidationResult(True, normalized, None)

        except ValueError:
            continue

    return ValidationResult(
        False,
        None,
        f"Invalid date format. Please use DD-MM-YYYY (e.g., 15-08-1990)"
    )


def validate_birth_time(time_str: str) -> ValidationResult:
    """
    Validate and normalize birth time string.

    Args:
        time_str: Time string (e.g., "10:30 AM", "14:30", "10.30 pm")

    Returns:
        ValidationResult with normalized HH:MM AM/PM format if valid
    """
    if not time_str or not time_str.strip():
        return ValidationResult(False, None, "Birth time is required")

    time_str = time_str.strip()

    match = TIME_PATTERN.match(time_str)
    if not match:
        return ValidationResult(
            False,
            None,
            "Invalid time format. Please use HH:MM AM/PM (e.g., 10:30 AM)"
        )

    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3)

    # Validate ranges
    if minute < 0 or minute > 59:
        return ValidationResult(False, None, "Minutes must be between 0 and 59")

    # Handle 24-hour format
    if period is None:
        if hour < 0 or hour > 23:
            return ValidationResult(False, None, "Hour must be between 0 and 23")
        # Convert to 12-hour format
        if hour == 0:
            period = "AM"
            hour = 12
        elif hour < 12:
            period = "AM"
        elif hour == 12:
            period = "PM"
        else:
            period = "PM"
            hour = hour - 12
    else:
        period = period.upper()
        if hour < 1 or hour > 12:
            return ValidationResult(False, None, "Hour must be between 1 and 12 for AM/PM format")

    normalized = f"{hour:02d}:{minute:02d} {period}"
    return ValidationResult(True, normalized, None)


def validate_birth_place(place_str: str) -> ValidationResult:
    """
    Validate birth place string.

    Args:
        place_str: Place/city name

    Returns:
        ValidationResult with trimmed place name if valid
    """
    if not place_str or not place_str.strip():
        return ValidationResult(False, None, "Birth place is required")

    place = place_str.strip()

    # Basic length check
    if len(place) < 2:
        return ValidationResult(False, None, "Birth place must be at least 2 characters")

    if len(place) > 100:
        return ValidationResult(False, None, "Birth place is too long")

    # Check for only valid characters (letters, spaces, common punctuation)
    if not re.match(r'^[a-zA-Z\s\-\',\.]+$', place):
        return ValidationResult(
            False,
            None,
            "Birth place should contain only letters and common punctuation"
        )

    return ValidationResult(True, place, None)


def validate_birth_details(
    birth_date: str,
    birth_time: str,
    birth_place: str
) -> Tuple[bool, dict, List[str]]:
    """
    Validate all birth details at once.

    Args:
        birth_date: Date of birth
        birth_time: Time of birth
        birth_place: Place of birth

    Returns:
        Tuple of (is_valid, normalized_values, errors)
    """
    errors = []
    normalized = {}

    # Validate date
    date_result = validate_birth_date(birth_date)
    if date_result.is_valid:
        normalized["birth_date"] = date_result.value
    else:
        errors.append(date_result.error)

    # Validate time
    time_result = validate_birth_time(birth_time)
    if time_result.is_valid:
        normalized["birth_time"] = time_result.value
    else:
        errors.append(time_result.error)

    # Validate place
    place_result = validate_birth_place(birth_place)
    if place_result.is_valid:
        normalized["birth_place"] = place_result.value
    else:
        errors.append(place_result.error)

    return len(errors) == 0, normalized, errors


def parse_birth_date(date_str: str) -> Optional[datetime]:
    """
    Parse birth date string to datetime object.

    Args:
        date_str: Date string in various formats

    Returns:
        datetime object if valid, None otherwise
    """
    result = validate_birth_date(date_str)
    if not result.is_valid:
        return None

    return datetime.strptime(result.value, "%d-%m-%Y")


def parse_birth_time(time_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse birth time string to (hour, minute) tuple in 24-hour format.

    Args:
        time_str: Time string

    Returns:
        (hour, minute) tuple in 24-hour format if valid, None otherwise
    """
    result = validate_birth_time(time_str)
    if not result.is_valid:
        return None

    # Parse normalized format "HH:MM AM/PM"
    match = re.match(r'(\d{2}):(\d{2}) (AM|PM)', result.value)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3)

    # Convert to 24-hour
    if period == "AM":
        if hour == 12:
            hour = 0
    else:  # PM
        if hour != 12:
            hour += 12

    return (hour, minute)


def get_missing_birth_fields(entities: dict) -> List[str]:
    """
    Get list of missing birth detail fields.

    Args:
        entities: Extracted entities dictionary

    Returns:
        List of missing field names with examples
    """
    missing = []

    if not entities.get("birth_date", "").strip():
        missing.append("birth date (e.g., 15-08-1990)")

    if not entities.get("birth_time", "").strip():
        missing.append("birth time (e.g., 10:30 AM)")

    if not entities.get("birth_place", "").strip():
        missing.append("birth place (e.g., Delhi)")

    return missing


def format_missing_fields_message(missing_fields: List[str]) -> str:
    """
    Format a user-friendly message for missing fields.

    Args:
        missing_fields: List of missing field names

    Returns:
        Formatted message string
    """
    if not missing_fields:
        return ""

    if len(missing_fields) == 1:
        return f"Please provide your {missing_fields[0]}."

    fields_str = ", ".join(missing_fields[:-1]) + f" and {missing_fields[-1]}"
    return f"Please provide your {fields_str}."
