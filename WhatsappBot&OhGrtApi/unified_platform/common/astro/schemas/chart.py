"""
Chart Data Schemas

Immutable data structures for chart computation output.
All data is computed deterministically and cannot be modified.
"""

from typing import Optional, Dict, List, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from enum import Enum


class AyanamsaType(str, Enum):
    """Supported ayanamsa types."""
    LAHIRI = "lahiri"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"


class HouseSystem(str, Enum):
    """Supported house systems."""
    WHOLE_SIGN = "whole_sign"
    PLACIDUS = "placidus"
    EQUAL = "equal"


class Planet(str, Enum):
    """Vedic planets (Grahas)."""
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"


class ZodiacSign(str, Enum):
    """12 zodiac signs (Rashis)."""
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


ZODIAC_LORDS = {
    ZodiacSign.ARIES: Planet.MARS,
    ZodiacSign.TAURUS: Planet.VENUS,
    ZodiacSign.GEMINI: Planet.MERCURY,
    ZodiacSign.CANCER: Planet.MOON,
    ZodiacSign.LEO: Planet.SUN,
    ZodiacSign.VIRGO: Planet.MERCURY,
    ZodiacSign.LIBRA: Planet.VENUS,
    ZodiacSign.SCORPIO: Planet.MARS,
    ZodiacSign.SAGITTARIUS: Planet.JUPITER,
    ZodiacSign.CAPRICORN: Planet.SATURN,
    ZodiacSign.AQUARIUS: Planet.SATURN,
    ZodiacSign.PISCES: Planet.JUPITER,
}


class Nakshatra(str, Enum):
    """27 Nakshatras (Lunar mansions)."""
    ASHWINI = "Ashwini"
    BHARANI = "Bharani"
    KRITTIKA = "Krittika"
    ROHINI = "Rohini"
    MRIGASHIRA = "Mrigashira"
    ARDRA = "Ardra"
    PUNARVASU = "Punarvasu"
    PUSHYA = "Pushya"
    ASHLESHA = "Ashlesha"
    MAGHA = "Magha"
    PURVA_PHALGUNI = "Purva Phalguni"
    UTTARA_PHALGUNI = "Uttara Phalguni"
    HASTA = "Hasta"
    CHITRA = "Chitra"
    SWATI = "Swati"
    VISHAKHA = "Vishakha"
    ANURADHA = "Anuradha"
    JYESHTHA = "Jyeshtha"
    MULA = "Mula"
    PURVA_ASHADHA = "Purva Ashadha"
    UTTARA_ASHADHA = "Uttara Ashadha"
    SHRAVANA = "Shravana"
    DHANISHTA = "Dhanishta"
    SHATABHISHA = "Shatabhisha"
    PURVA_BHADRAPADA = "Purva Bhadrapada"
    UTTARA_BHADRAPADA = "Uttara Bhadrapada"
    REVATI = "Revati"


# Nakshatra ruling planets for Vimshottari Dasha
NAKSHATRA_LORDS = {
    Nakshatra.ASHWINI: Planet.KETU,
    Nakshatra.BHARANI: Planet.VENUS,
    Nakshatra.KRITTIKA: Planet.SUN,
    Nakshatra.ROHINI: Planet.MOON,
    Nakshatra.MRIGASHIRA: Planet.MARS,
    Nakshatra.ARDRA: Planet.RAHU,
    Nakshatra.PUNARVASU: Planet.JUPITER,
    Nakshatra.PUSHYA: Planet.SATURN,
    Nakshatra.ASHLESHA: Planet.MERCURY,
    Nakshatra.MAGHA: Planet.KETU,
    Nakshatra.PURVA_PHALGUNI: Planet.VENUS,
    Nakshatra.UTTARA_PHALGUNI: Planet.SUN,
    Nakshatra.HASTA: Planet.MOON,
    Nakshatra.CHITRA: Planet.MARS,
    Nakshatra.SWATI: Planet.RAHU,
    Nakshatra.VISHAKHA: Planet.JUPITER,
    Nakshatra.ANURADHA: Planet.SATURN,
    Nakshatra.JYESHTHA: Planet.MERCURY,
    Nakshatra.MULA: Planet.KETU,
    Nakshatra.PURVA_ASHADHA: Planet.VENUS,
    Nakshatra.UTTARA_ASHADHA: Planet.SUN,
    Nakshatra.SHRAVANA: Planet.MOON,
    Nakshatra.DHANISHTA: Planet.MARS,
    Nakshatra.SHATABHISHA: Planet.RAHU,
    Nakshatra.PURVA_BHADRAPADA: Planet.JUPITER,
    Nakshatra.UTTARA_BHADRAPADA: Planet.SATURN,
    Nakshatra.REVATI: Planet.MERCURY,
}


class BirthDetails(BaseModel):
    """User input for birth details."""

    name: Optional[str] = Field(None, description="Name of the person")
    date_of_birth: date = Field(..., description="Date of birth (YYYY-MM-DD)")
    time_of_birth: str = Field(..., description="Time of birth (HH:MM:SS or HH:MM)")
    place_of_birth: str = Field(..., description="Place of birth")

    # Computed fields (set after geocoding)
    latitude: Optional[float] = Field(None, description="Latitude of birth place")
    longitude: Optional[float] = Field(None, description="Longitude of birth place")
    timezone: Optional[str] = Field(None, description="Timezone string")

    # Configuration
    ayanamsa: AyanamsaType = Field(default=AyanamsaType.LAHIRI, description="Ayanamsa to use")
    house_system: HouseSystem = Field(default=HouseSystem.WHOLE_SIGN, description="House system")

    # Uncertainty flag
    time_uncertain: bool = Field(default=False, description="Whether birth time has uncertainty")
    time_uncertainty_minutes: int = Field(default=0, description="Uncertainty in minutes")

    @field_validator('time_of_birth')
    @classmethod
    def validate_time(cls, v):
        """Validate and normalize time format."""
        v = v.strip().upper()
        # Remove AM/PM for now, parse later
        return v


class NakshatraData(BaseModel):
    """Nakshatra position data."""

    name: Nakshatra = Field(..., description="Nakshatra name")
    pada: int = Field(..., ge=1, le=4, description="Pada (1-4)")
    lord: Planet = Field(..., description="Nakshatra lord")
    degree_in_nakshatra: float = Field(..., ge=0, lt=13.3334, description="Degree within nakshatra")


class PlanetPosition(BaseModel):
    """Immutable planetary position data."""

    planet: Planet = Field(..., description="Planet name")
    longitude: float = Field(..., ge=0, lt=360, description="Sidereal longitude (0-360)")
    sign: ZodiacSign = Field(..., description="Zodiac sign")
    sign_degree: float = Field(..., ge=0, lt=30, description="Degree within sign (0-30)")
    house: int = Field(..., ge=1, le=12, description="House placement (1-12)")
    nakshatra: NakshatraData = Field(..., description="Nakshatra data")

    # Additional attributes
    is_retrograde: bool = Field(default=False, description="Whether planet is retrograde")
    is_combust: bool = Field(default=False, description="Whether planet is combust (too close to Sun)")
    speed: float = Field(default=0.0, description="Daily speed in degrees")

    # Dignity (calculated by rules engine)
    dignity: Optional[str] = Field(None, description="own/exalted/debilitated/neutral")

    class Config:
        frozen = True  # Make immutable


class HouseData(BaseModel):
    """House (Bhava) data."""

    house_number: int = Field(..., ge=1, le=12)
    sign: ZodiacSign = Field(..., description="Sign on house cusp")
    lord: Planet = Field(..., description="House lord")
    degree: float = Field(..., ge=0, lt=360, description="Cusp degree")
    planets: List[Planet] = Field(default_factory=list, description="Planets in this house")

    class Config:
        frozen = True


class AspectData(BaseModel):
    """Graha Drishti (planetary aspect) data."""

    aspecting_planet: Planet
    aspected_planet: Optional[Planet] = None
    aspected_house: Optional[int] = None
    aspect_type: str = Field(..., description="Type of aspect (full/partial)")
    strength: float = Field(default=1.0, ge=0, le=1, description="Aspect strength")


class ChartData(BaseModel):
    """
    Complete birth chart data - IMMUTABLE after computation.

    This is the single source of truth for all astrological calculations.
    LLM receives this data but cannot modify it.
    """

    # Metadata
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    birth_details: BirthDetails

    # Core chart data
    ascendant: PlanetPosition = Field(..., description="Ascendant (Lagna) position")
    planets: Dict[Planet, PlanetPosition] = Field(..., description="All planetary positions")
    houses: Dict[int, HouseData] = Field(..., description="All 12 houses")

    # Computed attributes
    sun_sign: ZodiacSign = Field(..., description="Sun sign (Western)")
    moon_sign: ZodiacSign = Field(..., description="Moon sign (Rashi)")
    moon_nakshatra: NakshatraData = Field(..., description="Moon's nakshatra")

    # Aspects
    aspects: List[AspectData] = Field(default_factory=list)

    # Vedic attributes for matching
    varna: str = Field(..., description="Brahmin/Kshatriya/Vaishya/Shudra")
    nadi: str = Field(..., description="Adi/Madhya/Antya")
    yoni: str = Field(..., description="Animal type from nakshatra")
    gana: str = Field(..., description="Deva/Manushya/Rakshasa")
    vashya: str = Field(..., description="Vashya category")

    # Julian day for reference
    julian_day: float = Field(..., description="Julian day number")

    class Config:
        frozen = True  # CRITICAL: Make immutable


class PanchangData(BaseModel):
    """Panchang (5-element Vedic calendar) data."""

    date: date
    place: str

    tithi: str = Field(..., description="Lunar day name")
    tithi_number: int = Field(..., ge=1, le=30)
    tithi_paksha: str = Field(..., description="Shukla/Krishna Paksha")

    nakshatra: str = Field(..., description="Current nakshatra")
    nakshatra_pada: int = Field(..., ge=1, le=4)

    yoga: str = Field(..., description="Yoga name")
    karana: str = Field(..., description="Karana name")

    vara: str = Field(..., description="Day of week (Sanskrit)")

    moon_sign: ZodiacSign
    sun_sign: ZodiacSign

    sunrise: Optional[str] = None
    sunset: Optional[str] = None

    auspicious_timings: List[str] = Field(default_factory=list)
    inauspicious_timings: List[str] = Field(default_factory=list)
