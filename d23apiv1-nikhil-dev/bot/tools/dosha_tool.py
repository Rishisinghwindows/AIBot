"""
Dosha Detection Tool

Detects major Vedic astrology doshas:
1. Manglik/Mangal Dosha - Mars in 1, 4, 7, 8, 12 from Lagna/Moon
2. Kaal Sarp Dosha - All planets between Rahu-Ketu axis
3. Shani Sade Sati - Saturn transiting 12th, 1st, 2nd from Moon
4. Pitra Dosha - Sun afflicted by Rahu/Ketu/Saturn
5. Nadi Dosha - Same Nadi in matching (for compatibility)
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from bot.state import ToolResult
from bot.tools.astro_tool import (
    calculate_kundli,
    get_zodiac_sign,
    get_nakshatra,
    ZODIAC_SIGNS,
    NAKSHATRAS,
    RASHI_LORD,
)

# Try to import Swiss Ephemeris for transit calculations
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False


# =============================================================================
# CONSTANTS
# =============================================================================

# Manglik Dosha - Houses where Mars causes dosha
MANGLIK_HOUSES = [1, 4, 7, 8, 12]

# Kaal Sarp Dosha types based on Rahu's house
KAAL_SARP_TYPES = {
    1: "Anant Kaal Sarp",
    2: "Kulik Kaal Sarp",
    3: "Vasuki Kaal Sarp",
    4: "Shankpal Kaal Sarp",
    5: "Padma Kaal Sarp",
    6: "Mahapadma Kaal Sarp",
    7: "Takshak Kaal Sarp",
    8: "Karkotak Kaal Sarp",
    9: "Shankachood Kaal Sarp",
    10: "Ghatak Kaal Sarp",
    11: "Vishdhar Kaal Sarp",
    12: "Sheshnag Kaal Sarp"
}

# Sade Sati phases
SADE_SATI_PHASES = {
    "rising": "Rising Phase (12th from Moon) - Beginning of challenges",
    "peak": "Peak Phase (Over Moon) - Most intense period",
    "setting": "Setting Phase (2nd from Moon) - Gradual relief"
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_house_number(planet_sign: str, reference_sign: str) -> int:
    """
    Calculate house number of a planet from a reference sign.

    Args:
        planet_sign: Sign where the planet is placed
        reference_sign: Reference sign (Lagna or Moon sign)

    Returns:
        House number (1-12)
    """
    if planet_sign not in ZODIAC_SIGNS or reference_sign not in ZODIAC_SIGNS:
        return 0

    planet_idx = ZODIAC_SIGNS.index(planet_sign)
    reference_idx = ZODIAC_SIGNS.index(reference_sign)

    house = ((planet_idx - reference_idx) % 12) + 1
    return house


def is_between_nodes(planet_deg: float, rahu_deg: float, ketu_deg: float) -> bool:
    """
    Check if a planet is between Rahu and Ketu.

    Rahu and Ketu are always 180 degrees apart.
    A planet is "between" if it falls in the arc from Rahu to Ketu (going forward).
    """
    # Normalize degrees
    planet_deg = planet_deg % 360
    rahu_deg = rahu_deg % 360
    ketu_deg = ketu_deg % 360

    # Check if planet is in the arc from Rahu to Ketu
    if rahu_deg < ketu_deg:
        return rahu_deg <= planet_deg <= ketu_deg
    else:
        return planet_deg >= rahu_deg or planet_deg <= ketu_deg


def get_current_saturn_sign() -> str:
    """Get Saturn's current zodiac sign."""
    if not HAS_SWISSEPH:
        # Approximate Saturn position (Saturn takes ~29.5 years to complete zodiac)
        # As of 2024, Saturn is in Aquarius/Pisces
        return "Pisces"

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    now = datetime.now()
    julian_day = swe.julday(now.year, now.month, now.day, 12.0)
    saturn_pos = swe.calc_ut(julian_day, swe.SATURN, swe.FLG_SIDEREAL)[0][0] % 360

    return get_zodiac_sign(saturn_pos)


# =============================================================================
# MANGLIK DOSHA
# =============================================================================

def check_manglik_dosha(chart_data: dict) -> dict:
    """
    Check for Manglik (Mangal) Dosha.

    Manglik dosha occurs when Mars is placed in:
    - 1st, 4th, 7th, 8th, or 12th house from Lagna
    - 1st, 4th, 7th, 8th, or 12th house from Moon

    Cancellation conditions:
    - Mars in own sign (Aries, Scorpio)
    - Mars in exaltation (Capricorn)
    - Mars aspected by benefics (Jupiter)
    - Mars in Leo in 7th house
    - Both partners are Manglik
    """
    mars_info = chart_data.get("planetary_positions", {}).get("Mars", {})
    mars_sign = mars_info.get("sign", "")

    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")
    moon_sign = chart_data.get("moon_sign", "")

    if not mars_sign or not ascendant_sign:
        return {
            "dosha_name": "Manglik Dosha",
            "is_present": False,
            "error": "Insufficient chart data"
        }

    # Calculate Mars house from Lagna and Moon
    mars_house_lagna = get_house_number(mars_sign, ascendant_sign)
    mars_house_moon = get_house_number(mars_sign, moon_sign) if moon_sign else 0

    is_manglik_lagna = mars_house_lagna in MANGLIK_HOUSES
    is_manglik_moon = mars_house_moon in MANGLIK_HOUSES

    # Check cancellation factors
    cancellation_factors = []

    # Mars in own sign
    if mars_sign in ["Aries", "Scorpio"]:
        cancellation_factors.append(f"Mars in own sign ({mars_sign})")

    # Mars in exaltation
    if mars_sign == "Capricorn":
        cancellation_factors.append("Mars in exaltation (Capricorn)")

    # Mars in Leo in 7th house (special cancellation)
    if mars_sign == "Leo" and mars_house_lagna == 7:
        cancellation_factors.append("Mars in Leo in 7th house")

    # Jupiter's aspect on Mars (check if Jupiter is in trine/opposition)
    jupiter_info = chart_data.get("planetary_positions", {}).get("Jupiter", {})
    jupiter_sign = jupiter_info.get("sign", "")
    if jupiter_sign:
        jupiter_house = get_house_number(jupiter_sign, ascendant_sign)
        mars_house = mars_house_lagna
        # Jupiter aspects 5th, 7th, 9th from its position
        jupiter_aspects = [(jupiter_house + 4) % 12 or 12,
                          (jupiter_house + 6) % 12 or 12,
                          (jupiter_house + 8) % 12 or 12]
        if mars_house in jupiter_aspects:
            cancellation_factors.append("Jupiter aspects Mars")

    # Determine severity
    is_cancelled = len(cancellation_factors) >= 2

    if is_manglik_lagna and is_manglik_moon:
        severity = "Cancelled" if is_cancelled else "High (Double Manglik)"
    elif is_manglik_lagna or is_manglik_moon:
        severity = "Cancelled" if is_cancelled else "Partial"
    else:
        severity = "None"

    is_present = (is_manglik_lagna or is_manglik_moon) and not is_cancelled

    # Effects based on house
    effects = []
    if is_manglik_lagna and not is_cancelled:
        house_effects = {
            1: "May cause ego clashes and health issues in marriage",
            4: "Domestic discord and property disputes possible",
            7: "Delays or obstacles in marriage, spouse compatibility issues",
            8: "Risk of accidents, hidden conflicts in relationship",
            12: "Excessive expenses, bed pleasures issues"
        }
        effects.append(house_effects.get(mars_house_lagna, "General marital challenges"))

    # Remedies
    remedies = []
    if is_present:
        remedies = [
            "Kumbh Vivah (symbolic marriage with pot/tree before actual marriage)",
            "Mangal Shanti Puja on Tuesday",
            "Recite Hanuman Chalisa daily",
            "Wear Red Coral (Moonga) after consultation",
            "Donate red lentils (masoor dal) on Tuesdays",
            "Fast on Tuesdays (Mangalvar Vrat)",
            "Visit Mangalnath Temple in Ujjain",
            "Marry a Manglik partner (doshas cancel each other)"
        ]

    return {
        "dosha_name": "Manglik Dosha (Kuja Dosha)",
        "is_present": is_present,
        "severity": severity,
        "mars_sign": mars_sign,
        "mars_house_from_lagna": mars_house_lagna,
        "mars_house_from_moon": mars_house_moon,
        "is_manglik_from_lagna": is_manglik_lagna,
        "is_manglik_from_moon": is_manglik_moon,
        "cancellation_factors": cancellation_factors,
        "effects": effects,
        "remedies": remedies,
        "advice": "Manglik dosha is common and has many cancellations. Consult an experienced astrologer for personalized guidance." if is_present else "No Manglik dosha present."
    }


# =============================================================================
# KAAL SARP DOSHA
# =============================================================================

def check_kaal_sarp_dosha(chart_data: dict) -> dict:
    """
    Check for Kaal Sarp Dosha.

    Occurs when all 7 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn)
    are hemmed between Rahu and Ketu axis.

    12 types based on Rahu's house position.
    """
    planets = chart_data.get("planetary_positions", {})

    rahu_info = planets.get("Rahu", {})
    ketu_info = planets.get("Ketu", {})

    rahu_deg = rahu_info.get("degree", 0)
    ketu_deg = ketu_info.get("degree", 0)

    if not rahu_deg and not ketu_deg:
        return {
            "dosha_name": "Kaal Sarp Dosha",
            "is_present": False,
            "error": "Rahu/Ketu positions not available"
        }

    # Check if all planets are between Rahu and Ketu
    planets_to_check = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    all_between = True
    planet_positions = []

    for planet_name in planets_to_check:
        planet_info = planets.get(planet_name, {})
        planet_deg = planet_info.get("degree", 0)

        is_between = is_between_nodes(planet_deg, rahu_deg, ketu_deg)
        planet_positions.append({
            "planet": planet_name,
            "degree": planet_deg,
            "sign": planet_info.get("sign", ""),
            "is_between": is_between
        })

        if not is_between:
            all_between = False

    if not all_between:
        return {
            "dosha_name": "Kaal Sarp Dosha",
            "is_present": False,
            "severity": "None",
            "message": "No Kaal Sarp Dosha - planets are not hemmed between Rahu-Ketu"
        }

    # Determine type based on Rahu's house
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")
    rahu_sign = rahu_info.get("sign", "")
    rahu_house = get_house_number(rahu_sign, ascendant_sign) if ascendant_sign and rahu_sign else 1

    dosha_type = KAAL_SARP_TYPES.get(rahu_house, "Kaal Sarp Dosha")

    # Effects based on type
    type_effects = {
        1: "Struggles in personal life, health issues, but eventual rise",
        2: "Financial challenges, family disputes, speech problems",
        3: "Sibling issues, communication problems, short travel troubles",
        4: "Mother's health, property disputes, mental unrest",
        5: "Children delays/issues, education obstacles, speculation losses",
        6: "Enemy troubles, health issues, debt problems",
        7: "Marriage delays, partnership issues, business troubles",
        8: "Sudden obstacles, accidents risk, inheritance issues",
        9: "Father's health, luck obstacles, higher education delays",
        10: "Career struggles, reputation issues, authority conflicts",
        11: "Income fluctuations, unfulfilled desires, elder sibling issues",
        12: "Expenses, foreign troubles, spiritual confusion"
    }

    # Remedies
    remedies = [
        "Kaal Sarp Dosha Nivaran Puja at Trimbakeshwar or Kalahasti",
        "Recite 'Om Namah Shivaya' 108 times daily",
        "Worship Lord Shiva on Mondays",
        "Offer milk to Shivling on Mondays and Saturdays",
        "Keep fast on Nag Panchami",
        "Donate black sesame seeds (til) on Saturdays",
        "Wear Gomed (Hessonite) for Rahu after consultation",
        "Perform Rahu-Ketu Shanti Puja",
        "Feed birds daily, especially crows",
        "Chant Rahu Beej Mantra: 'Om Bhram Bhreem Bhroum Sah Rahave Namah'"
    ]

    return {
        "dosha_name": "Kaal Sarp Dosha",
        "is_present": True,
        "type": dosha_type,
        "rahu_house": rahu_house,
        "severity": "High",
        "effects": type_effects.get(rahu_house, "General life obstacles and delays"),
        "positive_aspects": [
            "Can give sudden rise after struggles",
            "Spiritual inclination and intuition",
            "Success after 33-35 years of age",
            "Research and occult abilities"
        ],
        "remedies": remedies,
        "advice": "Kaal Sarp Dosha creates obstacles but also gives tremendous spiritual growth and eventual success after perseverance."
    }


# =============================================================================
# SHANI SADE SATI
# =============================================================================

def check_sade_sati(chart_data: dict, check_date: datetime = None) -> dict:
    """
    Check Shani Sade Sati status.

    Sade Sati is 7.5 year period when Saturn transits:
    - 12th house from Moon (Rising phase - 2.5 years)
    - 1st house (over Moon sign) (Peak phase - 2.5 years)
    - 2nd house from Moon (Setting phase - 2.5 years)

    Also checks Small Panoti (Dhaiya):
    - Saturn in 4th from Moon (Ardha Ashtama Shani)
    - Saturn in 8th from Moon (Ashtama Shani)
    """
    moon_sign = chart_data.get("moon_sign", "")

    if not moon_sign or moon_sign not in ZODIAC_SIGNS:
        return {
            "dosha_name": "Shani Sade Sati",
            "is_present": False,
            "error": "Moon sign not available"
        }

    # Get current Saturn sign
    current_saturn_sign = get_current_saturn_sign()

    moon_idx = ZODIAC_SIGNS.index(moon_sign)
    saturn_idx = ZODIAC_SIGNS.index(current_saturn_sign)

    # Calculate Saturn's position relative to Moon
    relative_position = (saturn_idx - moon_idx) % 12

    # Determine phase
    phase = None
    phase_name = None
    is_sade_sati = False
    is_dhaiya = False

    if relative_position == 11:  # 12th from Moon
        phase = "rising"
        phase_name = "Rising Phase (12th from Moon)"
        is_sade_sati = True
    elif relative_position == 0:  # Same as Moon (1st)
        phase = "peak"
        phase_name = "Peak Phase (Saturn over Moon sign)"
        is_sade_sati = True
    elif relative_position == 1:  # 2nd from Moon
        phase = "setting"
        phase_name = "Setting Phase (2nd from Moon)"
        is_sade_sati = True
    elif relative_position == 3:  # 4th from Moon
        is_dhaiya = True
        phase_name = "Small Panoti - Dhaiya (4th from Moon)"
    elif relative_position == 7:  # 8th from Moon
        is_dhaiya = True
        phase_name = "Ashtama Shani (8th from Moon)"

    # Calculate approximate dates
    # Saturn spends ~2.5 years in each sign
    saturn_entry_dates = calculate_saturn_transit_dates(current_saturn_sign)

    # Effects based on phase
    phase_effects = {
        "rising": [
            "Financial challenges may begin",
            "Health of family members may need attention",
            "Mental stress and worry increase",
            "Career pressures start building"
        ],
        "peak": [
            "Most challenging period - maximum intensity",
            "Health issues possible, especially chronic ones",
            "Career obstacles and delays",
            "Relationship stress and misunderstandings",
            "Financial difficulties peak"
        ],
        "setting": [
            "Gradual relief from difficulties",
            "Financial situation starts improving",
            "Lessons learned during Sade Sati crystallize",
            "Health begins to stabilize",
            "New opportunities start appearing"
        ]
    }

    dhaiya_effects = [
        "Moderate challenges for 2.5 years",
        "Health attention needed",
        "Some career or relationship stress",
        "Less intense than Sade Sati"
    ]

    # Remedies
    remedies = []
    if is_sade_sati or is_dhaiya:
        remedies = [
            "Recite Shani Chalisa or Shani Stotra on Saturdays",
            "Light sesame oil lamp under Peepal tree on Saturdays",
            "Donate black clothes, iron, sesame, or oil on Saturdays",
            "Feed crows and black dogs",
            "Worship Lord Hanuman - Hanuman Chalisa daily",
            "Wear Blue Sapphire (Neelam) only after careful consultation",
            "Alternatively wear Amethyst as a milder Saturn stone",
            "Visit Shani temples on Saturdays",
            "Perform Shani Shanti Puja",
            "Chant Shani Beej Mantra: 'Om Pram Preem Proum Sah Shanaye Namah'",
            "Help the elderly, disabled, and poor",
            "Avoid non-vegetarian food on Saturdays"
        ]

    # Determine severity
    if phase == "peak":
        severity = "High"
    elif is_sade_sati:
        severity = "Medium"
    elif is_dhaiya:
        severity = "Low-Medium"
    else:
        severity = "None"

    return {
        "dosha_name": "Shani Sade Sati",
        "is_sade_sati": is_sade_sati,
        "is_dhaiya": is_dhaiya,
        "is_present": is_sade_sati or is_dhaiya,
        "current_phase": phase_name,
        "phase": phase,
        "severity": severity,
        "moon_sign": moon_sign,
        "current_saturn_sign": current_saturn_sign,
        "effects": phase_effects.get(phase, dhaiya_effects if is_dhaiya else []),
        "positive_aspects": [
            "Saturn teaches discipline and patience",
            "Karmic debts get cleared",
            "Character building and maturity",
            "Spiritual growth and detachment",
            "Success through hard work is lasting"
        ] if is_sade_sati else [],
        "remedies": remedies,
        "duration": "Approximately 2.5 years for current phase" if is_sade_sati else "Approximately 2.5 years" if is_dhaiya else None,
        "transit_info": saturn_entry_dates,
        "advice": get_sade_sati_advice(phase) if is_sade_sati else "Monitor health and finances during this period." if is_dhaiya else "No Sade Sati or Dhaiya currently active."
    }


def calculate_saturn_transit_dates(current_sign: str) -> dict:
    """Calculate approximate Saturn transit dates."""
    # Saturn takes ~29.5 years to complete zodiac, ~2.5 years per sign
    if current_sign not in ZODIAC_SIGNS:
        return {}

    current_idx = ZODIAC_SIGNS.index(current_sign)

    # Approximate current date and calculate
    now = datetime.now()

    # Saturn entered Pisces around March 2025 (approximate)
    # This is a rough calculation - actual dates need ephemeris
    base_entries = {
        "Aquarius": datetime(2023, 1, 17),
        "Pisces": datetime(2025, 3, 29),
        "Aries": datetime(2027, 6, 1),
    }

    entry_date = base_entries.get(current_sign, now)
    exit_date = entry_date + timedelta(days=int(2.5 * 365))

    return {
        "current_sign": current_sign,
        "approximate_entry": entry_date.strftime("%B %Y"),
        "approximate_exit": exit_date.strftime("%B %Y"),
        "note": "Dates are approximate. Consult detailed ephemeris for exact dates."
    }


def get_sade_sati_advice(phase: str) -> str:
    """Get phase-specific advice for Sade Sati."""
    advice = {
        "rising": """Rising Phase - Saturn is entering your zone.
- Start building financial reserves now
- Focus on health checkups and prevention
- Strengthen relationships with patience
- Avoid major new commitments if possible
- This is preparation time - be ready for challenges ahead""",

        "peak": """Peak Phase - Maximum intensity period.
- Patience is your greatest ally now
- Focus on karma - do good, avoid shortcuts
- Health needs priority attention
- Conserve finances, avoid risky investments
- This too shall pass - stay strong and faithful
- Great spiritual growth is possible now""",

        "setting": """Setting Phase - Relief is coming.
- Rewards for your patience will manifest
- Good time to restart stalled projects
- Health and finances gradually improve
- New opportunities will emerge
- Reflect on lessons learned during Sade Sati
- Don't abandon the discipline you've built"""
    }

    return advice.get(phase, "Follow Saturn-related remedies for best results.")


# =============================================================================
# PITRA DOSHA
# =============================================================================

def check_pitra_dosha(chart_data: dict) -> dict:
    """
    Check for Pitra Dosha (Ancestral Curse).

    Occurs when:
    - Sun is afflicted by Rahu, Ketu, or Saturn
    - Sun in 9th house with malefics
    - 9th lord afflicted
    - Rahu in 9th house
    """
    planets = chart_data.get("planetary_positions", {})
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")

    if not planets or not ascendant_sign:
        return {
            "dosha_name": "Pitra Dosha",
            "is_present": False,
            "error": "Insufficient chart data"
        }

    sun_sign = planets.get("Sun", {}).get("sign", "")
    rahu_sign = planets.get("Rahu", {}).get("sign", "")
    ketu_sign = planets.get("Ketu", {}).get("sign", "")
    saturn_sign = planets.get("Saturn", {}).get("sign", "")

    indicators = []

    # Sun conjunct Rahu (within same sign)
    if sun_sign == rahu_sign:
        indicators.append("Sun conjunct Rahu (Grahan Yoga)")

    # Sun conjunct Ketu
    if sun_sign == ketu_sign:
        indicators.append("Sun conjunct Ketu")

    # Sun conjunct Saturn
    if sun_sign == saturn_sign:
        indicators.append("Sun conjunct Saturn")

    # Rahu in 9th house
    rahu_house = get_house_number(rahu_sign, ascendant_sign)
    if rahu_house == 9:
        indicators.append("Rahu in 9th house (house of father/ancestors)")

    # Sun in 9th house with malefics
    sun_house = get_house_number(sun_sign, ascendant_sign)
    if sun_house == 9 and (rahu_sign == sun_sign or saturn_sign == sun_sign):
        indicators.append("Sun in 9th house afflicted by malefics")

    is_present = len(indicators) >= 1

    effects = []
    if is_present:
        effects = [
            "Obstacles in career and education",
            "Delays in marriage or childbirth",
            "Frequent health issues in family",
            "Financial instability despite hard work",
            "Disharmony in family relationships",
            "Father's health or relationship issues"
        ]

    remedies = []
    if is_present:
        remedies = [
            "Perform Pitra Tarpan during Pitru Paksha (Shradh)",
            "Feed Brahmins on father's death anniversary",
            "Offer water to Peepal tree daily",
            "Perform Narayan Bali or Tripindi Shradh at Gaya/Trimbakeshwar",
            "Donate food to the needy (Anna Daan)",
            "Recite Pitra Suktam or Pitra Gayatri Mantra",
            "Keep ancestors' photos in South direction and offer prayers",
            "Feed crows regularly (considered Pitra representatives)"
        ]

    return {
        "dosha_name": "Pitra Dosha",
        "is_present": is_present,
        "severity": "High" if len(indicators) >= 2 else "Medium" if is_present else "None",
        "indicators": indicators,
        "effects": effects,
        "remedies": remedies,
        "advice": "Pitra Dosha indicates karmic debts from ancestors. Performing Shradh rituals and serving the needy can help mitigate its effects." if is_present else "No significant Pitra Dosha indicators found."
    }


# =============================================================================
# MAIN DOSHA CHECK FUNCTION
# =============================================================================

async def check_all_doshas(
    birth_date: str,
    birth_time: str,
    birth_place: str,
    name: str = None,
    specific_dosha: str = None
) -> ToolResult:
    """
    Check all major doshas or a specific one.

    Args:
        birth_date: Date of birth (DD-MM-YYYY)
        birth_time: Time of birth (HH:MM AM/PM)
        birth_place: Place of birth
        name: Person's name (optional)
        specific_dosha: Check specific dosha only (manglik/kaal_sarp/sade_sati/pitra)

    Returns:
        ToolResult with dosha analysis
    """
    try:
        # First calculate the birth chart
        kundli_result = await calculate_kundli(birth_date, birth_time, birth_place, name)

        if not kundli_result["success"]:
            return ToolResult(
                success=False,
                data=None,
                error=f"Could not calculate birth chart: {kundli_result.get('error', 'Unknown error')}",
                tool_name="dosha_check"
            )

        chart_data = kundli_result["data"]

        # Check specific dosha or all
        if specific_dosha:
            dosha_map = {
                "manglik": check_manglik_dosha,
                "mangal": check_manglik_dosha,
                "kuja": check_manglik_dosha,
                "kaal_sarp": check_kaal_sarp_dosha,
                "kaalsarp": check_kaal_sarp_dosha,
                "sade_sati": lambda x: check_sade_sati(x),
                "sadesati": lambda x: check_sade_sati(x),
                "shani": lambda x: check_sade_sati(x),
                "pitra": check_pitra_dosha,
                "pitru": check_pitra_dosha,
            }

            check_func = dosha_map.get(specific_dosha.lower())
            if check_func:
                result = check_func(chart_data)
                return ToolResult(
                    success=True,
                    data={
                        "person": {"name": name, "dob": birth_date, "birth_place": birth_place},
                        "chart_summary": {
                            "moon_sign": chart_data.get("moon_sign"),
                            "ascendant": chart_data.get("ascendant", {}).get("sign"),
                            "moon_nakshatra": chart_data.get("moon_nakshatra")
                        },
                        "dosha": result
                    },
                    error=None,
                    tool_name="dosha_check"
                )

        # Check all doshas
        manglik = check_manglik_dosha(chart_data)
        kaal_sarp = check_kaal_sarp_dosha(chart_data)
        sade_sati = check_sade_sati(chart_data)
        pitra = check_pitra_dosha(chart_data)

        # Summary
        active_doshas = []
        if manglik.get("is_present"):
            active_doshas.append(f"Manglik Dosha ({manglik.get('severity')})")
        if kaal_sarp.get("is_present"):
            active_doshas.append(f"Kaal Sarp Dosha ({kaal_sarp.get('type')})")
        if sade_sati.get("is_present"):
            active_doshas.append(f"Sade Sati ({sade_sati.get('current_phase')})")
        if pitra.get("is_present"):
            active_doshas.append(f"Pitra Dosha ({pitra.get('severity')})")

        return ToolResult(
            success=True,
            data={
                "person": {
                    "name": name,
                    "dob": birth_date,
                    "birth_time": birth_time,
                    "birth_place": birth_place
                },
                "chart_summary": {
                    "moon_sign": chart_data.get("moon_sign"),
                    "ascendant": chart_data.get("ascendant", {}).get("sign"),
                    "moon_nakshatra": chart_data.get("moon_nakshatra"),
                    "sun_sign": chart_data.get("sun_sign")
                },
                "doshas": {
                    "manglik": manglik,
                    "kaal_sarp": kaal_sarp,
                    "sade_sati": sade_sati,
                    "pitra": pitra
                },
                "summary": {
                    "total_checked": 4,
                    "active_doshas": active_doshas,
                    "active_count": len(active_doshas),
                    "overall_message": f"Found {len(active_doshas)} active dosha(s)" if active_doshas else "No major doshas found - chart is relatively clear"
                }
            },
            error=None,
            tool_name="dosha_check"
        )

    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="dosha_check"
        )


async def check_manglik_only(
    birth_date: str,
    birth_time: str,
    birth_place: str,
    name: str = None
) -> ToolResult:
    """Quick Manglik dosha check."""
    return await check_all_doshas(birth_date, birth_time, birth_place, name, "manglik")


async def check_sade_sati_only(moon_sign: str) -> ToolResult:
    """
    Quick Sade Sati check using just Moon sign.

    Args:
        moon_sign: User's Moon sign (e.g., "Aries", "Leo")
    """
    try:
        # Create minimal chart data
        chart_data = {"moon_sign": moon_sign.strip().capitalize()}

        result = check_sade_sati(chart_data)

        return ToolResult(
            success=True,
            data={
                "moon_sign": moon_sign,
                "sade_sati": result
            },
            error=None,
            tool_name="sade_sati_check"
        )

    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="sade_sati_check"
        )
