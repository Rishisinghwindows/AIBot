"""
Life Prediction Tool

Analyzes birth chart to predict major life events:
1. Marriage timing and spouse characteristics
2. Career progression and suitable professions
3. Children - timing and gender indication
4. Wealth accumulation and financial peaks
5. Foreign travel and settlement
6. Health outlook

Based on house analysis, planetary dashas, and transits.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from common.graph.state import ToolResult
from common.tools.astro_tool import (
    calculate_kundli,
    get_zodiac_sign,
    get_nakshatra,
    ZODIAC_SIGNS,
    NAKSHATRAS,
    RASHI_LORD,
)

# Try to import Swiss Ephemeris
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False


# =============================================================================
# CONSTANTS
# =============================================================================

# House significations
HOUSE_MEANINGS = {
    1: "Self, personality, health, physical body",
    2: "Wealth, family, speech, food, values",
    3: "Siblings, courage, short travels, communication",
    4: "Mother, home, property, vehicles, comfort",
    5: "Children, education, romance, creativity, past karma",
    6: "Enemies, debts, diseases, service, daily work",
    7: "Marriage, partnerships, business, spouse",
    8: "Longevity, transformation, inheritance, occult",
    9: "Father, luck, higher education, religion, long travels",
    10: "Career, reputation, government, authority",
    11: "Income, gains, fulfillment of desires, friends",
    12: "Losses, expenses, foreign lands, moksha, hidden enemies"
}

# Karaka planets for different life areas
KARAKAS = {
    "marriage": ["Venus", "Jupiter"],  # Venus for love, Jupiter for husband
    "career": ["Saturn", "Sun", "Mercury", "Mars"],
    "children": ["Jupiter"],
    "wealth": ["Jupiter", "Venus"],
    "foreign": ["Rahu", "Ketu", "Saturn"],
    "health": ["Sun", "Moon", "Mars"],
}

# Planet strengths
PLANET_DIGNITY = {
    "Sun": {"exalted": "Aries", "debilitated": "Libra", "own": ["Leo"]},
    "Moon": {"exalted": "Taurus", "debilitated": "Scorpio", "own": ["Cancer"]},
    "Mars": {"exalted": "Capricorn", "debilitated": "Cancer", "own": ["Aries", "Scorpio"]},
    "Mercury": {"exalted": "Virgo", "debilitated": "Pisces", "own": ["Gemini", "Virgo"]},
    "Jupiter": {"exalted": "Cancer", "debilitated": "Capricorn", "own": ["Sagittarius", "Pisces"]},
    "Venus": {"exalted": "Pisces", "debilitated": "Virgo", "own": ["Taurus", "Libra"]},
    "Saturn": {"exalted": "Libra", "debilitated": "Aries", "own": ["Capricorn", "Aquarius"]},
}

# Dasha sequence (Vimshottari)
DASHA_SEQUENCE = ["Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus"]
DASHA_YEARS = {"Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17, "Ketu": 7, "Venus": 20}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_house_number(planet_sign: str, ascendant_sign: str) -> int:
    """Calculate house number from ascendant."""
    if planet_sign not in ZODIAC_SIGNS or ascendant_sign not in ZODIAC_SIGNS:
        return 0
    planet_idx = ZODIAC_SIGNS.index(planet_sign)
    asc_idx = ZODIAC_SIGNS.index(ascendant_sign)
    return ((planet_idx - asc_idx) % 12) + 1


def get_planet_dignity(planet: str, sign: str) -> str:
    """Determine planet's dignity in a sign."""
    if planet not in PLANET_DIGNITY:
        return "neutral"
    dignity = PLANET_DIGNITY[planet]
    if sign == dignity.get("exalted"):
        return "exalted"
    elif sign == dignity.get("debilitated"):
        return "debilitated"
    elif sign in dignity.get("own", []):
        return "own_sign"
    return "neutral"


def calculate_current_dasha(birth_date: str, moon_nakshatra: str) -> Dict[str, Any]:
    """Calculate current Vimshottari Mahadasha and Antardasha."""
    try:
        from common.tools.astro_tool import parse_date
        dt = parse_date(birth_date)
        if not dt:
            return {}

        # Find nakshatra lord
        nakshatra_lords = {
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

        birth_lord = nakshatra_lords.get(moon_nakshatra, "Moon")

        # Find starting dasha
        start_idx = DASHA_SEQUENCE.index(birth_lord)

        # Calculate years elapsed since birth
        now = datetime.now()
        years_elapsed = (now - dt).days / 365.25

        # Find current dasha
        total_years = 0
        current_idx = start_idx
        for _ in range(len(DASHA_SEQUENCE) * 2):  # Max 2 cycles
            planet = DASHA_SEQUENCE[current_idx % len(DASHA_SEQUENCE)]
            dasha_duration = DASHA_YEARS[planet]

            if total_years + dasha_duration > years_elapsed:
                # Found current Mahadasha
                years_in_dasha = years_elapsed - total_years
                remaining_years = dasha_duration - years_in_dasha

                # Calculate end date
                end_date = now + timedelta(days=int(remaining_years * 365.25))

                return {
                    "mahadasha": planet,
                    "mahadasha_duration": dasha_duration,
                    "years_completed": round(years_in_dasha, 1),
                    "years_remaining": round(remaining_years, 1),
                    "end_date": end_date.strftime("%B %Y"),
                    "next_dasha": DASHA_SEQUENCE[(current_idx + 1) % len(DASHA_SEQUENCE)]
                }

            total_years += dasha_duration
            current_idx += 1

        return {}

    except Exception as e:
        return {"error": str(e)}


def analyze_house(chart_data: dict, house_num: int) -> Dict[str, Any]:
    """Analyze a specific house for predictions."""
    planets = chart_data.get("planetary_positions", {})
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "Aries")

    # Find house sign
    house_sign_idx = (ZODIAC_SIGNS.index(ascendant_sign) + house_num - 1) % 12
    house_sign = ZODIAC_SIGNS[house_sign_idx]
    house_lord = RASHI_LORD.get(house_sign, "Unknown")

    # Find planets in this house
    planets_in_house = []
    for planet_name, planet_info in planets.items():
        planet_sign = planet_info.get("sign", "")
        planet_house = get_house_number(planet_sign, ascendant_sign)
        if planet_house == house_num:
            dignity = get_planet_dignity(planet_name, planet_sign)
            planets_in_house.append({
                "planet": planet_name,
                "sign": planet_sign,
                "dignity": dignity
            })

    # Find house lord position
    house_lord_info = planets.get(house_lord, {})
    house_lord_sign = house_lord_info.get("sign", "")
    house_lord_house = get_house_number(house_lord_sign, ascendant_sign)
    house_lord_dignity = get_planet_dignity(house_lord, house_lord_sign)

    return {
        "house_number": house_num,
        "house_sign": house_sign,
        "house_lord": house_lord,
        "house_lord_position": {
            "sign": house_lord_sign,
            "house": house_lord_house,
            "dignity": house_lord_dignity
        },
        "planets_in_house": planets_in_house,
        "is_strong": len(planets_in_house) > 0 or house_lord_dignity in ["exalted", "own_sign"]
    }


# =============================================================================
# MARRIAGE PREDICTION
# =============================================================================

def predict_marriage(chart_data: dict) -> Dict[str, Any]:
    """Predict marriage timing and spouse characteristics."""
    # Analyze 7th house (marriage)
    house_7 = analyze_house(chart_data, 7)

    # Check Venus (karaka for love/marriage)
    planets = chart_data.get("planetary_positions", {})
    venus_info = planets.get("Venus", {})
    venus_sign = venus_info.get("sign", "")
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")
    venus_house = get_house_number(venus_sign, ascendant_sign)
    venus_dignity = get_planet_dignity("Venus", venus_sign)

    # For female charts, Jupiter is karaka for husband
    jupiter_info = planets.get("Jupiter", {})
    jupiter_sign = jupiter_info.get("sign", "")
    jupiter_house = get_house_number(jupiter_sign, ascendant_sign)

    # Analyze factors
    marriage_factors = {
        "7th_house_strong": house_7["is_strong"],
        "venus_well_placed": venus_dignity in ["exalted", "own_sign"] or venus_house in [1, 4, 5, 7, 9, 11],
        "jupiter_well_placed": jupiter_house in [1, 4, 5, 7, 9, 11],
        "7th_lord_strong": house_7["house_lord_position"]["dignity"] in ["exalted", "own_sign"]
    }

    # Determine timing indication
    strong_factors = sum(1 for v in marriage_factors.values() if v)

    if strong_factors >= 3:
        timing = "Marriage is likely in favorable planetary periods. Generally between 24-28 years."
    elif strong_factors >= 2:
        timing = "Marriage timing is average. May happen between 26-30 years."
    else:
        timing = "Some delays possible in marriage. May happen after 28-32 years. Consider remedies."

    # Spouse direction (based on 7th sign)
    direction_map = {
        "Aries": "East", "Taurus": "South", "Gemini": "West", "Cancer": "North",
        "Leo": "East", "Virgo": "South", "Libra": "West", "Scorpio": "North",
        "Sagittarius": "East", "Capricorn": "South", "Aquarius": "West", "Pisces": "North"
    }
    spouse_direction = direction_map.get(house_7["house_sign"], "Unknown")

    # Spouse characteristics based on 7th sign
    spouse_traits = {
        "Aries": "Active, independent, leadership qualities",
        "Taurus": "Artistic, stable, loves comfort and luxury",
        "Gemini": "Intelligent, communicative, versatile",
        "Cancer": "Nurturing, emotional, family-oriented",
        "Leo": "Confident, generous, proud",
        "Virgo": "Analytical, helpful, detail-oriented",
        "Libra": "Charming, diplomatic, beauty-conscious",
        "Scorpio": "Intense, passionate, secretive",
        "Sagittarius": "Adventurous, philosophical, optimistic",
        "Capricorn": "Ambitious, disciplined, practical",
        "Aquarius": "Innovative, independent, humanitarian",
        "Pisces": "Spiritual, creative, compassionate"
    }

    return {
        "prediction_type": "Marriage",
        "7th_house_analysis": house_7,
        "venus_position": {
            "sign": venus_sign,
            "house": venus_house,
            "dignity": venus_dignity
        },
        "marriage_factors": marriage_factors,
        "timing_indication": timing,
        "spouse_characteristics": spouse_traits.get(house_7["house_sign"], ""),
        "spouse_direction": spouse_direction,
        "advice": "For more accurate timing, consider current Dasha period and Jupiter/Venus transits."
    }


# =============================================================================
# CAREER PREDICTION
# =============================================================================

def predict_career(chart_data: dict) -> Dict[str, Any]:
    """Predict career path and suitable professions."""
    # Analyze 10th house (career)
    house_10 = analyze_house(chart_data, 10)

    # Also check 6th house (daily work) and 2nd house (income)
    house_6 = analyze_house(chart_data, 6)
    house_2 = analyze_house(chart_data, 2)

    # Get ascendant for overall direction
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")

    # Career suggestions based on 10th house sign
    career_by_sign = {
        "Aries": ["Military, Police, Sports, Entrepreneurship, Surgery"],
        "Taurus": ["Banking, Finance, Arts, Agriculture, Real Estate"],
        "Gemini": ["Media, Writing, Communication, Teaching, Trading"],
        "Cancer": ["Hospitality, Nursing, Real Estate, Food Industry"],
        "Leo": ["Government, Politics, Entertainment, Management"],
        "Virgo": ["Healthcare, Accounting, Analysis, Quality Control"],
        "Libra": ["Law, Diplomacy, Fashion, Interior Design"],
        "Scorpio": ["Research, Investigation, Insurance, Medicine"],
        "Sagittarius": ["Law, Teaching, Travel, Publishing, Religion"],
        "Capricorn": ["Administration, Mining, Construction, Politics"],
        "Aquarius": ["Technology, Science, Social Work, Aviation"],
        "Pisces": ["Arts, Healing, Spirituality, Marine, Film"]
    }

    # Check dominant planets for career
    planets = chart_data.get("planetary_positions", {})
    planet_careers = {
        "Sun": "Government, Authority positions, Medicine",
        "Moon": "Public dealing, Hospitality, Psychology",
        "Mars": "Military, Engineering, Sports, Surgery",
        "Mercury": "Communication, Trading, Writing, IT",
        "Jupiter": "Teaching, Law, Finance, Consulting",
        "Venus": "Arts, Entertainment, Luxury goods, Fashion",
        "Saturn": "Labor, Mining, Agriculture, Real Estate",
        "Rahu": "Foreign careers, Technology, Politics",
        "Ketu": "Spirituality, Research, Alternative healing"
    }

    # Identify strong planets
    strong_planets = []
    for planet_name, planet_info in planets.items():
        sign = planet_info.get("sign", "")
        dignity = get_planet_dignity(planet_name, sign) if planet_name in PLANET_DIGNITY else "neutral"
        house = get_house_number(sign, ascendant_sign)

        if dignity in ["exalted", "own_sign"] or house in [1, 4, 7, 10]:
            strong_planets.append({
                "planet": planet_name,
                "career_indication": planet_careers.get(planet_name, ""),
                "reason": f"{dignity} in house {house}"
            })

    # Career timing
    career_analysis = {
        "10th_lord_strong": house_10["house_lord_position"]["dignity"] in ["exalted", "own_sign"],
        "planets_in_10th": len(house_10["planets_in_house"]) > 0,
        "2nd_house_strong": house_2["is_strong"]
    }

    strong_factors = sum(1 for v in career_analysis.values() if v)

    if strong_factors >= 2:
        career_outlook = "Excellent career prospects. Success in chosen field likely."
    elif strong_factors >= 1:
        career_outlook = "Good career potential with some challenges. Perseverance needed."
    else:
        career_outlook = "Career may require extra effort. Consider building skills and networking."

    return {
        "prediction_type": "Career",
        "10th_house_analysis": house_10,
        "suitable_careers": career_by_sign.get(house_10["house_sign"], ["General professions"]),
        "strong_planets_indication": strong_planets[:3],  # Top 3
        "career_factors": career_analysis,
        "career_outlook": career_outlook,
        "advice": "Best career timing during favorable Dasha of 10th lord or planets in 10th house."
    }


# =============================================================================
# CHILDREN PREDICTION
# =============================================================================

def predict_children(chart_data: dict) -> Dict[str, Any]:
    """Predict about children timing and characteristics."""
    # Analyze 5th house (children, creativity)
    house_5 = analyze_house(chart_data, 5)

    # Check Jupiter (karaka for children)
    planets = chart_data.get("planetary_positions", {})
    jupiter_info = planets.get("Jupiter", {})
    jupiter_sign = jupiter_info.get("sign", "")
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")
    jupiter_house = get_house_number(jupiter_sign, ascendant_sign)
    jupiter_dignity = get_planet_dignity("Jupiter", jupiter_sign)

    # Analyze factors
    children_factors = {
        "5th_house_strong": house_5["is_strong"],
        "jupiter_well_placed": jupiter_dignity in ["exalted", "own_sign"] or jupiter_house in [1, 2, 5, 9, 11],
        "5th_lord_strong": house_5["house_lord_position"]["dignity"] in ["exalted", "own_sign"],
        "no_malefics_in_5th": not any(p["planet"] in ["Saturn", "Rahu", "Ketu"] for p in house_5["planets_in_house"])
    }

    strong_factors = sum(1 for v in children_factors.values() if v)

    if strong_factors >= 3:
        timing = "Children are indicated in favorable periods. Generally possible between 2-5 years of marriage."
        blessing = "Good fortune through children is indicated."
    elif strong_factors >= 2:
        timing = "Average indications. Children possible with some wait period."
        blessing = "Children will bring mixed experiences."
    else:
        timing = "Some delays or challenges possible. Consider remedies for Jupiter and 5th lord."
        blessing = "Remedies recommended for smooth childbirth."

    # Number indication based on 5th sign and planets
    number_indication = "1-2 children likely" if strong_factors >= 2 else "1-2 children with effort"

    return {
        "prediction_type": "Children",
        "5th_house_analysis": house_5,
        "jupiter_position": {
            "sign": jupiter_sign,
            "house": jupiter_house,
            "dignity": jupiter_dignity
        },
        "children_factors": children_factors,
        "timing_indication": timing,
        "number_indication": number_indication,
        "blessing": blessing,
        "advice": "Worship Jupiter (Brihaspati) and perform Santan Gopal puja for blessings."
    }


# =============================================================================
# WEALTH PREDICTION
# =============================================================================

def predict_wealth(chart_data: dict) -> Dict[str, Any]:
    """Predict wealth accumulation potential."""
    # Analyze 2nd house (wealth), 11th house (gains), 9th house (luck)
    house_2 = analyze_house(chart_data, 2)
    house_11 = analyze_house(chart_data, 11)
    house_9 = analyze_house(chart_data, 9)

    # Check Jupiter (karaka for wealth)
    planets = chart_data.get("planetary_positions", {})
    jupiter_info = planets.get("Jupiter", {})
    venus_info = planets.get("Venus", {})
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")

    jupiter_house = get_house_number(jupiter_info.get("sign", ""), ascendant_sign)
    venus_house = get_house_number(venus_info.get("sign", ""), ascendant_sign)

    # Dhana Yogas check
    dhana_yoga_present = False
    yoga_description = ""

    # Check for Lakshmi Yoga (Venus in own/exalted in kendra/trikona)
    venus_dignity = get_planet_dignity("Venus", venus_info.get("sign", ""))
    if venus_dignity in ["exalted", "own_sign"] and venus_house in [1, 4, 5, 7, 9, 10]:
        dhana_yoga_present = True
        yoga_description = "Lakshmi Yoga present - Venus well placed"

    # Check 2nd-11th lords connection
    if house_2["house_lord_position"]["house"] == 11 or house_11["house_lord_position"]["house"] == 2:
        dhana_yoga_present = True
        yoga_description = "2nd-11th lord connection - Wealth accumulation yoga"

    wealth_factors = {
        "2nd_house_strong": house_2["is_strong"],
        "11th_house_strong": house_11["is_strong"],
        "9th_house_strong": house_9["is_strong"],
        "dhana_yoga": dhana_yoga_present,
        "jupiter_well_placed": jupiter_house in [1, 2, 5, 9, 11]
    }

    strong_factors = sum(1 for v in wealth_factors.values() if v)

    if strong_factors >= 4:
        wealth_outlook = "Excellent wealth potential. Multiple sources of income likely."
        accumulation = "Significant wealth accumulation possible, especially after mid-30s."
    elif strong_factors >= 2:
        wealth_outlook = "Good financial prospects with consistent effort."
        accumulation = "Steady wealth building through career and savings."
    else:
        wealth_outlook = "Financial growth requires extra effort and planning."
        accumulation = "Focus on skill development and multiple income sources."

    return {
        "prediction_type": "Wealth",
        "2nd_house_analysis": house_2,
        "11th_house_analysis": house_11,
        "wealth_factors": wealth_factors,
        "dhana_yoga": yoga_description if dhana_yoga_present else "No major Dhana Yoga",
        "wealth_outlook": wealth_outlook,
        "accumulation_period": accumulation,
        "advice": "Worship Lakshmi and donate on Fridays for wealth blessings."
    }


# =============================================================================
# FOREIGN SETTLEMENT PREDICTION
# =============================================================================

def predict_foreign(chart_data: dict) -> Dict[str, Any]:
    """Predict foreign travel and settlement possibilities."""
    # Analyze 12th house (foreign lands), 9th house (long travels), 4th house (home)
    house_12 = analyze_house(chart_data, 12)
    house_9 = analyze_house(chart_data, 9)
    house_4 = analyze_house(chart_data, 4)

    planets = chart_data.get("planetary_positions", {})
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")

    # Check Rahu (foreign karaka)
    rahu_info = planets.get("Rahu", {})
    rahu_house = get_house_number(rahu_info.get("sign", ""), ascendant_sign)

    # Check for foreign yoga
    foreign_indicators = []

    # Rahu in 1, 4, 7, 9, 12 indicates foreign connection
    if rahu_house in [1, 4, 7, 9, 12]:
        foreign_indicators.append(f"Rahu in {rahu_house}th house - strong foreign connection")

    # 4th lord in 12th or vice versa
    if house_4["house_lord_position"]["house"] == 12:
        foreign_indicators.append("4th lord in 12th - indicates living away from birthplace")

    if house_12["house_lord_position"]["house"] in [1, 4, 9, 10]:
        foreign_indicators.append("12th lord well placed - foreign gains possible")

    # Planets in 12th house
    for p in house_12["planets_in_house"]:
        foreign_indicators.append(f"{p['planet']} in 12th house - foreign connection")

    foreign_factors = {
        "rahu_well_placed": rahu_house in [1, 4, 7, 9, 12],
        "12th_house_active": len(house_12["planets_in_house"]) > 0,
        "4th_12th_connection": house_4["house_lord_position"]["house"] == 12 or house_12["house_lord_position"]["house"] == 4,
        "9th_house_strong": house_9["is_strong"]
    }

    strong_factors = sum(1 for v in foreign_factors.values() if v)

    if strong_factors >= 3:
        foreign_outlook = "Strong foreign connection. Foreign travel/settlement highly likely."
        timing = "May happen during Rahu Dasha or transits of Rahu/Saturn over 4th/9th/12th houses."
    elif strong_factors >= 2:
        foreign_outlook = "Moderate foreign possibilities. May involve work or short stays."
        timing = "Foreign opportunities possible during favorable planetary periods."
    else:
        foreign_outlook = "Limited foreign indications. May have occasional foreign travel."
        timing = "Foreign travel possible during Rahu or 12th lord periods."

    return {
        "prediction_type": "Foreign",
        "12th_house_analysis": house_12,
        "9th_house_analysis": house_9,
        "rahu_position": {"house": rahu_house, "sign": rahu_info.get("sign", "")},
        "foreign_indicators": foreign_indicators,
        "foreign_factors": foreign_factors,
        "foreign_outlook": foreign_outlook,
        "timing": timing,
        "advice": "Strengthen Rahu if foreign travel is desired. Wear Gomed after consultation."
    }


# =============================================================================
# HEALTH PREDICTION
# =============================================================================

def predict_health(chart_data: dict) -> Dict[str, Any]:
    """Predict health outlook and potential concerns."""
    # Analyze 1st house (body), 6th house (diseases), 8th house (chronic issues)
    house_1 = analyze_house(chart_data, 1)
    house_6 = analyze_house(chart_data, 6)
    house_8 = analyze_house(chart_data, 8)

    planets = chart_data.get("planetary_positions", {})
    ascendant_sign = chart_data.get("ascendant", {}).get("sign", "")

    # Check Sun (vitality) and Moon (mind)
    sun_info = planets.get("Sun", {})
    moon_info = planets.get("Moon", {})

    sun_dignity = get_planet_dignity("Sun", sun_info.get("sign", ""))
    moon_dignity = get_planet_dignity("Moon", moon_info.get("sign", ""))

    # Health concerns by sign
    health_by_sign = {
        "Aries": "Head, brain, nervous system",
        "Taurus": "Throat, neck, thyroid",
        "Gemini": "Lungs, arms, shoulders",
        "Cancer": "Chest, stomach, digestion",
        "Leo": "Heart, spine, back",
        "Virgo": "Intestines, digestion, nerves",
        "Libra": "Kidneys, lower back",
        "Scorpio": "Reproductive system, urinary",
        "Sagittarius": "Hips, thighs, liver",
        "Capricorn": "Knees, bones, joints",
        "Aquarius": "Ankles, circulation",
        "Pisces": "Feet, immune system"
    }

    vulnerable_area = health_by_sign.get(ascendant_sign, "General health")

    # Check for health yogas
    health_concerns = []

    # Malefics in 6th without benefic aspect
    malefics_in_6 = [p for p in house_6["planets_in_house"] if p["planet"] in ["Saturn", "Mars", "Rahu", "Ketu"]]
    if malefics_in_6:
        health_concerns.append("May face health challenges - need preventive care")

    # Weak Sun indicates vitality issues
    if sun_dignity == "debilitated":
        health_concerns.append("Sun debilitated - take care of heart and eyesight")

    # Weak Moon indicates mental health
    if moon_dignity == "debilitated":
        health_concerns.append("Moon afflicted - focus on mental wellness")

    health_factors = {
        "ascendant_strong": house_1["is_strong"],
        "sun_strong": sun_dignity in ["exalted", "own_sign"],
        "moon_strong": moon_dignity in ["exalted", "own_sign"],
        "6th_house_manageable": len(house_6["planets_in_house"]) < 2
    }

    strong_factors = sum(1 for v in health_factors.values() if v)

    if strong_factors >= 3:
        health_outlook = "Good overall health constitution. Maintain regular checkups."
    elif strong_factors >= 2:
        health_outlook = "Average health. Be mindful of diet and lifestyle."
    else:
        health_outlook = "Health needs attention. Follow preventive healthcare strictly."

    return {
        "prediction_type": "Health",
        "ascendant_analysis": house_1,
        "vulnerable_areas": vulnerable_area,
        "health_factors": health_factors,
        "health_concerns": health_concerns if health_concerns else ["No major concerns indicated"],
        "health_outlook": health_outlook,
        "advice": "Strengthen Sun and Moon through yoga and meditation. Regular exercise recommended."
    }


# =============================================================================
# MAIN PREDICTION FUNCTION
# =============================================================================

async def get_life_prediction(
    birth_date: str,
    birth_time: str,
    birth_place: str,
    prediction_type: str = "general",
    name: str = None,
    question: str = None
) -> ToolResult:
    """
    Get life prediction based on birth chart analysis.

    Args:
        birth_date: Date of birth (DD-MM-YYYY)
        birth_time: Time of birth (HH:MM AM/PM)
        birth_place: Place of birth
        prediction_type: marriage/career/children/wealth/foreign/health/general
        name: Person's name (optional)
        question: Specific question asked (optional)

    Returns:
        ToolResult with prediction data
    """
    try:
        # Calculate birth chart
        kundli_result = await calculate_kundli(birth_date, birth_time, birth_place, name)

        if not kundli_result["success"]:
            return ToolResult(
                success=False,
                data=None,
                error=f"Could not calculate birth chart: {kundli_result.get('error', 'Unknown error')}",
                tool_name="life_prediction"
            )

        chart_data = kundli_result["data"]

        # Calculate current dasha
        current_dasha = calculate_current_dasha(birth_date, chart_data.get("moon_nakshatra", "Ashwini"))

        # Get specific prediction
        prediction_map = {
            "marriage": predict_marriage,
            "career": predict_career,
            "children": predict_children,
            "wealth": predict_wealth,
            "foreign": predict_foreign,
            "health": predict_health
        }

        if prediction_type in prediction_map:
            prediction = prediction_map[prediction_type](chart_data)
        else:
            # General prediction - include all
            prediction = {
                "prediction_type": "General Life Reading",
                "marriage": predict_marriage(chart_data),
                "career": predict_career(chart_data),
                "children": predict_children(chart_data),
                "wealth": predict_wealth(chart_data),
                "foreign": predict_foreign(chart_data),
                "health": predict_health(chart_data)
            }

        return ToolResult(
            success=True,
            data={
                "person": {
                    "name": name,
                    "birth_date": birth_date,
                    "birth_time": birth_time,
                    "birth_place": birth_place
                },
                "chart_summary": {
                    "ascendant": chart_data.get("ascendant", {}).get("sign"),
                    "moon_sign": chart_data.get("moon_sign"),
                    "sun_sign": chart_data.get("sun_sign"),
                    "moon_nakshatra": chart_data.get("moon_nakshatra")
                },
                "current_dasha": current_dasha,
                "prediction": prediction,
                "question": question
            },
            error=None,
            tool_name="life_prediction"
        )

    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="life_prediction"
        )
