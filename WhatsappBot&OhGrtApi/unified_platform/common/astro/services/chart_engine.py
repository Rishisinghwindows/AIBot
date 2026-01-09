"""
Chart Engine Service

Deterministic chart calculations using Swiss Ephemeris.
This is the ONLY place where astrological math happens.
LLM never touches these calculations.

All calculations use:
- Swiss Ephemeris for planetary positions
- Lahiri Ayanamsa (default) for sidereal zodiac
- Whole Sign house system (default)
"""

import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime, date, timedelta

from common.astro.schemas.chart import (
    BirthDetails,
    ChartData,
    PlanetPosition,
    HouseData,
    NakshatraData,
    AspectData,
    PanchangData,
    Planet,
    ZodiacSign,
    Nakshatra,
    AyanamsaType,
    HouseSystem,
    ZODIAC_LORDS,
    NAKSHATRA_LORDS,
)

logger = logging.getLogger(__name__)

# Try to import Swiss Ephemeris
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False
    logger.warning("Swiss Ephemeris not available. Using simplified calculations.")

# Try to import geopy for geocoding
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False
    logger.warning("Geopy not available. Using fallback coordinates.")


# =============================================================================
# CONSTANTS
# =============================================================================

ZODIAC_SIGNS_LIST = list(ZodiacSign)
NAKSHATRAS_LIST = list(Nakshatra)

# Planet IDs for Swiss Ephemeris
SWE_PLANETS = {
    Planet.SUN: 0,      # swe.SUN
    Planet.MOON: 1,     # swe.MOON
    Planet.MARS: 4,     # swe.MARS
    Planet.MERCURY: 2,  # swe.MERCURY
    Planet.JUPITER: 5,  # swe.JUPITER
    Planet.VENUS: 3,    # swe.VENUS
    Planet.SATURN: 6,   # swe.SATURN
    Planet.RAHU: 10,    # swe.MEAN_NODE (True node would be 11)
}

# Ayanamsa mapping
AYANAMSA_MAP = {
    AyanamsaType.LAHIRI: 1,      # swe.SIDM_LAHIRI
    AyanamsaType.RAMAN: 3,       # swe.SIDM_RAMAN
    AyanamsaType.KRISHNAMURTI: 5,  # swe.SIDM_KRISHNAMURTI
}

# Varna mapping (Moon sign based)
VARNA_MAPPING = {
    ZodiacSign.CANCER: "Brahmin",
    ZodiacSign.SCORPIO: "Brahmin",
    ZodiacSign.PISCES: "Brahmin",
    ZodiacSign.ARIES: "Kshatriya",
    ZodiacSign.LEO: "Kshatriya",
    ZodiacSign.SAGITTARIUS: "Kshatriya",
    ZodiacSign.TAURUS: "Vaishya",
    ZodiacSign.VIRGO: "Vaishya",
    ZodiacSign.CAPRICORN: "Vaishya",
    ZodiacSign.GEMINI: "Shudra",
    ZodiacSign.LIBRA: "Shudra",
    ZodiacSign.AQUARIUS: "Shudra",
}

# Nadi mapping (Nakshatra based)
NADI_MAPPING = {
    "Adi": [
        Nakshatra.ASHWINI, Nakshatra.ARDRA, Nakshatra.PUNARVASU,
        Nakshatra.UTTARA_PHALGUNI, Nakshatra.HASTA, Nakshatra.JYESHTHA,
        Nakshatra.MULA, Nakshatra.SHATABHISHA, Nakshatra.PURVA_BHADRAPADA
    ],
    "Madhya": [
        Nakshatra.BHARANI, Nakshatra.MRIGASHIRA, Nakshatra.PUSHYA,
        Nakshatra.PURVA_PHALGUNI, Nakshatra.CHITRA, Nakshatra.ANURADHA,
        Nakshatra.PURVA_ASHADHA, Nakshatra.DHANISHTA, Nakshatra.UTTARA_BHADRAPADA
    ],
    "Antya": [
        Nakshatra.KRITTIKA, Nakshatra.ROHINI, Nakshatra.ASHLESHA,
        Nakshatra.MAGHA, Nakshatra.SWATI, Nakshatra.VISHAKHA,
        Nakshatra.UTTARA_ASHADHA, Nakshatra.SHRAVANA, Nakshatra.REVATI
    ]
}

# Yoni (animal) mapping
YONI_MAPPING = {
    Nakshatra.ASHWINI: "Horse",
    Nakshatra.BHARANI: "Elephant",
    Nakshatra.KRITTIKA: "Sheep",
    Nakshatra.ROHINI: "Serpent",
    Nakshatra.MRIGASHIRA: "Serpent",
    Nakshatra.ARDRA: "Dog",
    Nakshatra.PUNARVASU: "Cat",
    Nakshatra.PUSHYA: "Goat",
    Nakshatra.ASHLESHA: "Cat",
    Nakshatra.MAGHA: "Rat",
    Nakshatra.PURVA_PHALGUNI: "Rat",
    Nakshatra.UTTARA_PHALGUNI: "Cow",
    Nakshatra.HASTA: "Buffalo",
    Nakshatra.CHITRA: "Tiger",
    Nakshatra.SWATI: "Buffalo",
    Nakshatra.VISHAKHA: "Tiger",
    Nakshatra.ANURADHA: "Deer",
    Nakshatra.JYESHTHA: "Deer",
    Nakshatra.MULA: "Dog",
    Nakshatra.PURVA_ASHADHA: "Monkey",
    Nakshatra.UTTARA_ASHADHA: "Mongoose",
    Nakshatra.SHRAVANA: "Monkey",
    Nakshatra.DHANISHTA: "Lion",
    Nakshatra.SHATABHISHA: "Horse",
    Nakshatra.PURVA_BHADRAPADA: "Lion",
    Nakshatra.UTTARA_BHADRAPADA: "Cow",
    Nakshatra.REVATI: "Elephant",
}

# Gana (temperament) mapping
GANA_MAPPING = {
    "Deva": [
        Nakshatra.ASHWINI, Nakshatra.MRIGASHIRA, Nakshatra.PUNARVASU,
        Nakshatra.PUSHYA, Nakshatra.HASTA, Nakshatra.SWATI,
        Nakshatra.ANURADHA, Nakshatra.SHRAVANA, Nakshatra.REVATI
    ],
    "Manushya": [
        Nakshatra.BHARANI, Nakshatra.ROHINI, Nakshatra.ARDRA,
        Nakshatra.PURVA_PHALGUNI, Nakshatra.UTTARA_PHALGUNI, Nakshatra.PURVA_ASHADHA,
        Nakshatra.UTTARA_ASHADHA, Nakshatra.PURVA_BHADRAPADA, Nakshatra.UTTARA_BHADRAPADA
    ],
    "Rakshasa": [
        Nakshatra.KRITTIKA, Nakshatra.ASHLESHA, Nakshatra.MAGHA,
        Nakshatra.CHITRA, Nakshatra.VISHAKHA, Nakshatra.JYESHTHA,
        Nakshatra.MULA, Nakshatra.DHANISHTA, Nakshatra.SHATABHISHA
    ]
}

# Vashya mapping (Moon sign based)
VASHYA_MAPPING = {
    "Human": [ZodiacSign.GEMINI, ZodiacSign.VIRGO, ZodiacSign.LIBRA, ZodiacSign.AQUARIUS],
    "Quadruped": [ZodiacSign.ARIES, ZodiacSign.TAURUS, ZodiacSign.SAGITTARIUS, ZodiacSign.CAPRICORN],
    "Water": [ZodiacSign.CANCER, ZodiacSign.PISCES],
    "Wild Animal": [ZodiacSign.LEO],
    "Insect": [ZodiacSign.SCORPIO],
}

# Common Indian cities with coordinates
CITY_COORDINATES = {
    "delhi": (28.6139, 77.2090),
    "new delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "varanasi": (25.3176, 82.9739),
    "chandigarh": (30.7333, 76.7794),
    "patna": (25.5941, 85.1376),
    "bhopal": (23.2599, 77.4126),
    "indore": (22.7196, 75.8577),
    "nagpur": (21.1458, 79.0882),
    "surat": (21.1702, 72.8311),
    "kanpur": (26.4499, 80.3319),
    "new york": (40.7128, -74.0060),
    "london": (51.5074, -0.1278),
    "sydney": (-33.8688, 151.2093),
    "dubai": (25.2048, 55.2708),
    "singapore": (1.3521, 103.8198),
}

# Yoga names (27)
YOGA_NAMES = [
    "Vishkumbha", "Preeti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

# Tithi names (30)
TITHI_NAMES = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shasthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima",  # Shukla Paksha (1-15)
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shasthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Amavasya"   # Krishna Paksha (16-30)
]

# Vara (day) names
VARA_NAMES = {
    0: "Ravivara",    # Sunday
    1: "Somavara",    # Monday
    2: "Mangalavara", # Tuesday
    3: "Budhavara",   # Wednesday
    4: "Guruvara",    # Thursday
    5: "Shukravara",  # Friday
    6: "Shanivara",   # Saturday
}


class ChartEngine:
    """
    Deterministic Chart Calculation Engine.

    All calculations are pure functions with no randomness.
    Results are immutable after computation.
    """

    def __init__(self, ayanamsa: AyanamsaType = AyanamsaType.LAHIRI):
        """Initialize chart engine with ayanamsa."""
        self.ayanamsa = ayanamsa
        self._setup_ephemeris()

    def _setup_ephemeris(self):
        """Setup Swiss Ephemeris with correct ayanamsa."""
        if HAS_SWISSEPH:
            ayanamsa_id = AYANAMSA_MAP.get(self.ayanamsa, 1)
            swe.set_sid_mode(ayanamsa_id)

    # =========================================================================
    # GEOCODING
    # =========================================================================

    def get_coordinates(self, place: str) -> Tuple[float, float]:
        """
        Get latitude and longitude for a place.

        Uses geopy if available, otherwise falls back to known cities.
        """
        place_lower = place.lower().strip()

        # Check known cities first (faster)
        for city, coords in CITY_COORDINATES.items():
            if city in place_lower:
                return coords

        # Try geopy
        if HAS_GEOPY:
            try:
                geolocator = Nominatim(user_agent="vedic_astro_bot", timeout=10)
                location = geolocator.geocode(place)
                if location:
                    return (location.latitude, location.longitude)
            except GeocoderTimedOut:
                logger.warning(f"Geocoding timed out for: {place}")
            except Exception as e:
                logger.warning(f"Geocoding error for {place}: {e}")

        # Default to Delhi
        logger.warning(f"Using default coordinates (Delhi) for: {place}")
        return CITY_COORDINATES["delhi"]

    # =========================================================================
    # BASIC CALCULATIONS
    # =========================================================================

    def _parse_time(self, time_str: str) -> Tuple[int, int, int]:
        """Parse time string into (hour, minute, second)."""
        time_str = time_str.strip().upper()

        # Handle AM/PM
        is_pm = "PM" in time_str
        is_am = "AM" in time_str
        time_str = time_str.replace("AM", "").replace("PM", "").strip()

        # Parse components
        parts = time_str.replace(":", " ").replace(".", " ").split()
        hour = int(parts[0]) if parts else 12
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0

        # Convert to 24-hour format
        if is_pm and hour < 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0

        return hour, minute, second

    def _get_julian_day(self, dt: datetime) -> float:
        """Convert datetime to Julian day number."""
        if HAS_SWISSEPH:
            hour_decimal = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            return swe.julday(dt.year, dt.month, dt.day, hour_decimal)
        else:
            # Simplified Julian day calculation
            a = (14 - dt.month) // 12
            y = dt.year + 4800 - a
            m = dt.month + 12 * a - 3
            jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
            hour_decimal = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            return jdn + hour_decimal / 24.0 - 0.5

    def _get_zodiac_sign(self, longitude: float) -> ZodiacSign:
        """Get zodiac sign from longitude (0-360)."""
        sign_index = int(longitude // 30) % 12
        return ZODIAC_SIGNS_LIST[sign_index]

    def _get_nakshatra(self, longitude: float) -> Tuple[Nakshatra, int, float]:
        """
        Get nakshatra, pada, and degree within nakshatra from longitude.

        Each nakshatra spans 13°20' (13.3333°).
        Each pada spans 3°20' (3.3333°).
        """
        nakshatra_span = 360 / 27  # 13.3333°
        pada_span = nakshatra_span / 4  # 3.3333°

        nakshatra_index = int((longitude % 360) / nakshatra_span) % 27
        degree_in_nakshatra = longitude % nakshatra_span
        pada = int(degree_in_nakshatra / pada_span) + 1

        return NAKSHATRAS_LIST[nakshatra_index], pada, degree_in_nakshatra

    def _get_varna(self, moon_sign: ZodiacSign) -> str:
        """Get Varna from Moon sign."""
        return VARNA_MAPPING.get(moon_sign, "Unknown")

    def _get_nadi(self, nakshatra: Nakshatra) -> str:
        """Get Nadi from Nakshatra."""
        for nadi, nakshatras in NADI_MAPPING.items():
            if nakshatra in nakshatras:
                return nadi
        return "Unknown"

    def _get_yoni(self, nakshatra: Nakshatra) -> str:
        """Get Yoni (animal) from Nakshatra."""
        return YONI_MAPPING.get(nakshatra, "Unknown")

    def _get_gana(self, nakshatra: Nakshatra) -> str:
        """Get Gana from Nakshatra."""
        for gana, nakshatras in GANA_MAPPING.items():
            if nakshatra in nakshatras:
                return gana
        return "Unknown"

    def _get_vashya(self, moon_sign: ZodiacSign) -> str:
        """Get Vashya from Moon sign."""
        for vashya, signs in VASHYA_MAPPING.items():
            if moon_sign in signs:
                return vashya
        return "Unknown"

    # =========================================================================
    # PLANETARY CALCULATIONS
    # =========================================================================

    def _calculate_planet_position(
        self,
        julian_day: float,
        planet: Planet,
        ascendant_longitude: float
    ) -> PlanetPosition:
        """Calculate position of a single planet."""

        if HAS_SWISSEPH:
            planet_id = SWE_PLANETS.get(planet)
            if planet_id is None:
                # Ketu is calculated from Rahu
                if planet == Planet.KETU:
                    rahu_result = swe.calc_ut(julian_day, SWE_PLANETS[Planet.RAHU], swe.FLG_SIDEREAL)
                    longitude = (rahu_result[0][0] + 180) % 360
                    speed = -rahu_result[0][3]  # Opposite direction
                else:
                    raise ValueError(f"Unknown planet: {planet}")
            else:
                result = swe.calc_ut(julian_day, planet_id, swe.FLG_SIDEREAL)
                longitude = result[0][0] % 360
                speed = result[0][3]
        else:
            # Simplified fallback (not accurate for production)
            day_offset = julian_day - 2451545.0  # Days since J2000
            if planet == Planet.SUN:
                longitude = (day_offset * 360 / 365.25) % 360
            elif planet == Planet.MOON:
                longitude = (day_offset * 13.176) % 360
            else:
                # Very approximate
                longitude = (day_offset * (360 / 365.25) * 0.5) % 360
            speed = 0.0

        # Calculate derived values
        sign = self._get_zodiac_sign(longitude)
        sign_degree = longitude % 30
        nakshatra, pada, degree_in_nak = self._get_nakshatra(longitude)

        # Calculate house (Whole Sign)
        house = int(((longitude - ascendant_longitude) % 360) / 30) + 1

        # Check retrograde (negative speed, except for Sun and Moon)
        is_retrograde = speed < 0 and planet not in [Planet.SUN, Planet.MOON]

        # Check combustion (within certain degrees of Sun)
        is_combust = False  # Will be calculated after all planets

        return PlanetPosition(
            planet=planet,
            longitude=round(longitude, 4),
            sign=sign,
            sign_degree=round(sign_degree, 4),
            house=house,
            nakshatra=NakshatraData(
                name=nakshatra,
                pada=pada,
                lord=NAKSHATRA_LORDS.get(nakshatra, Planet.SUN),
                degree_in_nakshatra=round(degree_in_nak, 4)
            ),
            is_retrograde=is_retrograde,
            is_combust=is_combust,
            speed=round(speed, 6)
        )

    def _calculate_houses(
        self,
        julian_day: float,
        latitude: float,
        longitude: float,
        house_system: HouseSystem
    ) -> Tuple[float, Dict[int, HouseData]]:
        """
        Calculate ascendant and 12 houses.

        Returns (ascendant_longitude, {house_num: HouseData})
        """

        if HAS_SWISSEPH:
            # House system codes
            house_codes = {
                HouseSystem.WHOLE_SIGN: b'W',
                HouseSystem.PLACIDUS: b'P',
                HouseSystem.EQUAL: b'E',
            }
            house_code = house_codes.get(house_system, b'W')

            cusps, ascmc = swe.houses_ex(
                julian_day, latitude, longitude, house_code, swe.FLG_SIDEREAL
            )
            ascendant_longitude = ascmc[0]
        else:
            # Very simplified fallback
            hour_decimal = (julian_day % 1) * 24
            ascendant_longitude = (hour_decimal * 15 + longitude) % 360

            # Generate cusps for whole sign
            asc_sign_start = (int(ascendant_longitude / 30) * 30)
            cusps = [(asc_sign_start + i * 30) % 360 for i in range(12)]

        # Build house data
        houses = {}
        for i in range(12):
            house_num = i + 1
            if HAS_SWISSEPH and house_system != HouseSystem.WHOLE_SIGN:
                cusp_degree = cusps[i]
            else:
                # Whole sign: each house starts at sign boundary
                cusp_degree = ((int(ascendant_longitude / 30) + i) * 30) % 360

            sign = self._get_zodiac_sign(cusp_degree)
            lord = ZODIAC_LORDS.get(sign, Planet.SUN)

            houses[house_num] = HouseData(
                house_number=house_num,
                sign=sign,
                lord=lord,
                degree=round(cusp_degree, 4),
                planets=[]  # Will be populated later
            )

        return ascendant_longitude, houses

    def _check_combustion(
        self,
        planets: Dict[Planet, PlanetPosition],
        sun_position: PlanetPosition
    ) -> Dict[Planet, PlanetPosition]:
        """
        Check and update combustion status for all planets.

        Combustion occurs when a planet is too close to the Sun.
        """
        combustion_degrees = {
            Planet.MOON: 12,
            Planet.MARS: 17,
            Planet.MERCURY: 14,  # 12 if retrograde
            Planet.JUPITER: 11,
            Planet.VENUS: 10,   # 8 if retrograde
            Planet.SATURN: 15,
        }

        sun_long = sun_position.longitude
        updated_planets = {}

        for planet, position in planets.items():
            if planet in combustion_degrees:
                threshold = combustion_degrees[planet]
                if position.is_retrograde and planet in [Planet.MERCURY, Planet.VENUS]:
                    threshold -= 2

                diff = abs(position.longitude - sun_long)
                if diff > 180:
                    diff = 360 - diff

                is_combust = diff < threshold

                # Create new position with updated combust status
                updated_planets[planet] = PlanetPosition(
                    planet=position.planet,
                    longitude=position.longitude,
                    sign=position.sign,
                    sign_degree=position.sign_degree,
                    house=position.house,
                    nakshatra=position.nakshatra,
                    is_retrograde=position.is_retrograde,
                    is_combust=is_combust,
                    speed=position.speed
                )
            else:
                updated_planets[planet] = position

        return updated_planets

    # =========================================================================
    # MAIN CALCULATION METHODS
    # =========================================================================

    def calculate_chart(self, birth_details: BirthDetails) -> ChartData:
        """
        Calculate complete birth chart.

        This is a PURE FUNCTION - same inputs always produce same outputs.
        Result is IMMUTABLE after computation.
        """
        # Get coordinates if not provided
        if birth_details.latitude is None or birth_details.longitude is None:
            lat, lon = self.get_coordinates(birth_details.place_of_birth)
            birth_details.latitude = lat
            birth_details.longitude = lon

        # Parse date and time
        hour, minute, second = self._parse_time(birth_details.time_of_birth)
        dt = datetime(
            birth_details.date_of_birth.year,
            birth_details.date_of_birth.month,
            birth_details.date_of_birth.day,
            hour, minute, second
        )

        # Get Julian day
        julian_day = self._get_julian_day(dt)

        # Calculate houses and ascendant
        ascendant_longitude, houses = self._calculate_houses(
            julian_day,
            birth_details.latitude,
            birth_details.longitude,
            birth_details.house_system
        )

        # Calculate ascendant position
        asc_sign = self._get_zodiac_sign(ascendant_longitude)
        asc_nakshatra, asc_pada, asc_degree_in_nak = self._get_nakshatra(ascendant_longitude)

        ascendant = PlanetPosition(
            planet=Planet.SUN,  # Placeholder for ascendant
            longitude=round(ascendant_longitude, 4),
            sign=asc_sign,
            sign_degree=round(ascendant_longitude % 30, 4),
            house=1,
            nakshatra=NakshatraData(
                name=asc_nakshatra,
                pada=asc_pada,
                lord=NAKSHATRA_LORDS.get(asc_nakshatra, Planet.SUN),
                degree_in_nakshatra=round(asc_degree_in_nak, 4)
            ),
            is_retrograde=False,
            is_combust=False,
            speed=0.0
        )

        # Calculate all planetary positions
        planets = {}
        for planet in Planet:
            planets[planet] = self._calculate_planet_position(
                julian_day, planet, ascendant_longitude
            )

        # Check combustion
        planets = self._check_combustion(planets, planets[Planet.SUN])

        # Assign planets to houses
        for planet, position in planets.items():
            house_num = position.house
            if house_num in houses:
                houses[house_num].planets.append(planet)

        # Get Moon's nakshatra for matching attributes
        moon_nakshatra = planets[Planet.MOON].nakshatra.name
        moon_sign = planets[Planet.MOON].sign

        # Calculate Vedic attributes
        varna = self._get_varna(moon_sign)
        nadi = self._get_nadi(moon_nakshatra)
        yoni = self._get_yoni(moon_nakshatra)
        gana = self._get_gana(moon_nakshatra)
        vashya = self._get_vashya(moon_sign)

        # Build chart data
        chart = ChartData(
            birth_details=birth_details,
            ascendant=ascendant,
            planets=planets,
            houses=houses,
            sun_sign=planets[Planet.SUN].sign,
            moon_sign=moon_sign,
            moon_nakshatra=planets[Planet.MOON].nakshatra,
            varna=varna,
            nadi=nadi,
            yoni=yoni,
            gana=gana,
            vashya=vashya,
            julian_day=julian_day,
            aspects=[]  # Will be calculated by rules engine
        )

        logger.info(f"Chart calculated for {birth_details.name or 'unnamed'} at {birth_details.place_of_birth}")
        return chart

    def calculate_panchang(self, target_date: date, place: str = "Delhi") -> PanchangData:
        """
        Calculate Panchang (5-element Vedic calendar) for a given date.
        """
        latitude, longitude = self.get_coordinates(place)

        # Use noon for panchang calculations
        dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0)
        julian_day = self._get_julian_day(dt)

        if HAS_SWISSEPH:
            sun_result = swe.calc_ut(julian_day, 0, swe.FLG_SIDEREAL)
            moon_result = swe.calc_ut(julian_day, 1, swe.FLG_SIDEREAL)
            sun_longitude = sun_result[0][0] % 360
            moon_longitude = moon_result[0][0] % 360
        else:
            day_offset = julian_day - 2451545.0
            sun_longitude = (day_offset * 360 / 365.25) % 360
            moon_longitude = (day_offset * 13.176) % 360

        # Calculate Tithi
        angle_diff = (moon_longitude - sun_longitude) % 360
        tithi_number = int(angle_diff / 12) + 1
        if tithi_number > 30:
            tithi_number = 30
        tithi_name = TITHI_NAMES[tithi_number - 1]
        paksha = "Shukla Paksha" if tithi_number <= 15 else "Krishna Paksha"

        # Calculate Nakshatra
        nakshatra, pada, _ = self._get_nakshatra(moon_longitude)

        # Calculate Yoga
        total_longitude = (sun_longitude + moon_longitude) % 360
        yoga_index = int(total_longitude / 13.3333) % 27
        yoga_name = YOGA_NAMES[yoga_index]

        # Calculate Karana
        karana_index = int((angle_diff % 12) / 6)
        karana_names = [
            "Bava", "Balava", "Kaulava", "Taitila", "Gara",
            "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
        ]
        karana = karana_names[karana_index % len(karana_names)]

        # Get Vara (day of week)
        weekday = target_date.weekday()
        vara = VARA_NAMES.get(weekday, "Unknown")

        return PanchangData(
            date=target_date,
            place=place,
            tithi=tithi_name,
            tithi_number=tithi_number,
            tithi_paksha=paksha,
            nakshatra=nakshatra.value,
            nakshatra_pada=pada,
            yoga=yoga_name,
            karana=karana,
            vara=vara,
            moon_sign=self._get_zodiac_sign(moon_longitude),
            sun_sign=self._get_zodiac_sign(sun_longitude),
        )

    def calculate_transit_positions(self, target_date: date) -> Dict[Planet, PlanetPosition]:
        """
        Calculate current planetary positions for transit analysis.
        """
        dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0)
        julian_day = self._get_julian_day(dt)

        # Use Aries as reference ascendant for transit charts
        ascendant_longitude = 0.0

        positions = {}
        for planet in Planet:
            positions[planet] = self._calculate_planet_position(
                julian_day, planet, ascendant_longitude
            )

        return positions
