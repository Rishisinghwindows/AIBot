"""
Input validation utilities for API requests.

Provides robust validation for dates, times, and other user inputs.
"""

import re
from datetime import datetime, date
from typing import Optional, Tuple

from app.i18n.constants import RASHI_TO_ENGLISH, ZODIAC_SIGNS


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_date_string(
    date_str: str,
    field_name: str = "date",
    format: str = "DD-MM-YYYY",
    min_year: int = 1900,
    max_year: int = None,
    allow_future: bool = True
) -> Tuple[int, int, int]:
    """
    Validate a date string and return (day, month, year).

    Args:
        date_str: Date string to validate
        field_name: Name of the field for error messages
        format: Expected format (DD-MM-YYYY or YYYY-MM-DD)
        min_year: Minimum allowed year
        max_year: Maximum allowed year (defaults to current year + 1)
        allow_future: Whether to allow future dates

    Returns:
        Tuple of (day, month, year) as integers

    Raises:
        ValidationError: If validation fails
    """
    if not date_str:
        raise ValidationError(f"{field_name} is required", field_name)

    date_str = date_str.strip()

    # Determine format and parse
    if format == "DD-MM-YYYY":
        pattern = r"^(\d{1,2})-(\d{1,2})-(\d{4})$"
        match = re.match(pattern, date_str)
        if not match:
            raise ValidationError(
                f"Invalid {field_name} format. Expected DD-MM-YYYY (e.g., 25-12-1990)",
                field_name
            )
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    elif format == "YYYY-MM-DD":
        pattern = r"^(\d{4})-(\d{1,2})-(\d{1,2})$"
        match = re.match(pattern, date_str)
        if not match:
            raise ValidationError(
                f"Invalid {field_name} format. Expected YYYY-MM-DD (e.g., 1990-12-25)",
                field_name
            )
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
    else:
        raise ValidationError(f"Unsupported date format: {format}", field_name)

    # Validate ranges
    if max_year is None:
        max_year = datetime.now().year + 1

    if year < min_year or year > max_year:
        raise ValidationError(
            f"Year must be between {min_year} and {max_year}",
            field_name
        )

    if month < 1 or month > 12:
        raise ValidationError(
            f"Month must be between 1 and 12",
            field_name
        )

    # Validate day based on month
    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Leap year check
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    if is_leap:
        days_in_month[2] = 29

    if day < 1 or day > days_in_month[month]:
        raise ValidationError(
            f"Invalid day {day} for month {month}",
            field_name
        )

    # Check for future dates
    if not allow_future:
        try:
            input_date = date(year, month, day)
            if input_date > date.today():
                raise ValidationError(
                    f"{field_name} cannot be in the future",
                    field_name
                )
        except ValueError as e:
            raise ValidationError(str(e), field_name)

    return day, month, year


def validate_time_string(
    time_str: str,
    field_name: str = "time",
    format: str = "HH:MM"
) -> Tuple[int, int]:
    """
    Validate a time string and return (hour, minute).

    Args:
        time_str: Time string to validate
        field_name: Name of the field for error messages
        format: Expected format (HH:MM)

    Returns:
        Tuple of (hour, minute) as integers

    Raises:
        ValidationError: If validation fails
    """
    if not time_str:
        raise ValidationError(f"{field_name} is required", field_name)

    time_str = time_str.strip()

    if format == "HH:MM":
        pattern = r"^(\d{1,2}):(\d{2})$"
        match = re.match(pattern, time_str)
        if not match:
            raise ValidationError(
                f"Invalid {field_name} format. Expected HH:MM (e.g., 14:30)",
                field_name
            )
        hour, minute = int(match.group(1)), int(match.group(2))
    else:
        raise ValidationError(f"Unsupported time format: {format}", field_name)

    if hour < 0 or hour > 23:
        raise ValidationError(
            f"Hour must be between 0 and 23",
            field_name
        )

    if minute < 0 or minute > 59:
        raise ValidationError(
            f"Minute must be between 0 and 59",
            field_name
        )

    return hour, minute


def validate_zodiac_sign(sign: str, field_name: str = "zodiac_sign") -> str:
    """
    Validate a zodiac sign (supports English and Indian languages).

    Args:
        sign: Zodiac sign to validate (English, Hindi, or transliterated)
        field_name: Name of the field for error messages

    Returns:
        Normalized zodiac sign (capitalized English name)

    Raises:
        ValidationError: If validation fails
    """
    valid_signs = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]

    if not sign:
        raise ValidationError(f"{field_name} is required", field_name)

    sign_stripped = sign.strip()
    sign_lower = sign_stripped.lower()

    # First check if it's already a valid English sign
    if sign_lower in valid_signs:
        return sign_lower.capitalize()

    # Check for Hindi/transliterated names using RASHI_TO_ENGLISH mapping
    if sign_stripped in RASHI_TO_ENGLISH:
        return RASHI_TO_ENGLISH[sign_stripped].capitalize()

    # Also check lowercase version for transliterated names
    if sign_lower in RASHI_TO_ENGLISH:
        return RASHI_TO_ENGLISH[sign_lower].capitalize()

    # Check against all zodiac signs in all languages from ZODIAC_SIGNS
    for english_sign, translations in ZODIAC_SIGNS.items():
        for lang, name in translations.items():
            if name.lower() == sign_lower or name == sign_stripped:
                return english_sign.capitalize()

    raise ValidationError(
        f"Invalid zodiac sign. Must be one of: {', '.join(s.capitalize() for s in valid_signs)}",
        field_name
    )


def validate_pnr(pnr: str, field_name: str = "PNR") -> str:
    """
    Validate an Indian Railways PNR number.

    Args:
        pnr: PNR number to validate
        field_name: Name of the field for error messages

    Returns:
        Cleaned PNR string

    Raises:
        ValidationError: If validation fails
    """
    if not pnr:
        raise ValidationError(f"{field_name} is required", field_name)

    pnr = pnr.strip().replace(" ", "").replace("-", "")

    if not pnr.isdigit():
        raise ValidationError(
            f"Invalid {field_name}. Must contain only digits.",
            field_name
        )

    if len(pnr) != 10:
        raise ValidationError(
            f"Invalid {field_name}. Must be exactly 10 digits.",
            field_name
        )

    return pnr


def validate_train_number(train_number: str, field_name: str = "train_number") -> str:
    """
    Validate an Indian Railways train number.

    Args:
        train_number: Train number to validate
        field_name: Name of the field for error messages

    Returns:
        Cleaned train number string

    Raises:
        ValidationError: If validation fails
    """
    if not train_number:
        raise ValidationError(f"{field_name} is required", field_name)

    train_number = train_number.strip()

    if not train_number.isdigit():
        raise ValidationError(
            f"Invalid {field_name}. Must contain only digits.",
            field_name
        )

    if len(train_number) not in [4, 5]:
        raise ValidationError(
            f"Invalid {field_name}. Must be 4 or 5 digits.",
            field_name
        )

    return train_number


def validate_news_category(category: str, field_name: str = "category") -> str:
    """
    Validate a news category.

    Args:
        category: Category to validate
        field_name: Name of the field for error messages

    Returns:
        Normalized category string

    Raises:
        ValidationError: If validation fails
    """
    valid_categories = [
        "general", "business", "entertainment", "health",
        "science", "sports", "technology"
    ]

    if not category:
        return None  # Category is optional

    category_lower = category.strip().lower()

    if category_lower not in valid_categories:
        raise ValidationError(
            f"Invalid category. Must be one of: {', '.join(valid_categories)}",
            field_name
        )

    return category_lower


def validate_limit(
    limit: int,
    field_name: str = "limit",
    min_value: int = 1,
    max_value: int = 100,
    default: int = 10
) -> int:
    """
    Validate a limit/count parameter.

    Args:
        limit: Limit value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        default: Default value if limit is None

    Returns:
        Validated limit value

    Raises:
        ValidationError: If validation fails
    """
    if limit is None:
        return default

    if not isinstance(limit, int):
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be an integer",
                field_name
            )

    if limit < min_value:
        raise ValidationError(
            f"{field_name} must be at least {min_value}",
            field_name
        )

    if limit > max_value:
        raise ValidationError(
            f"{field_name} cannot exceed {max_value}",
            field_name
        )

    return limit
