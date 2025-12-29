"""
WhatsApp Response Formatter

Provides utilities for formatting responses in WhatsApp-compatible format.
Reduces code duplication across node handlers.
"""

import logging
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class WhatsAppFormatter:
    """
    Formatter for WhatsApp message responses.

    Uses WhatsApp text formatting:
    - *text* for bold
    - _text_ for italic
    - ~text~ for strikethrough
    - ```text``` for monospace
    """

    @staticmethod
    def bold(text: str) -> str:
        """Format text as bold."""
        return f"*{text}*"

    @staticmethod
    def italic(text: str) -> str:
        """Format text as italic."""
        return f"_{text}_"

    @staticmethod
    def strike(text: str) -> str:
        """Format text with strikethrough."""
        return f"~{text}~"

    @staticmethod
    def mono(text: str) -> str:
        """Format text as monospace."""
        return f"```{text}```"

    @staticmethod
    def divider(char: str = "─", length: int = 30) -> str:
        """Create a visual divider line."""
        return char * length

    @staticmethod
    def header(title: str) -> str:
        """Format a section header."""
        return f"*{title}*\n"

    @staticmethod
    def subheader(title: str) -> str:
        """Format a subsection header."""
        return f"*{title}:*\n"

    @staticmethod
    def key_value(key: str, value: Any, bold_key: bool = True) -> str:
        """
        Format a key-value pair.

        Args:
            key: The label
            value: The value (will be converted to string)
            bold_key: Whether to bold the key

        Returns:
            Formatted string like "*Key:* Value"
        """
        if value is None or value == "":
            value = "N/A"
        key_str = f"*{key}:*" if bold_key else f"{key}:"
        return f"{key_str} {value}\n"

    @staticmethod
    def bullet_list(items: List[str], prefix: str = "-") -> str:
        """
        Format a bulleted list.

        Args:
            items: List of items to format
            prefix: Bullet character (default: -)

        Returns:
            Formatted bulleted list string
        """
        if not items:
            return ""
        return "\n".join([f"{prefix} {item}" for item in items]) + "\n"

    @staticmethod
    def numbered_list(items: List[str]) -> str:
        """Format a numbered list."""
        if not items:
            return ""
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)]) + "\n"

    @staticmethod
    def section(title: str, content: str) -> str:
        """
        Format a complete section with title and content.

        Args:
            title: Section title
            content: Section content

        Returns:
            Formatted section string
        """
        return f"*{title}:*\n{content}\n"

    @staticmethod
    def info_block(data: Dict[str, Any], bold_keys: bool = True) -> str:
        """
        Format a dictionary as an info block.

        Args:
            data: Dictionary of key-value pairs
            bold_keys: Whether to bold the keys

        Returns:
            Formatted info block string
        """
        lines = []
        for key, value in data.items():
            if value is not None and value != "":
                if bold_keys:
                    lines.append(f"*{key}:* {value}")
                else:
                    lines.append(f"{key}: {value}")
        return "\n".join(lines) + "\n" if lines else ""

    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if not text or len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def status_indicator(is_active: bool, active_text: str = "Active",
                        inactive_text: str = "Not Active") -> str:
        """Format a status indicator."""
        return active_text if is_active else inactive_text

    @staticmethod
    def progress_bar(value: int, max_value: int, length: int = 10) -> str:
        """
        Create a simple text progress bar.

        Args:
            value: Current value
            max_value: Maximum value
            length: Bar length in characters

        Returns:
            Progress bar string like "[████░░░░░░] 4/10"
        """
        filled = int((value / max_value) * length) if max_value > 0 else 0
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {value}/{max_value}"

    @staticmethod
    def score_display(score: int, max_score: int, label: str = "Score") -> str:
        """Format a score display."""
        return f"*{label}:* {score}/{max_score}\n"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def format_error_response(
    error_message: str,
    title: str = "Error",
    include_retry: bool = True
) -> dict:
    """
    Format a standard error response.

    Args:
        error_message: The error message to display
        title: Error title
        include_retry: Whether to include retry suggestion

    Returns:
        Response dict with response_text, response_type, should_fallback
    """
    fmt = WhatsAppFormatter()

    response = fmt.header(title)
    response += f"\n{error_message}"

    if include_retry:
        response += "\n\n_Please try again or rephrase your request._"

    return {
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
    }


def format_missing_fields_response(
    missing_fields: List[str],
    feature_name: str,
    example_query: str = None
) -> dict:
    """
    Format a response for missing required fields.

    Args:
        missing_fields: List of missing field names with examples
        feature_name: Name of the feature (e.g., "Marriage Prediction")
        example_query: Optional example query to show

    Returns:
        Response dict
    """
    fmt = WhatsAppFormatter()

    response = fmt.header(feature_name)
    response += "\nTo provide accurate results, I need:\n\n"
    response += fmt.bullet_list(missing_fields)

    if example_query:
        response += f"\n*Example:*\n{example_query}"

    return {
        "response_text": response,
        "response_type": "text",
        "should_fallback": False,
    }


def format_success_response(
    data: dict,
    tool_result: dict = None,
    response_type: str = "text"
) -> dict:
    """
    Format a standard success response.

    Args:
        data: Response data (usually contains response_text)
        tool_result: Optional tool result to include
        response_type: Response type (text, image, interactive)

    Returns:
        Response dict
    """
    return {
        "tool_result": tool_result,
        "response_text": data.get("response_text", ""),
        "response_type": response_type,
        "should_fallback": False,
    }


# =============================================================================
# SPECIALIZED FORMATTERS
# =============================================================================

class AstroResponseFormatter(WhatsAppFormatter):
    """Specialized formatter for astrology responses."""

    @staticmethod
    def person_info(person: dict) -> str:
        """Format person information block."""
        fmt = WhatsAppFormatter()
        lines = []

        if person.get("name"):
            lines.append(fmt.key_value("Name", person["name"]).strip())
        if person.get("dob") or person.get("birth_date"):
            lines.append(fmt.key_value("DOB", person.get("dob") or person.get("birth_date")).strip())
        if person.get("birth_time"):
            lines.append(fmt.key_value("Time", person["birth_time"]).strip())
        if person.get("birth_place"):
            lines.append(fmt.key_value("Place", person["birth_place"]).strip())

        return "\n".join(lines) + "\n\n" if lines else ""

    @staticmethod
    def chart_summary(chart: dict) -> str:
        """Format chart summary block."""
        fmt = WhatsAppFormatter()

        response = fmt.subheader("Chart Summary")
        response += fmt.bullet_list([
            f"Ascendant: {chart.get('ascendant', 'N/A')}",
            f"Moon Sign: {chart.get('moon_sign', 'N/A')}",
            f"Sun Sign: {chart.get('sun_sign', 'N/A')}",
            f"Nakshatra: {chart.get('moon_nakshatra', 'N/A')}",
        ])

        return response

    @staticmethod
    def dasha_info(dasha: dict) -> str:
        """Format current dasha information."""
        if not dasha or not dasha.get("mahadasha"):
            return ""

        fmt = WhatsAppFormatter()

        response = fmt.subheader("Current Dasha")
        response += fmt.bullet_list([
            f"Mahadasha: {dasha['mahadasha']}",
            f"Remaining: {dasha.get('years_remaining', 'N/A')} years",
            f"Ends: {dasha.get('end_date', 'N/A')}",
            f"Next: {dasha.get('next_dasha', 'N/A')} Mahadasha",
        ])

        return response

    @staticmethod
    def dosha_status(
        dosha_name: str,
        is_present: bool,
        severity: str = None
    ) -> str:
        """Format dosha status line."""
        if is_present:
            severity_str = f" ({severity})" if severity else ""
            return f"*{dosha_name}:* Present{severity_str}\n"
        return f"*{dosha_name}:* Not Present\n"

    @staticmethod
    def remedies_section(remedies: List[str], max_items: int = 5) -> str:
        """Format remedies section."""
        if not remedies:
            return ""

        fmt = WhatsAppFormatter()
        response = fmt.subheader("Remedies")
        response += fmt.bullet_list(remedies[:max_items])
        return response

    @staticmethod
    def advice_footer(advice: str) -> str:
        """Format advice as footer."""
        if not advice:
            return ""
        return f"\n_{advice}_"

    @staticmethod
    def disclaimer() -> str:
        """Standard astrology disclaimer."""
        return "\n_For personalized guidance, consult a qualified astrologer._"

    @staticmethod
    def house_analysis(
        house_num: int,
        house_name: str,
        analysis: dict
    ) -> str:
        """Format house analysis block."""
        fmt = WhatsAppFormatter()

        response = fmt.key_value(
            f"{house_num}th House ({house_name})",
            analysis.get("house_sign", "N/A")
        )

        lord = analysis.get("house_lord", "")
        lord_pos = analysis.get("house_lord_position", {})
        if lord:
            response += fmt.key_value(
                f"{house_num}th Lord",
                f"{lord} in house {lord_pos.get('house', 'N/A')}"
            )

        return response

    @staticmethod
    def planet_position(planet_name: str, position: dict) -> str:
        """Format planet position block."""
        fmt = WhatsAppFormatter()

        response = fmt.key_value(
            f"{planet_name} Position",
            f"{position.get('sign', 'N/A')} (House {position.get('house', 'N/A')})"
        )

        if position.get("dignity"):
            response += fmt.key_value(f"{planet_name} Dignity", position["dignity"])

        return response

    @staticmethod
    def factors_count(factors: dict, total: int, label: str = "Positive Factors") -> str:
        """Format factors count."""
        positive = sum(1 for v in factors.values() if v)
        return f"*{label}:* {positive}/{total}\n\n"


# =============================================================================
# RESPONSE TEMPLATES
# =============================================================================

def build_astro_response(
    title: str,
    person: dict = None,
    chart_summary: dict = None,
    current_dasha: dict = None,
    main_content: str = "",
    remedies: List[str] = None,
    advice: str = None,
    include_disclaimer: bool = True
) -> str:
    """
    Build a complete astrology response.

    Args:
        title: Response title
        person: Person info dict
        chart_summary: Chart summary dict
        current_dasha: Current dasha dict
        main_content: Main response content
        remedies: List of remedies
        advice: Advice text
        include_disclaimer: Whether to include standard disclaimer

    Returns:
        Formatted response string
    """
    fmt = AstroResponseFormatter()

    response = fmt.header(title) + "\n"

    if person:
        response += fmt.person_info(person)

    if chart_summary:
        response += fmt.chart_summary(chart_summary)

    if current_dasha:
        response += fmt.dasha_info(current_dasha)

    if main_content:
        response += fmt.divider() + "\n"
        response += main_content

    if remedies:
        response += fmt.remedies_section(remedies)

    if advice:
        response += fmt.advice_footer(advice)

    if include_disclaimer:
        response += fmt.disclaimer()

    return response


# =============================================================================
# ERROR HANDLING UTILITIES
# =============================================================================

def sanitize_error(error: str, context: str = "") -> str:
    """
    Convert technical errors to user-friendly messages.

    Args:
        error: Raw error message (may contain technical details)
        context: Optional context (e.g., "weather", "prediction")

    Returns:
        User-friendly error message
    """
    if not error:
        return "Something went wrong. Please try again."

    error_lower = error.lower()

    # Connection/Network errors
    if any(term in error_lower for term in ["timeout", "timed out", "connection"]):
        return "The service is taking too long to respond. Please try again in a moment."

    if any(term in error_lower for term in ["network", "unreachable", "refused"]):
        return "Unable to connect to the service. Please check your connection and try again."

    # API/Service errors
    if any(term in error_lower for term in ["api", "rate limit", "quota"]):
        return "The service is temporarily busy. Please try again in a few minutes."

    if any(term in error_lower for term in ["unauthorized", "forbidden", "401", "403"]):
        return "Service access issue. Please try again later."

    if any(term in error_lower for term in ["not found", "404"]):
        return f"Could not find the requested {context or 'information'}. Please check your input."

    if any(term in error_lower for term in ["server error", "500", "502", "503"]):
        return "The service is experiencing issues. Please try again later."

    # Input validation errors
    if any(term in error_lower for term in ["invalid", "validation", "format"]):
        return "Please check your input format and try again."

    if any(term in error_lower for term in ["missing", "required"]):
        return "Some required information is missing. Please provide complete details."

    # Parsing errors
    if any(term in error_lower for term in ["parse", "json", "decode"]):
        return "There was an issue processing the response. Please try again."

    # Location errors
    if any(term in error_lower for term in ["location", "geocod", "coordinates"]):
        return "Could not find that location. Please check the spelling and try again."

    # Default - don't expose raw error
    logger.warning(f"Unhandled error type: {error}")
    return "Something went wrong. Please try again."


def format_error_with_suggestions(
    error_type: str,
    context: str = "",
    suggestions: List[str] = None,
    example: str = None
) -> str:
    """
    Format error message with helpful suggestions.

    Args:
        error_type: Type of error (missing_input, service_error, invalid_input, etc.)
        context: Feature context (e.g., "weather", "PNR status")
        suggestions: List of suggestions for the user
        example: Example of correct usage

    Returns:
        Formatted error message with suggestions
    """
    fmt = WhatsAppFormatter()

    # Error type to message mapping
    error_messages = {
        "missing_input": f"I need more information to help with {context or 'your request'}.",
        "invalid_input": f"The input doesn't look right for {context or 'this request'}.",
        "service_error": f"I'm having trouble getting {context or 'the information'} right now.",
        "not_found": f"I couldn't find {context or 'what you were looking for'}.",
        "rate_limit": "You're sending requests too quickly. Please wait a moment.",
        "general": "Something went wrong with your request.",
    }

    response = fmt.header("Oops!")
    response += f"\n{error_messages.get(error_type, error_messages['general'])}\n"

    if suggestions:
        response += "\n*What you can try:*\n"
        response += fmt.bullet_list(suggestions)

    if example:
        response += f"\n*Example:*\n{example}"

    return response


def create_error_response(
    error_msg: str,
    intent: str,
    context: str = "",
    suggestions: List[str] = None,
    example: str = None,
    should_fallback: bool = False,
    raw_error: str = None
) -> dict:
    """
    Create a standardized error response dict.

    Args:
        error_msg: User-friendly error message
        intent: The intent being handled
        context: Feature context for error sanitization
        suggestions: List of helpful suggestions
        example: Example of correct usage
        should_fallback: Whether to trigger fallback node
        raw_error: Raw error for logging (not shown to user)

    Returns:
        Standardized response dict
    """
    fmt = WhatsAppFormatter()

    response_text = fmt.header("Oops!") + f"\n{error_msg}\n"

    if suggestions:
        response_text += "\n*What you can try:*\n"
        response_text += fmt.bullet_list(suggestions)

    if example:
        response_text += f"\n*Example:*\n{example}"

    result = {
        "response_text": response_text,
        "response_type": "text",
        "should_fallback": should_fallback,
        "intent": intent,
    }

    if raw_error:
        result["error"] = raw_error
        logger.error(f"Error in {intent}: {raw_error}")

    return result


def create_missing_input_response(
    missing_fields: List[str],
    intent: str,
    feature_name: str,
    example: str = None
) -> dict:
    """
    Create a standardized response for missing required input.

    Args:
        missing_fields: List of missing fields with descriptions
        intent: The intent being handled
        feature_name: Name of the feature (e.g., "Marriage Prediction")
        example: Example of correct usage

    Returns:
        Standardized response dict
    """
    fmt = WhatsAppFormatter()

    response_text = fmt.header(feature_name)
    response_text += "\nTo help you with this, I need:\n\n"
    response_text += fmt.bullet_list(missing_fields)

    if example:
        response_text += f"\n*Example:*\n{example}"

    return {
        "response_text": response_text,
        "response_type": "text",
        "should_fallback": False,
        "intent": intent,
    }


def create_service_error_response(
    intent: str,
    feature_name: str,
    raw_error: str = None,
    retry_suggestion: bool = True
) -> dict:
    """
    Create a standardized response for service/API errors.

    Args:
        intent: The intent being handled
        feature_name: Name of the feature
        raw_error: Raw error for logging
        retry_suggestion: Whether to include retry suggestion

    Returns:
        Standardized response dict
    """
    fmt = WhatsAppFormatter()

    # Sanitize the error for user display
    user_message = sanitize_error(raw_error or "", feature_name)

    response_text = fmt.header(feature_name)
    response_text += f"\n{user_message}\n"

    if retry_suggestion:
        response_text += "\n_Please try again in a moment._"

    result = {
        "response_text": response_text,
        "response_type": "text",
        "should_fallback": True,
        "intent": intent,
    }

    if raw_error:
        result["error"] = raw_error
        logger.error(f"Service error in {intent}: {raw_error}")

    return result


def create_success_response_with_data(
    response_text: str,
    intent: str,
    tool_result: dict = None,
    response_type: str = "text",
    media_url: str = None
) -> dict:
    """
    Create a standardized success response.

    Args:
        response_text: The response message
        intent: The intent being handled
        tool_result: Optional tool result data
        response_type: Response type (text, image, interactive)
        media_url: Optional media URL for images

    Returns:
        Standardized response dict
    """
    result = {
        "response_text": response_text,
        "response_type": response_type,
        "should_fallback": False,
        "intent": intent,
    }

    if tool_result:
        result["tool_result"] = tool_result

    if media_url:
        result["response_media_url"] = media_url

    return result
