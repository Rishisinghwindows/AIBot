"""
Input Validation Service

Validates and sanitizes all user inputs before processing.
Handles geocoding, date/time parsing, and input constraints.
"""

import re
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Geopy for geocoding
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, field: str = None, suggestion: str = None):
        self.message = message
        self.field = field
        self.suggestion = suggestion
        super().__init__(self.message)


class InputType(str, Enum):
    """Types of validated inputs."""
    BIRTH_DETAILS = "birth_details"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    QUESTION = "question"
    NAME = "name"


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    value: Any = None
    error: str = None
    suggestion: str = None
    input_type: InputType = None


@dataclass
class GeoLocation:
    """Validated geographic location."""
    city: str
    latitude: float
    longitude: float
    timezone: str
    country: str = None
    state: str = None


class InputValidator:
    """
    Validates and sanitizes all user inputs for astrology calculations.

    Responsibilities:
    - Date/time parsing and validation
    - Location geocoding and validation
    - Name sanitization
    - Question content validation
    - Birth details completeness checking
    """

    # Known city coordinates for fallback
    KNOWN_CITIES: Dict[str, Dict[str, Any]] = {
        "new delhi": {"lat": 28.6139, "lng": 77.2090, "tz": "Asia/Kolkata", "country": "India"},
        "delhi": {"lat": 28.6139, "lng": 77.2090, "tz": "Asia/Kolkata", "country": "India"},
        "mumbai": {"lat": 19.0760, "lng": 72.8777, "tz": "Asia/Kolkata", "country": "India"},
        "bangalore": {"lat": 12.9716, "lng": 77.5946, "tz": "Asia/Kolkata", "country": "India"},
        "bengaluru": {"lat": 12.9716, "lng": 77.5946, "tz": "Asia/Kolkata", "country": "India"},
        "chennai": {"lat": 13.0827, "lng": 80.2707, "tz": "Asia/Kolkata", "country": "India"},
        "kolkata": {"lat": 22.5726, "lng": 88.3639, "tz": "Asia/Kolkata", "country": "India"},
        "hyderabad": {"lat": 17.3850, "lng": 78.4867, "tz": "Asia/Kolkata", "country": "India"},
        "pune": {"lat": 18.5204, "lng": 73.8567, "tz": "Asia/Kolkata", "country": "India"},
        "ahmedabad": {"lat": 23.0225, "lng": 72.5714, "tz": "Asia/Kolkata", "country": "India"},
        "jaipur": {"lat": 26.9124, "lng": 75.7873, "tz": "Asia/Kolkata", "country": "India"},
        "lucknow": {"lat": 26.8467, "lng": 80.9462, "tz": "Asia/Kolkata", "country": "India"},
        "kanpur": {"lat": 26.4499, "lng": 80.3319, "tz": "Asia/Kolkata", "country": "India"},
        "nagpur": {"lat": 21.1458, "lng": 79.0882, "tz": "Asia/Kolkata", "country": "India"},
        "patna": {"lat": 25.5941, "lng": 85.1376, "tz": "Asia/Kolkata", "country": "India"},
        "indore": {"lat": 22.7196, "lng": 75.8577, "tz": "Asia/Kolkata", "country": "India"},
        "bhopal": {"lat": 23.2599, "lng": 77.4126, "tz": "Asia/Kolkata", "country": "India"},
        "surat": {"lat": 21.1702, "lng": 72.8311, "tz": "Asia/Kolkata", "country": "India"},
        "varanasi": {"lat": 25.3176, "lng": 82.9739, "tz": "Asia/Kolkata", "country": "India"},
        "agra": {"lat": 27.1767, "lng": 78.0081, "tz": "Asia/Kolkata", "country": "India"},
        "chandigarh": {"lat": 30.7333, "lng": 76.7794, "tz": "Asia/Kolkata", "country": "India"},
        "coimbatore": {"lat": 11.0168, "lng": 76.9558, "tz": "Asia/Kolkata", "country": "India"},
        "kochi": {"lat": 9.9312, "lng": 76.2673, "tz": "Asia/Kolkata", "country": "India"},
        "thiruvananthapuram": {"lat": 8.5241, "lng": 76.9366, "tz": "Asia/Kolkata", "country": "India"},
        "visakhapatnam": {"lat": 17.6868, "lng": 83.2185, "tz": "Asia/Kolkata", "country": "India"},
        "guwahati": {"lat": 26.1445, "lng": 91.7362, "tz": "Asia/Kolkata", "country": "India"},
        "bhubaneswar": {"lat": 20.2961, "lng": 85.8245, "tz": "Asia/Kolkata", "country": "India"},
        "dehradun": {"lat": 30.3165, "lng": 78.0322, "tz": "Asia/Kolkata", "country": "India"},
        "shimla": {"lat": 31.1048, "lng": 77.1734, "tz": "Asia/Kolkata", "country": "India"},
        # International cities
        "new york": {"lat": 40.7128, "lng": -74.0060, "tz": "America/New_York", "country": "USA"},
        "los angeles": {"lat": 34.0522, "lng": -118.2437, "tz": "America/Los_Angeles", "country": "USA"},
        "chicago": {"lat": 41.8781, "lng": -87.6298, "tz": "America/Chicago", "country": "USA"},
        "london": {"lat": 51.5074, "lng": -0.1278, "tz": "Europe/London", "country": "UK"},
        "dubai": {"lat": 25.2048, "lng": 55.2708, "tz": "Asia/Dubai", "country": "UAE"},
        "singapore": {"lat": 1.3521, "lng": 103.8198, "tz": "Asia/Singapore", "country": "Singapore"},
        "sydney": {"lat": -33.8688, "lng": 151.2093, "tz": "Australia/Sydney", "country": "Australia"},
        "toronto": {"lat": 43.6532, "lng": -79.3832, "tz": "America/Toronto", "country": "Canada"},
        "san francisco": {"lat": 37.7749, "lng": -122.4194, "tz": "America/Los_Angeles", "country": "USA"},
    }

    # Date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d",       # 2024-01-15
        "%d-%m-%Y",       # 15-01-2024
        "%d/%m/%Y",       # 15/01/2024
        "%m/%d/%Y",       # 01/15/2024
        "%d %B %Y",       # 15 January 2024
        "%d %b %Y",       # 15 Jan 2024
        "%B %d, %Y",      # January 15, 2024
        "%b %d, %Y",      # Jan 15, 2024
        "%Y/%m/%d",       # 2024/01/15
        "%d.%m.%Y",       # 15.01.2024
    ]

    # Time formats to try
    TIME_FORMATS = [
        "%H:%M",          # 14:30
        "%H:%M:%S",       # 14:30:00
        "%I:%M %p",       # 02:30 PM
        "%I:%M:%S %p",    # 02:30:00 PM
        "%I:%M%p",        # 02:30PM
        "%I %p",          # 2 PM
    ]

    # Blocked question patterns (safety)
    BLOCKED_PATTERNS = [
        r"\b(suicide|kill|murder|death date|when.*die)\b",
        r"\b(lottery|gambling|stock.*tip|bet.*win)\b",
        r"\b(illegal|crime|steal|fraud)\b",
    ]

    def __init__(self):
        """Initialize the validator with optional geocoder."""
        self._geocoder = None
        if GEOPY_AVAILABLE:
            try:
                self._geocoder = Nominatim(user_agent="vedic_astrologer_v1")
            except Exception:
                pass

    def validate_date(self, date_input: str) -> ValidationResult:
        """
        Parse and validate a date string.

        Args:
            date_input: Date string in various formats

        Returns:
            ValidationResult with parsed date or error
        """
        if not date_input:
            return ValidationResult(
                is_valid=False,
                error="Date is required",
                input_type=InputType.DATE
            )

        date_str = str(date_input).strip()

        # Try each format
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # Validate reasonable date range
                if parsed.year < 1900:
                    return ValidationResult(
                        is_valid=False,
                        error="Year must be 1900 or later",
                        suggestion="Please provide a date after 1900",
                        input_type=InputType.DATE
                    )
                if parsed > datetime.now():
                    return ValidationResult(
                        is_valid=False,
                        error="Birth date cannot be in the future",
                        input_type=InputType.DATE
                    )
                return ValidationResult(
                    is_valid=True,
                    value=parsed.date(),
                    input_type=InputType.DATE
                )
            except ValueError:
                continue

        return ValidationResult(
            is_valid=False,
            error=f"Could not parse date: {date_str}",
            suggestion="Try formats like YYYY-MM-DD or DD/MM/YYYY",
            input_type=InputType.DATE
        )

    def validate_time(self, time_input: str) -> ValidationResult:
        """
        Parse and validate a time string.

        Args:
            time_input: Time string in various formats

        Returns:
            ValidationResult with parsed time or error
        """
        if not time_input:
            return ValidationResult(
                is_valid=False,
                error="Time is required",
                input_type=InputType.TIME
            )

        time_str = str(time_input).strip().upper()

        # Try each format
        for fmt in self.TIME_FORMATS:
            try:
                parsed = datetime.strptime(time_str, fmt)
                return ValidationResult(
                    is_valid=True,
                    value=parsed.time(),
                    input_type=InputType.TIME
                )
            except ValueError:
                continue

        return ValidationResult(
            is_valid=False,
            error=f"Could not parse time: {time_input}",
            suggestion="Try formats like HH:MM or HH:MM AM/PM",
            input_type=InputType.TIME
        )

    def validate_location(self, location: str) -> ValidationResult:
        """
        Validate and geocode a location string.

        Args:
            location: City name or location string

        Returns:
            ValidationResult with GeoLocation or error
        """
        if not location:
            return ValidationResult(
                is_valid=False,
                error="Location is required",
                input_type=InputType.LOCATION
            )

        location_clean = str(location).strip().lower()

        # Check known cities first
        if location_clean in self.KNOWN_CITIES:
            city_data = self.KNOWN_CITIES[location_clean]
            return ValidationResult(
                is_valid=True,
                value=GeoLocation(
                    city=location.strip().title(),
                    latitude=city_data["lat"],
                    longitude=city_data["lng"],
                    timezone=city_data["tz"],
                    country=city_data.get("country")
                ),
                input_type=InputType.LOCATION
            )

        # Try geocoding if available
        if self._geocoder:
            try:
                result = self._geocoder.geocode(location, timeout=5)
                if result:
                    # Determine timezone (simplified)
                    tz = self._estimate_timezone(result.latitude, result.longitude)
                    return ValidationResult(
                        is_valid=True,
                        value=GeoLocation(
                            city=location.strip().title(),
                            latitude=result.latitude,
                            longitude=result.longitude,
                            timezone=tz
                        ),
                        input_type=InputType.LOCATION
                    )
            except (GeocoderTimedOut, GeocoderServiceError):
                pass
            except Exception:
                pass

        return ValidationResult(
            is_valid=False,
            error=f"Could not find location: {location}",
            suggestion="Try a major city name like 'New Delhi' or 'Mumbai'",
            input_type=InputType.LOCATION
        )

    def _estimate_timezone(self, lat: float, lng: float) -> str:
        """Estimate timezone from coordinates (simplified)."""
        # India
        if 68 < lng < 97 and 8 < lat < 37:
            return "Asia/Kolkata"
        # US East
        if -85 < lng < -65:
            return "America/New_York"
        # US West
        if -125 < lng < -115:
            return "America/Los_Angeles"
        # UK/Europe
        if -10 < lng < 30 and 35 < lat < 70:
            return "Europe/London"
        # Default to UTC
        return "UTC"

    def validate_name(self, name: str, min_length: int = 1, max_length: int = 100) -> ValidationResult:
        """
        Validate and sanitize a name string.

        Args:
            name: Name to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length

        Returns:
            ValidationResult with sanitized name or error
        """
        if not name:
            return ValidationResult(
                is_valid=False,
                error="Name is required",
                input_type=InputType.NAME
            )

        # Sanitize: remove extra whitespace, strip
        sanitized = " ".join(str(name).split()).strip()

        if len(sanitized) < min_length:
            return ValidationResult(
                is_valid=False,
                error=f"Name must be at least {min_length} character(s)",
                input_type=InputType.NAME
            )

        if len(sanitized) > max_length:
            return ValidationResult(
                is_valid=False,
                error=f"Name must not exceed {max_length} characters",
                input_type=InputType.NAME
            )

        # Check for invalid characters
        if re.search(r'[<>{}|\[\]\\]', sanitized):
            return ValidationResult(
                is_valid=False,
                error="Name contains invalid characters",
                input_type=InputType.NAME
            )

        return ValidationResult(
            is_valid=True,
            value=sanitized,
            input_type=InputType.NAME
        )

    def validate_question(self, question: str, max_length: int = 1000) -> ValidationResult:
        """
        Validate a user's astrology question.

        Args:
            question: Question text
            max_length: Maximum allowed length

        Returns:
            ValidationResult with sanitized question or error
        """
        if not question:
            return ValidationResult(
                is_valid=False,
                error="Question is required",
                input_type=InputType.QUESTION
            )

        sanitized = " ".join(str(question).split()).strip()

        if len(sanitized) < 5:
            return ValidationResult(
                is_valid=False,
                error="Question is too short",
                suggestion="Please provide more details about what you'd like to know",
                input_type=InputType.QUESTION
            )

        if len(sanitized) > max_length:
            return ValidationResult(
                is_valid=False,
                error=f"Question must not exceed {max_length} characters",
                input_type=InputType.QUESTION
            )

        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    error="This type of question cannot be answered",
                    suggestion="Please ask about personality, career, relationships, or general life guidance",
                    input_type=InputType.QUESTION
                )

        return ValidationResult(
            is_valid=True,
            value=sanitized,
            input_type=InputType.QUESTION
        )

    def validate_birth_details(
        self,
        name: str = None,
        date_str: str = None,
        time_str: str = None,
        location: str = None,
        require_time: bool = True
    ) -> ValidationResult:
        """
        Validate complete birth details.

        Args:
            name: Person's name
            date_str: Birth date string
            time_str: Birth time string
            location: Birth location
            require_time: Whether time is required

        Returns:
            ValidationResult with validated details dict or error
        """
        errors = []
        validated = {}

        # Validate name (optional)
        if name:
            name_result = self.validate_name(name)
            if name_result.is_valid:
                validated["name"] = name_result.value
            else:
                errors.append(f"Name: {name_result.error}")

        # Validate date (required)
        date_result = self.validate_date(date_str)
        if date_result.is_valid:
            validated["date"] = date_result.value
        else:
            errors.append(f"Date: {date_result.error}")

        # Validate time
        if time_str:
            time_result = self.validate_time(time_str)
            if time_result.is_valid:
                validated["time"] = time_result.value
            else:
                errors.append(f"Time: {time_result.error}")
        elif require_time:
            errors.append("Time: Birth time is required for accurate calculations")

        # Validate location (required)
        location_result = self.validate_location(location)
        if location_result.is_valid:
            validated["location"] = location_result.value
        else:
            errors.append(f"Location: {location_result.error}")

        if errors:
            return ValidationResult(
                is_valid=False,
                error="; ".join(errors),
                input_type=InputType.BIRTH_DETAILS
            )

        return ValidationResult(
            is_valid=True,
            value=validated,
            input_type=InputType.BIRTH_DETAILS
        )

    def validate_coordinates(
        self,
        latitude: float,
        longitude: float
    ) -> ValidationResult:
        """
        Validate geographic coordinates.

        Args:
            latitude: Latitude value
            longitude: Longitude value

        Returns:
            ValidationResult with coordinates tuple or error
        """
        try:
            lat = float(latitude)
            lng = float(longitude)
        except (TypeError, ValueError):
            return ValidationResult(
                is_valid=False,
                error="Invalid coordinate format",
                input_type=InputType.LOCATION
            )

        if not -90 <= lat <= 90:
            return ValidationResult(
                is_valid=False,
                error="Latitude must be between -90 and 90",
                input_type=InputType.LOCATION
            )

        if not -180 <= lng <= 180:
            return ValidationResult(
                is_valid=False,
                error="Longitude must be between -180 and 180",
                input_type=InputType.LOCATION
            )

        return ValidationResult(
            is_valid=True,
            value=(lat, lng),
            input_type=InputType.LOCATION
        )

    def extract_birth_details_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract birth details from natural language text.

        Args:
            text: Natural language input containing birth details

        Returns:
            Dict with extracted fields (may be partial)
        """
        extracted = {}
        text_lower = text.lower()

        # Extract date patterns
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})',
            r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted["date"] = match.group(1)
                break

        # Extract time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm)?)',
            r'(\d{1,2}\s*(?:am|pm))',
        ]
        for pattern in time_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted["time"] = match.group(1)
                break

        # Extract location (check known cities)
        for city in self.KNOWN_CITIES.keys():
            if city in text_lower:
                extracted["location"] = city.title()
                break

        # Extract name (look for "name is" or "my name is" patterns)
        name_patterns = [
            r"(?:my\s+)?name\s+is\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
            r"(?:i\s+am|i'm)\s+([a-zA-Z]+)(?:\s|,|\.)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted["name"] = match.group(1).strip()
                break

        return extracted


# Singleton instance
_validator_instance = None


def get_validator() -> InputValidator:
    """Get or create singleton validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = InputValidator()
    return _validator_instance
