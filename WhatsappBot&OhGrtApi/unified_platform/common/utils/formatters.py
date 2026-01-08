"""
Text Formatting Utilities.
"""

from datetime import datetime
from typing import List, Optional


def format_timestamp(
    dt: Optional[datetime] = None,
    format_str: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """
    Format a datetime object as a string.

    Args:
        dt: Datetime object (uses current time if None)
        format_str: Format string

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def format_relative_time(dt: datetime) -> str:
    """
    Format datetime as relative time (e.g., "5 minutes ago").

    Args:
        dt: Datetime object

    Returns:
        Relative time string
    """
    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%B %d, %Y")


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "...",
) -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_list(
    items: List[str],
    numbered: bool = False,
    bullet: str = "•",
) -> str:
    """
    Format a list of items as a string.

    Args:
        items: List of items
        numbered: Whether to use numbers
        bullet: Bullet character (if not numbered)

    Returns:
        Formatted list string
    """
    if not items:
        return ""

    lines = []
    for i, item in enumerate(items, 1):
        if numbered:
            lines.append(f"{i}. {item}")
        else:
            lines.append(f"{bullet} {item}")

    return "\n".join(lines)


def format_key_value(
    data: dict,
    separator: str = ": ",
    line_separator: str = "\n",
) -> str:
    """
    Format a dictionary as key-value pairs.

    Args:
        data: Dictionary to format
        separator: Key-value separator
        line_separator: Line separator

    Returns:
        Formatted string
    """
    if not data:
        return ""

    lines = []
    for key, value in data.items():
        # Convert key to title case
        key_str = str(key).replace("_", " ").title()
        lines.append(f"{key_str}{separator}{value}")

    return line_separator.join(lines)


def format_currency(
    amount: float,
    currency: str = "INR",
    locale: str = "en_IN",
) -> str:
    """
    Format amount as currency string.

    Args:
        amount: Amount to format
        currency: Currency code
        locale: Locale for formatting

    Returns:
        Formatted currency string
    """
    symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }

    symbol = symbols.get(currency, currency)

    # Format with Indian numbering for INR
    if currency == "INR" and locale == "en_IN":
        # Indian numbering: 1,00,000 format
        s = f"{amount:,.2f}"
        # Convert to Indian format
        parts = s.split(".")
        integer_part = parts[0].replace(",", "")

        if len(integer_part) > 3:
            result = integer_part[-3:]
            integer_part = integer_part[:-3]
            while integer_part:
                result = integer_part[-2:] + "," + result
                integer_part = integer_part[:-2]
            return f"{symbol}{result}.{parts[1]}"

    return f"{symbol}{amount:,.2f}"


def format_phone_number(phone: str, format_type: str = "international") -> str:
    """
    Format phone number for display.

    Args:
        phone: Phone number
        format_type: 'international' or 'national'

    Returns:
        Formatted phone number
    """
    # Remove non-digit characters
    digits = "".join(c for c in phone if c.isdigit())

    if not digits:
        return phone

    # Indian phone number formatting
    if len(digits) == 10:
        return f"+91 {digits[:5]} {digits[5:]}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+91 {digits[2:7]} {digits[7:]}"
    elif len(digits) == 13 and digits.startswith("91"):
        return f"+91 {digits[2:7]} {digits[7:]}"

    return phone
