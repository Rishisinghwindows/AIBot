"""
Panchang Tool

LangGraph tool for calculating daily Vedic calendar (Panchang).
All calculations are deterministic using Swiss Ephemeris.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field, field_validator
import logging

from common.astro.services.chart_engine import ChartEngine
from common.astro.services.knowledge_layer import KnowledgeLayer
from common.astro.services.validation import InputValidator

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Tithi characteristics
TITHI_NATURE = {
    "Pratipada": {"nature": "Starting", "suitable_for": ["New beginnings", "Travel"]},
    "Dvitiya": {"nature": "Auspicious", "suitable_for": ["Marriage", "Festivals"]},
    "Tritiya": {"nature": "Auspicious", "suitable_for": ["Cutting hair/nails", "Travel"]},
    "Chaturthi": {"nature": "Rikta (Void)", "suitable_for": ["Destructive activities", "Fasting"]},
    "Panchami": {"nature": "Auspicious", "suitable_for": ["Education", "Medicine"]},
    "Shasthi": {"nature": "Auspicious", "suitable_for": ["Friendship", "Recreation"]},
    "Saptami": {"nature": "Auspicious", "suitable_for": ["Travel", "Vehicle purchase"]},
    "Ashtami": {"nature": "Half Rikta", "suitable_for": ["Fasting", "Spiritual practice"]},
    "Navami": {"nature": "Rikta (Void)", "suitable_for": ["Destructive activities"]},
    "Dashami": {"nature": "Auspicious", "suitable_for": ["Government work", "Travel"]},
    "Ekadashi": {"nature": "Auspicious", "suitable_for": ["Fasting", "Worship", "Vows"]},
    "Dwadashi": {"nature": "Auspicious", "suitable_for": ["Ceremonies", "Festivals"]},
    "Trayodashi": {"nature": "Auspicious", "suitable_for": ["Friendship", "Travel"]},
    "Chaturdashi": {"nature": "Rikta (Void)", "suitable_for": ["Poison/medicine work"]},
    "Purnima": {"nature": "Full Moon", "suitable_for": ["All auspicious activities"]},
    "Amavasya": {"nature": "New Moon", "suitable_for": ["Ancestor worship", "Tantra"]}
}

# Yoga (of Panchang, not planetary yogas) characteristics
YOGA_NATURE = {
    "Vishkumbha": "Inauspicious", "Preeti": "Auspicious", "Ayushman": "Auspicious",
    "Saubhagya": "Auspicious", "Shobhana": "Auspicious", "Atiganda": "Inauspicious",
    "Sukarma": "Auspicious", "Dhriti": "Auspicious", "Shula": "Inauspicious",
    "Ganda": "Inauspicious", "Vriddhi": "Auspicious", "Dhruva": "Auspicious",
    "Vyaghata": "Inauspicious", "Harshana": "Auspicious", "Vajra": "Inauspicious",
    "Siddhi": "Auspicious", "Vyatipata": "Inauspicious", "Variyan": "Auspicious",
    "Parigha": "Inauspicious", "Shiva": "Auspicious", "Siddha": "Auspicious",
    "Sadhya": "Auspicious", "Shubha": "Auspicious", "Shukla": "Auspicious",
    "Brahma": "Auspicious", "Indra": "Auspicious", "Vaidhriti": "Inauspicious"
}

# Day lord
DAY_LORDS = {
    0: ("Sunday", "Sun", "Surya"),
    1: ("Monday", "Moon", "Chandra"),
    2: ("Tuesday", "Mars", "Mangal"),
    3: ("Wednesday", "Mercury", "Budh"),
    4: ("Thursday", "Jupiter", "Guru"),
    5: ("Friday", "Venus", "Shukra"),
    6: ("Saturday", "Saturn", "Shani")
}


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class PanchangInput(BaseModel):
    """Input schema for Panchang calculation."""

    date: Optional[str] = Field(
        default=None,
        description="Date for Panchang (YYYY-MM-DD). Defaults to today."
    )
    location: str = Field(
        default="Delhi",
        description="Location for sunrise/sunset calculations"
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date if provided."""
        if v:
            return v.strip()
        return v


class SunriseSunsetInfo(BaseModel):
    """Sunrise and sunset times."""
    sunrise: str
    sunset: str
    day_duration: str


class TithiInfo(BaseModel):
    """Tithi (lunar day) information."""
    name: str
    number: int
    paksha: str  # Shukla/Krishna
    nature: str
    suitable_for: List[str]
    end_time: Optional[str] = None


class NakshatraInfo(BaseModel):
    """Nakshatra information."""
    name: str
    pada: int
    lord: str
    deity: Optional[str] = None
    end_time: Optional[str] = None


class YogaInfo(BaseModel):
    """Yoga (of Panchang) information."""
    name: str
    nature: str
    end_time: Optional[str] = None


class KaranInfo(BaseModel):
    """Karan (half-tithi) information."""
    name: str
    nature: str


class RahuKaalInfo(BaseModel):
    """Rahu Kaal timing."""
    start: str
    end: str
    duration: str
    avoid: str


class PanchangOutput(BaseModel):
    """Output schema for Panchang."""

    success: bool = Field(..., description="Whether calculation was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    # Date information
    date: Optional[str] = None
    day: Optional[str] = None
    day_lord: Optional[str] = None
    day_lord_hindi: Optional[str] = None

    # Location
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Sun & Moon
    sunrise_sunset: Optional[SunriseSunsetInfo] = None
    moon_sign: Optional[str] = None
    sun_sign: Optional[str] = None

    # Five elements of Panchang
    tithi: Optional[TithiInfo] = None
    nakshatra: Optional[NakshatraInfo] = None
    yoga: Optional[YogaInfo] = None
    karan: Optional[KaranInfo] = None
    paksha: Optional[str] = None

    # Additional timings
    rahu_kaal: Optional[RahuKaalInfo] = None
    gulika_kaal: Optional[str] = None
    yamaganda: Optional[str] = None
    abhijit_muhurta: Optional[str] = None

    # Auspiciousness
    overall_auspiciousness: Optional[str] = None
    good_for: Optional[List[str]] = None
    avoid: Optional[List[str]] = None

    # Hindu calendar
    hindu_month: Optional[str] = None
    samvat: Optional[str] = None

    # Metadata
    calculation_method: str = "Swiss Ephemeris (Lahiri Ayanamsa)"


# =============================================================================
# TOOL IMPLEMENTATION
# =============================================================================

async def get_panchang(
    input_data: PanchangInput
) -> PanchangOutput:
    """
    Calculate Panchang (Vedic daily calendar) for a given date.

    The five elements (Pancha Anga):
    1. Tithi - Lunar day (30 per month)
    2. Nakshatra - Moon's constellation (27 total)
    3. Yoga - Sun-Moon angular relationship (27 total)
    4. Karan - Half of Tithi (11 total)
    5. Var - Day of week (7 total)

    Args:
        input_data: Validated Panchang input

    Returns:
        PanchangOutput with all Panchang elements
    """
    try:
        # Initialize services
        validator = InputValidator()
        chart_engine = ChartEngine()

        # Determine date
        if input_data.date:
            date_result = validator.validate_date(input_data.date)
            if not date_result.is_valid:
                return PanchangOutput(
                    success=False,
                    error=date_result.error
                )
            target_date = date_result.value
        else:
            target_date = date.today()

        # Validate location
        location_result = validator.validate_location(input_data.location)
        if not location_result.is_valid:
            # Fall back to Delhi
            latitude, longitude = 28.6139, 77.2090
            timezone = "Asia/Kolkata"
            location_name = "Delhi"
        else:
            location = location_result.value
            latitude = location.latitude
            longitude = location.longitude
            timezone = location.timezone
            location_name = location.city

        # Calculate Panchang (deterministic)
        panchang_data = chart_engine.calculate_panchang(
            date=target_date,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone
        )

        # Get day information
        day_index = target_date.weekday()
        # Adjust for Indian week starting
        day_name, day_lord, day_lord_hindi = DAY_LORDS.get(
            (day_index + 1) % 7,  # Python: Monday=0, we need Sunday=0
            ("Unknown", "Unknown", "Unknown")
        )
        # Correct the mapping
        day_name, day_lord, day_lord_hindi = DAY_LORDS.get(
            target_date.isoweekday() % 7,  # Sunday=0
            ("Unknown", "Unknown", "Unknown")
        )

        # Get Tithi details
        tithi_name = panchang_data.get("tithi", {}).get("name", "Unknown")
        tithi_info = TITHI_NATURE.get(tithi_name, {"nature": "Unknown", "suitable_for": []})

        # Get Yoga nature
        yoga_name = panchang_data.get("yoga", "Unknown")
        yoga_nature = YOGA_NATURE.get(yoga_name, "Unknown")

        # Calculate Rahu Kaal
        rahu_kaal = _calculate_rahu_kaal(target_date, panchang_data.get("sunrise"), panchang_data.get("sunset"))

        # Determine overall auspiciousness
        auspiciousness, good_for, avoid = _determine_auspiciousness(
            tithi_name, yoga_name, panchang_data.get("nakshatra", {}).get("name")
        )

        # Build output
        output = PanchangOutput(
            success=True,
            date=target_date.strftime("%Y-%m-%d"),
            day=target_date.strftime("%A"),
            day_lord=day_lord,
            day_lord_hindi=day_lord_hindi,
            location=location_name,
            latitude=latitude,
            longitude=longitude,
            sunrise_sunset=SunriseSunsetInfo(
                sunrise=panchang_data.get("sunrise", "6:00 AM"),
                sunset=panchang_data.get("sunset", "6:00 PM"),
                day_duration=panchang_data.get("day_duration", "12:00")
            ),
            moon_sign=panchang_data.get("moon_sign"),
            sun_sign=panchang_data.get("sun_sign"),
            tithi=TithiInfo(
                name=tithi_name,
                number=panchang_data.get("tithi", {}).get("number", 1),
                paksha=panchang_data.get("tithi", {}).get("paksha", "Shukla"),
                nature=tithi_info["nature"],
                suitable_for=tithi_info["suitable_for"]
            ),
            nakshatra=NakshatraInfo(
                name=panchang_data.get("nakshatra", {}).get("name", "Unknown"),
                pada=panchang_data.get("nakshatra", {}).get("pada", 1),
                lord=_get_nakshatra_lord(panchang_data.get("nakshatra", {}).get("name"))
            ),
            yoga=YogaInfo(
                name=yoga_name,
                nature=yoga_nature
            ),
            karan=KaranInfo(
                name=panchang_data.get("karan", ["Unknown"])[0] if panchang_data.get("karan") else "Unknown",
                nature="Movable" if panchang_data.get("karan", [""])[0] not in ["Shakuni", "Chatushpada", "Naga", "Kimstughna"] else "Fixed"
            ),
            paksha=panchang_data.get("tithi", {}).get("paksha", "Shukla"),
            rahu_kaal=rahu_kaal,
            overall_auspiciousness=auspiciousness,
            good_for=good_for,
            avoid=avoid
        )

        return output

    except Exception as e:
        logger.error(f"Panchang calculation failed: {e}")
        return PanchangOutput(
            success=False,
            error=f"Calculation failed: {str(e)}"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_nakshatra_lord(nakshatra: str) -> str:
    """Get ruling planet of a nakshatra."""
    lords = {
        "Ashwini": "Ketu", "Bharani": "Venus", "Krittika": "Sun",
        "Rohini": "Moon", "Mrigashira": "Mars", "Ardra": "Rahu",
        "Punarvasu": "Jupiter", "Pushya": "Saturn", "Ashlesha": "Mercury",
        "Magha": "Ketu", "Purva Phalguni": "Venus", "Uttara Phalguni": "Sun",
        "Hasta": "Moon", "Chitra": "Mars", "Swati": "Rahu",
        "Vishakha": "Jupiter", "Anuradha": "Saturn", "Jyeshtha": "Mercury",
        "Mula": "Ketu", "Purva Ashadha": "Venus", "Uttara Ashadha": "Sun",
        "Shravana": "Moon", "Dhanishta": "Mars", "Shatabhisha": "Rahu",
        "Purva Bhadrapada": "Jupiter", "Uttara Bhadrapada": "Saturn", "Revati": "Mercury"
    }
    return lords.get(nakshatra, "Unknown")


def _calculate_rahu_kaal(target_date: date, sunrise: str, sunset: str) -> RahuKaalInfo:
    """Calculate Rahu Kaal timing."""
    # Rahu Kaal order by day (Sun=0 to Sat=6): 8,2,7,5,6,4,3 (segment number)
    rahu_segments = {
        0: 8,  # Sunday
        1: 2,  # Monday
        2: 7,  # Tuesday
        3: 5,  # Wednesday
        4: 6,  # Thursday
        5: 4,  # Friday
        6: 3   # Saturday
    }

    # Get day
    day_index = target_date.isoweekday() % 7

    # Calculate segment (day divided into 8 parts)
    segment = rahu_segments.get(day_index, 1)

    # Approximate times (each segment ~1.5 hours for 12-hour day)
    base_hour = 6  # Assuming 6 AM sunrise
    segment_duration = 1.5  # hours

    start_hour = base_hour + (segment - 1) * segment_duration
    end_hour = start_hour + segment_duration

    start_time = f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}"
    end_time = f"{int(end_hour)}:{int((end_hour % 1) * 60):02d}"

    # Convert to 12-hour format
    def to_12hr(hour_str):
        parts = hour_str.split(":")
        h = int(parts[0])
        m = parts[1] if len(parts) > 1 else "00"
        suffix = "AM" if h < 12 else "PM"
        h = h if h <= 12 else h - 12
        h = 12 if h == 0 else h
        return f"{h}:{m} {suffix}"

    return RahuKaalInfo(
        start=to_12hr(start_time),
        end=to_12hr(end_time),
        duration="1 hour 30 minutes",
        avoid="Starting new ventures, important decisions, travel"
    )


def _determine_auspiciousness(tithi: str, yoga: str, nakshatra: str) -> tuple:
    """Determine overall day auspiciousness."""
    score = 0
    good_for = []
    avoid = []

    # Tithi scoring
    tithi_info = TITHI_NATURE.get(tithi, {})
    if tithi_info.get("nature") == "Auspicious":
        score += 2
        good_for.extend(tithi_info.get("suitable_for", []))
    elif "Rikta" in tithi_info.get("nature", ""):
        score -= 1
        avoid.append(f"{tithi} is Rikta - avoid major undertakings")

    # Yoga scoring
    yoga_nature = YOGA_NATURE.get(yoga, "Unknown")
    if yoga_nature == "Auspicious":
        score += 1
    elif yoga_nature == "Inauspicious":
        score -= 1
        avoid.append(f"{yoga} Yoga is inauspicious")

    # Determine overall
    if score >= 2:
        auspiciousness = "Highly Auspicious"
    elif score >= 1:
        auspiciousness = "Auspicious"
    elif score >= 0:
        auspiciousness = "Moderately Auspicious"
    else:
        auspiciousness = "Exercise Caution"

    # Add default recommendations if lists are empty
    if not good_for:
        good_for = ["Routine activities", "Spiritual practice"]
    if not avoid:
        avoid = ["No major concerns"]

    return auspiciousness, good_for[:5], avoid[:3]


# =============================================================================
# LANGCHAIN TOOL WRAPPER
# =============================================================================

def get_panchang_tool():
    """Create a LangChain-compatible tool for Panchang calculation."""
    from langchain_core.tools import StructuredTool

    async def _run_panchang(
        date: str = None,
        location: str = "Delhi"
    ) -> Dict[str, Any]:
        """Get Panchang (Vedic daily calendar) for a date."""
        input_data = PanchangInput(
            date=date,
            location=location
        )
        result = await get_panchang(input_data)
        return result.model_dump()

    return StructuredTool.from_function(
        coroutine=_run_panchang,
        name="get_panchang",
        description="""Get Panchang (Vedic daily calendar) for any date.

Returns the five elements of Panchang:
1. Tithi - Lunar day (phase of Moon)
2. Nakshatra - Moon's constellation
3. Yoga - Sun-Moon combination
4. Karan - Half of Tithi
5. Var - Day of week

Also includes:
- Sunrise/Sunset times
- Rahu Kaal timing (inauspicious period)
- Auspiciousness rating
- Activities to favor or avoid

Default date: Today
Default location: Delhi"""
    )
