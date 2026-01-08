"""
Input Validation Utilities.
"""

import re
from typing import Optional


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number string

    Returns:
        True if valid
    """
    if not phone:
        return False

    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)

    # Check if it's all digits
    if not cleaned.isdigit():
        return False

    # Check length (10-15 digits is typical for international numbers)
    if not (10 <= len(cleaned) <= 15):
        return False

    return True


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address string

    Returns:
        True if valid
    """
    if not email:
        return False

    # Simple email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_input(text: str, max_length: int = 4096) -> str:
    """
    Sanitize user input text.

    Args:
        text: Input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Normalize whitespace
    text = ' '.join(text.split())

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def validate_city_name(city: str) -> Optional[str]:
    """
    Validate and clean city name.

    Args:
        city: City name

    Returns:
        Cleaned city name or None if invalid
    """
    if not city:
        return None

    # Remove special characters except spaces and hyphens
    cleaned = re.sub(r'[^a-zA-Z\s\-]', '', city)

    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())

    # Check minimum length
    if len(cleaned) < 2:
        return None

    return cleaned.title()


def validate_date_string(date_str: str) -> bool:
    """
    Validate date string format (YYYY-MM-DD).

    Args:
        date_str: Date string

    Returns:
        True if valid format
    """
    if not date_str:
        return False

    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False

    # Basic range validation
    try:
        year, month, day = map(int, date_str.split('-'))
        if not (1900 <= year <= 2100):
            return False
        if not (1 <= month <= 12):
            return False
        if not (1 <= day <= 31):
            return False
        return True
    except (ValueError, AttributeError):
        return False


def is_safe_path(path: str) -> bool:
    """
    Check if a path is safe (no traversal attacks).

    Args:
        path: File path

    Returns:
        True if safe
    """
    if not path:
        return False

    # Check for path traversal patterns
    dangerous_patterns = [
        '..',
        '~',
        '\x00',
        '\\',
    ]

    for pattern in dangerous_patterns:
        if pattern in path:
            return False

    # Check if path starts with /
    if path.startswith('/'):
        return False

    return True
