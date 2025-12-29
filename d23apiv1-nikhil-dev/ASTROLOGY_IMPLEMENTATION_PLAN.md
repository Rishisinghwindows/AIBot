# Astrology Features - Implementation Plan

## Priority Matrix

| Priority | Feature | User Demand | Complexity | Business Value |
|----------|---------|-------------|------------|----------------|
| P0 | Life Predictions (Marriage, Career, Children) | Very High | Medium | Very High |
| P0 | Doshas Detection (Manglik, Kaal Sarp, Sade Sati) | Very High | Medium | Very High |
| P1 | Remedies Engine (Gemstones, Mantras, Pujas) | High | Medium | High |
| P1 | Muhurta Finder (Auspicious Dates) | High | High | High |
| P1 | Panchang (Daily Calendar) | High | Low | Medium |
| P2 | Dasha & Transit Analysis | Medium | High | Medium |
| P2 | Vastu Basics | Medium | Low | Medium |
| P3 | Advanced Yogas Detection | Low | High | Low |
| P3 | Name Suggestion (Numerology) | Low | Medium | Low |

---

## Phase 1: Life Predictions Engine (P0)
**Timeline: Core feature - implement first**

### 1.1 New Intent: `life_prediction`

**Query Types to Handle:**
```
- "When will I get married?"
- "Will I get a job?"
- "When will I have children?"
- "Will my business succeed?"
- "Will I go abroad?"
- "How is my career this year?"
- "Love life prediction"
- "Financial future"
```

**Implementation:**

#### A. Add to `bot/state.py`:
```python
# Add to IntentType
"life_prediction",
```

#### B. Add to `bot/nodes/intent.py`:
```python
# Life prediction keywords
life_prediction_keywords = [
    "when will i", "will i get", "will i have", "will my",
    "marriage prediction", "career prediction", "job prediction",
    "love prediction", "child prediction", "baby prediction",
    "financial prediction", "wealth prediction", "foreign settlement",
    "go abroad", "settle abroad", "get married", "find love",
    "get job", "get promotion", "have baby", "have children"
]

life_prediction_topics = [
    "marriage", "career", "job", "love", "relationship",
    "children", "baby", "money", "wealth", "abroad", "foreign",
    "business", "promotion", "health", "education"
]
```

#### C. Create `bot/nodes/life_prediction_node.py`:
```python
"""
Life Prediction Node

Handles questions about:
- Marriage timing & spouse
- Career & job predictions
- Children & family
- Wealth & finance
- Foreign travel/settlement
- Health outlook
- Education & exams
"""

async def handle_life_prediction(state: BotState) -> dict:
    entities = state.get("extracted_entities", {})
    topic = entities.get("prediction_topic", "general")
    user_dob = entities.get("user_dob", "")

    # If no DOB, ask for it
    if not user_dob:
        return {
            "response_text": "*Life Prediction*\n\nTo give you accurate predictions, I need your birth details:\n\n"
                           "Please share:\n"
                           "- Date of birth (e.g., 15-08-1990)\n"
                           "- Time of birth (e.g., 10:30 AM)\n"
                           "- Place of birth (e.g., Delhi)\n\n"
                           "*Example:* \"My DOB is 15-08-1990, 10:30 AM, Delhi. When will I get married?\"",
            "response_type": "text",
            "should_fallback": False,
        }

    # Generate prediction based on topic
    result = await generate_life_prediction(
        topic=topic,
        birth_date=user_dob,
        birth_time=entities.get("user_time", "12:00"),
        birth_place=entities.get("user_place", "Delhi"),
        question=state.get("current_query", "")
    )

    return {
        "tool_result": result,
        "response_text": result["data"]["prediction"],
        "response_type": "text",
        "should_fallback": False,
    }
```

#### D. Create `bot/tools/life_prediction_tool.py`:
```python
"""
Life Prediction Tool

Uses birth chart analysis + AI to generate predictions for:
- 7th house: Marriage, partnerships
- 10th house: Career, profession
- 5th house: Children, creativity
- 2nd/11th house: Wealth, income
- 9th/12th house: Foreign travel
- 6th house: Health, enemies
- 4th house: Education, home
"""

from bot.tools.astro_tool import calculate_kundli, ZODIAC_SIGNS, NAKSHATRAS

# House significations
HOUSE_MEANINGS = {
    1: "Self, personality, health, beginnings",
    2: "Wealth, family, speech, food",
    3: "Siblings, courage, short travels, communication",
    4: "Mother, home, education, vehicles, peace",
    5: "Children, creativity, romance, intelligence",
    6: "Enemies, diseases, debts, service",
    7: "Marriage, partnerships, business, spouse",
    8: "Longevity, obstacles, inheritance, occult",
    9: "Father, luck, higher education, foreign travel",
    10: "Career, profession, fame, authority",
    11: "Gains, income, friends, aspirations",
    12: "Losses, expenses, foreign settlement, moksha"
}

# Topic to house mapping
TOPIC_HOUSE_MAP = {
    "marriage": [7, 2, 8],      # 7th primary, 2nd family, 8th longevity of marriage
    "career": [10, 6, 2],       # 10th career, 6th service, 2nd income
    "job": [10, 6, 11],         # 10th profession, 6th service, 11th gains
    "children": [5, 9, 2],      # 5th children, 9th fortune, 2nd family
    "wealth": [2, 11, 9],       # 2nd wealth, 11th gains, 9th luck
    "abroad": [9, 12, 7],       # 9th foreign travel, 12th foreign lands, 7th partnerships
    "health": [1, 6, 8],        # 1st self, 6th diseases, 8th longevity
    "education": [4, 5, 9],     # 4th education, 5th intelligence, 9th higher learning
    "love": [5, 7, 11],         # 5th romance, 7th partnership, 11th desires
    "business": [7, 10, 11],    # 7th partnerships, 10th profession, 11th gains
}

async def generate_life_prediction(
    topic: str,
    birth_date: str,
    birth_time: str,
    birth_place: str,
    question: str
) -> ToolResult:
    """Generate life prediction based on birth chart analysis."""

    # Calculate birth chart
    kundli_result = await calculate_kundli(birth_date, birth_time, birth_place)

    if not kundli_result["success"]:
        return kundli_result

    chart_data = kundli_result["data"]

    # Get relevant houses for the topic
    relevant_houses = TOPIC_HOUSE_MAP.get(topic, [1, 7, 10])

    # Analyze planetary positions in relevant houses
    analysis = analyze_houses_for_topic(chart_data, relevant_houses, topic)

    # Use AI to generate natural language prediction
    prediction = await generate_ai_prediction(
        topic=topic,
        question=question,
        chart_analysis=analysis,
        moon_sign=chart_data["moon_sign"],
        moon_nakshatra=chart_data["moon_nakshatra"],
        ascendant=chart_data["ascendant"]["sign"]
    )

    return ToolResult(
        success=True,
        data={
            "topic": topic,
            "prediction": prediction,
            "chart_summary": analysis,
            "favorable_periods": get_favorable_periods(chart_data, topic),
            "remedies": get_topic_remedies(chart_data, topic)
        },
        error=None,
        tool_name="life_prediction"
    )
```

---

## Phase 2: Doshas Detection (P0)
**Most asked questions: "Am I Manglik?", "Sade Sati effects"**

### 2.1 New Intent: `dosha_check`

**Query Types:**
```
- "Am I Manglik?"
- "Check Manglik dosha"
- "Do I have Kaal Sarp dosha?"
- "Shani Sade Sati check"
- "Am I in Sade Sati?"
- "When will Sade Sati end?"
- "Pitra dosha check"
- "Any dosha in my kundli?"
```

### 2.2 Create `bot/tools/dosha_tool.py`:

```python
"""
Dosha Detection Tool

Detects major Vedic astrology doshas:
1. Manglik/Mangal Dosha - Mars in 1, 4, 7, 8, 12 from Lagna/Moon
2. Kaal Sarp Dosha - All planets between Rahu-Ketu axis
3. Shani Sade Sati - Saturn transiting 12th, 1st, 2nd from Moon
4. Pitra Dosha - Sun afflicted by Rahu/Ketu/Saturn
5. Nadi Dosha - Same Nadi in matching (for compatibility)
6. Grahan Dosha - Born during eclipse
"""

# Manglik Dosha Rules
MANGLIK_HOUSES = [1, 4, 7, 8, 12]  # Houses where Mars causes Manglik

def check_manglik_dosha(chart_data: dict) -> dict:
    """
    Check for Manglik Dosha.

    Manglik dosha occurs when Mars is placed in:
    - 1st, 4th, 7th, 8th, or 12th house from Lagna
    - 1st, 4th, 7th, 8th, or 12th house from Moon

    Cancellation conditions:
    - Mars in own sign (Aries, Scorpio)
    - Mars in exaltation (Capricorn)
    - Jupiter aspects Mars
    - Venus in 7th house
    - Mars-Mars in both charts (for matching)
    """

    mars_position = chart_data["planetary_positions"].get("Mars", {})
    mars_house_from_lagna = get_house_from_lagna(mars_position, chart_data)
    mars_house_from_moon = get_house_from_moon(mars_position, chart_data)

    is_manglik_from_lagna = mars_house_from_lagna in MANGLIK_HOUSES
    is_manglik_from_moon = mars_house_from_moon in MANGLIK_HOUSES

    # Check cancellation
    cancellation_reasons = []
    mars_sign = mars_position.get("sign", "")

    if mars_sign in ["Aries", "Scorpio"]:
        cancellation_reasons.append("Mars in own sign")
    if mars_sign == "Capricorn":
        cancellation_reasons.append("Mars in exaltation")

    severity = "None"
    if is_manglik_from_lagna and is_manglik_from_moon:
        severity = "High" if not cancellation_reasons else "Cancelled"
    elif is_manglik_from_lagna or is_manglik_from_moon:
        severity = "Partial" if not cancellation_reasons else "Cancelled"

    return {
        "dosha_name": "Manglik Dosha",
        "is_present": is_manglik_from_lagna or is_manglik_from_moon,
        "severity": severity,
        "from_lagna": is_manglik_from_lagna,
        "from_moon": is_manglik_from_moon,
        "mars_house_lagna": mars_house_from_lagna,
        "mars_house_moon": mars_house_from_moon,
        "cancellation": cancellation_reasons,
        "effects": get_manglik_effects(severity),
        "remedies": get_manglik_remedies() if severity in ["High", "Partial"] else []
    }


def check_kaal_sarp_dosha(chart_data: dict) -> dict:
    """
    Check for Kaal Sarp Dosha.

    Occurs when all 7 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn)
    are hemmed between Rahu and Ketu.

    Types based on Rahu's house:
    - Anant (1st), Kulik (2nd), Vasuki (3rd), Shankpal (4th)
    - Padma (5th), Mahapadma (6th), Takshak (7th), Karkotak (8th)
    - Shankachood (9th), Ghatak (10th), Vishdhar (11th), Sheshnag (12th)
    """

    rahu_deg = chart_data["planetary_positions"].get("Rahu", {}).get("degree", 0)
    ketu_deg = chart_data["planetary_positions"].get("Ketu", {}).get("degree", 0)

    # Check if all planets are between Rahu and Ketu
    planets_to_check = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    all_between = True

    for planet in planets_to_check:
        planet_deg = chart_data["planetary_positions"].get(planet, {}).get("degree", 0)
        if not is_between_rahu_ketu(planet_deg, rahu_deg, ketu_deg):
            all_between = False
            break

    if all_between:
        kaal_sarp_type = get_kaal_sarp_type(rahu_deg)
        return {
            "dosha_name": "Kaal Sarp Dosha",
            "is_present": True,
            "type": kaal_sarp_type,
            "severity": "High",
            "effects": get_kaal_sarp_effects(kaal_sarp_type),
            "remedies": get_kaal_sarp_remedies()
        }

    return {
        "dosha_name": "Kaal Sarp Dosha",
        "is_present": False,
        "severity": "None"
    }


def check_sade_sati(chart_data: dict, current_date: str = None) -> dict:
    """
    Check Shani Sade Sati status.

    Sade Sati is 7.5 year period when Saturn transits:
    - 12th house from Moon (Rising phase - 2.5 years)
    - 1st house from Moon (Peak phase - 2.5 years)
    - 2nd house from Moon (Setting phase - 2.5 years)

    Also check Small Panoti (Dhaiya):
    - Saturn in 4th from Moon
    - Saturn in 8th from Moon
    """
    from datetime import datetime
    import swisseph as swe

    if current_date is None:
        current_date = datetime.now()

    moon_sign = chart_data["moon_sign"]
    moon_sign_index = ZODIAC_SIGNS.index(moon_sign)

    # Get current Saturn position
    # (Using Swiss Ephemeris for current transit)
    julian_day = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
    saturn_position = swe.calc_ut(julian_day, swe.SATURN, swe.FLG_SIDEREAL)[0][0] % 360
    saturn_sign_index = int(saturn_position // 30)

    # Calculate Saturn's position relative to Moon
    relative_position = (saturn_sign_index - moon_sign_index) % 12

    phase = None
    if relative_position == 11:  # 12th from Moon
        phase = "Rising (First Phase)"
    elif relative_position == 0:  # Same as Moon (1st)
        phase = "Peak (Second Phase)"
    elif relative_position == 1:  # 2nd from Moon
        phase = "Setting (Third Phase)"
    elif relative_position == 3:  # 4th from Moon
        phase = "Small Panoti (Dhaiya)"
    elif relative_position == 7:  # 8th from Moon
        phase = "Small Panoti (Ashtam Shani)"

    is_in_sade_sati = phase in ["Rising (First Phase)", "Peak (Second Phase)", "Setting (Third Phase)"]

    return {
        "dosha_name": "Shani Sade Sati",
        "is_present": is_in_sade_sati,
        "current_phase": phase,
        "moon_sign": moon_sign,
        "saturn_sign": ZODIAC_SIGNS[saturn_sign_index],
        "severity": "High" if phase == "Peak (Second Phase)" else ("Medium" if is_in_sade_sati else "Low"),
        "effects": get_sade_sati_effects(phase) if phase else [],
        "remedies": get_sade_sati_remedies() if is_in_sade_sati else [],
        "end_date": calculate_sade_sati_end(saturn_sign_index, moon_sign_index)
    }


async def check_all_doshas(chart_data: dict) -> dict:
    """Check all major doshas in one call."""

    return {
        "manglik": check_manglik_dosha(chart_data),
        "kaal_sarp": check_kaal_sarp_dosha(chart_data),
        "sade_sati": check_sade_sati(chart_data),
        "pitra_dosha": check_pitra_dosha(chart_data),
        "summary": generate_dosha_summary(chart_data)
    }
```

---

## Phase 3: Remedies Engine (P1)

### 3.1 New Intent: `get_remedy`

**Query Types:**
```
- "Which gemstone should I wear?"
- "Remedy for Rahu"
- "Mantra for success"
- "Puja for marriage"
- "How to please Saturn?"
- "Stone for career growth"
- "Remove negative energy"
```

### 3.2 Create `bot/tools/remedy_tool.py`:

```python
"""
Vedic Remedies Tool

Provides personalized remedies based on birth chart:
1. Gemstones - Based on weak/afflicted planets
2. Mantras - Planet-specific sacred chants
3. Pujas - Rituals for specific purposes
4. Fasting - Vrat recommendations
5. Charity - Daan suggestions
6. Rudraksha - Based on ruling planet
7. Yantras - Sacred geometry tools
"""

# Gemstone recommendations
PLANET_GEMSTONES = {
    "Sun": {"primary": "Ruby (Manik)", "alternative": "Red Garnet", "metal": "Gold", "finger": "Ring finger", "day": "Sunday"},
    "Moon": {"primary": "Pearl (Moti)", "alternative": "Moonstone", "metal": "Silver", "finger": "Little finger", "day": "Monday"},
    "Mars": {"primary": "Red Coral (Moonga)", "alternative": "Carnelian", "metal": "Gold/Copper", "finger": "Ring finger", "day": "Tuesday"},
    "Mercury": {"primary": "Emerald (Panna)", "alternative": "Green Tourmaline", "metal": "Gold", "finger": "Little finger", "day": "Wednesday"},
    "Jupiter": {"primary": "Yellow Sapphire (Pukhraj)", "alternative": "Citrine", "metal": "Gold", "finger": "Index finger", "day": "Thursday"},
    "Venus": {"primary": "Diamond (Heera)", "alternative": "White Sapphire", "metal": "Platinum/Silver", "finger": "Little finger", "day": "Friday"},
    "Saturn": {"primary": "Blue Sapphire (Neelam)", "alternative": "Amethyst", "metal": "Iron/Silver", "finger": "Middle finger", "day": "Saturday"},
    "Rahu": {"primary": "Hessonite (Gomed)", "alternative": "Orange Zircon", "metal": "Silver", "finger": "Middle finger", "day": "Saturday"},
    "Ketu": {"primary": "Cat's Eye (Lahsuniya)", "alternative": "Chrysoberyl", "metal": "Silver", "finger": "Little finger", "day": "Tuesday"}
}

# Planet Mantras
PLANET_MANTRAS = {
    "Sun": {
        "beej": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "vedic": "Om Aditya Ya Vidmahe Divakaraya Dhimahi Tanno Surya Prachodayat",
        "count": 7000,
        "benefits": "Leadership, confidence, health, father's blessings"
    },
    "Moon": {
        "beej": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "vedic": "Om Kshirputraya Vidmahe Amrittattvaya Dhimahi Tanno Chandra Prachodayat",
        "count": 11000,
        "benefits": "Mental peace, mother's blessings, emotional balance"
    },
    "Mars": {
        "beej": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "vedic": "Om Angarakaya Vidmahe Shakti Hastaya Dhimahi Tanno Bhaumah Prachodayat",
        "count": 10000,
        "benefits": "Courage, property, siblings, energy"
    },
    # ... (all planets)
}

# Puja recommendations
PUJA_RECOMMENDATIONS = {
    "marriage": ["Gauri-Shankar Puja", "Swayamvara Parvathi Homam", "Vivah Badha Nivaran"],
    "career": ["Vishnu Sahasranama", "Lakshmi Narayana Puja", "Baglamukhi Puja"],
    "children": ["Santana Gopala Puja", "Garbarakshambika Homam", "Putrakameshti Yagna"],
    "wealth": ["Lakshmi Puja", "Kubera Puja", "Mahalakshmi Homam"],
    "health": ["Maha Mrityunjaya Homam", "Dhanvantari Puja", "Ayushya Homam"],
    "remove_obstacles": ["Ganesha Puja", "Navgraha Shanti", "Sarpa Dosha Nivaran"],
}

async def get_gemstone_recommendation(chart_data: dict, purpose: str = None) -> dict:
    """Get personalized gemstone recommendation."""

    # Analyze chart for weak/afflicted planets
    weak_planets = find_weak_planets(chart_data)
    benefic_planets = find_benefic_planets(chart_data)

    # Primary recommendation based on ascendant lord
    ascendant = chart_data["ascendant"]["sign"]
    ascendant_lord = RASHI_LORD[ascendant]

    primary_stone = PLANET_GEMSTONES[ascendant_lord]

    # Secondary based on purpose
    purpose_planet = get_planet_for_purpose(purpose) if purpose else None

    return {
        "primary_recommendation": {
            "stone": primary_stone["primary"],
            "planet": ascendant_lord,
            "reason": f"Strengthens your ascendant lord {ascendant_lord}",
            "metal": primary_stone["metal"],
            "finger": primary_stone["finger"],
            "day_to_wear": primary_stone["day"],
            "weight": "3-5 carats minimum",
            "mantra": PLANET_MANTRAS[ascendant_lord]["beej"]
        },
        "alternative": primary_stone["alternative"],
        "avoid_stones": get_stones_to_avoid(chart_data),
        "precautions": [
            "Consult an astrologer before wearing",
            "Ensure the stone is natural and untreated",
            "Wear after proper energization (prana pratishtha)"
        ]
    }
```

---

## Phase 4: Muhurta Finder (P1)

### 4.1 New Intent: `find_muhurta`

**Query Types:**
```
- "Best date for marriage in 2025"
- "Shubh muhurat for business"
- "Auspicious time for griha pravesh"
- "Good day to buy car"
- "Wedding dates in January"
```

### 4.2 Create `bot/tools/muhurta_tool.py`:

```python
"""
Muhurta (Auspicious Timing) Tool

Finds auspicious dates/times for various activities:
- Vivah (Marriage)
- Griha Pravesh (Housewarming)
- Business Start
- Vehicle Purchase
- Travel
- Naming Ceremony
- Mundane (First Learning)

Based on:
- Tithi (Lunar Day)
- Nakshatra (Star)
- Yoga
- Karan
- Day of Week
- Rahu Kaal avoidance
- Planetary transits
"""

# Auspicious Tithis for different activities
AUSPICIOUS_TITHIS = {
    "marriage": [2, 3, 5, 7, 10, 11, 12, 13, 15],  # Avoid 4, 6, 8, 9, 14, 30
    "griha_pravesh": [2, 3, 5, 7, 10, 11, 12, 13],
    "business": [2, 3, 5, 6, 7, 10, 11, 12, 13],
    "vehicle": [2, 3, 5, 7, 10, 11, 12, 13],
    "travel": [2, 3, 5, 7, 11, 12, 13],
    "naming": [2, 3, 5, 7, 10, 12, 13]
}

# Auspicious Nakshatras
AUSPICIOUS_NAKSHATRAS = {
    "marriage": ["Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati",
                 "Anuradha", "Mula", "Uttara Ashadha", "Uttara Bhadrapada", "Revati"],
    "griha_pravesh": ["Rohini", "Mrigashira", "Uttara Phalguni", "Hasta", "Chitra",
                      "Swati", "Anuradha", "Uttara Ashadha", "Shravana", "Dhanishta", "Revati"],
    "business": ["Ashwini", "Rohini", "Mrigashira", "Punarvasu", "Pushya", "Hasta",
                 "Chitra", "Swati", "Anuradha", "Shravana", "Revati"],
    "vehicle": ["Ashwini", "Rohini", "Punarvasu", "Pushya", "Hasta", "Chitra",
                "Swati", "Anuradha", "Shravana", "Revati"],
}

# Days to avoid for activities
AVOID_DAYS = {
    "marriage": ["Tuesday", "Saturday"],  # Avoid Mangalvar and Shanivar
    "griha_pravesh": ["Tuesday"],
    "travel": ["Tuesday"],
    "vehicle": ["Tuesday", "Saturday"],
}

async def find_muhurta(
    activity: str,
    start_date: str,
    end_date: str,
    location: str = "Delhi"
) -> ToolResult:
    """Find auspicious dates for an activity within a date range."""

    from datetime import datetime, timedelta

    start = parse_date(start_date)
    end = parse_date(end_date)

    if not start or not end:
        return ToolResult(success=False, error="Invalid date format")

    lat, lon = get_lat_lon(location)
    auspicious_dates = []

    current = start
    while current <= end:
        panchang = await calculate_panchang(current.strftime("%Y-%m-%d"), location)

        if panchang["success"]:
            data = panchang["data"]

            # Check all criteria
            is_good_tithi = data["tithi"]["number"] in AUSPICIOUS_TITHIS.get(activity, [])
            is_good_nakshatra = data["nakshatra"]["name"] in AUSPICIOUS_NAKSHATRAS.get(activity, [])
            is_good_day = data["day"] not in AVOID_DAYS.get(activity, [])
            is_not_rahu_kaal = True  # Would calculate actual Rahu Kaal

            score = sum([is_good_tithi * 3, is_good_nakshatra * 3, is_good_day * 2, is_not_rahu_kaal * 2])

            if score >= 6:  # Threshold for "good" muhurta
                auspicious_dates.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "day": data["day"],
                    "tithi": data["tithi"]["name"],
                    "nakshatra": data["nakshatra"]["name"],
                    "score": score,
                    "rating": "Excellent" if score >= 9 else "Good",
                    "auspicious_time": get_auspicious_time_slots(current, lat, lon)
                })

        current += timedelta(days=1)

    # Sort by score
    auspicious_dates.sort(key=lambda x: x["score"], reverse=True)

    return ToolResult(
        success=True,
        data={
            "activity": activity,
            "search_range": f"{start_date} to {end_date}",
            "location": location,
            "auspicious_dates": auspicious_dates[:10],  # Top 10
            "total_found": len(auspicious_dates)
        },
        error=None,
        tool_name="muhurta"
    )
```

---

## Phase 5: Expose Panchang (P1)

### 5.1 New Intent: `get_panchang`

**Already implemented in `astro_tool.py`, just need to expose as intent.**

**Query Types:**
```
- "Today's panchang"
- "What tithi is today?"
- "Today's nakshatra"
- "Rahu kaal today"
- "Panchang for tomorrow"
```

### 5.2 Add to `intent.py`:
```python
# Panchang keywords
panchang_keywords = ["panchang", "tithi", "today's nakshatra", "rahu kaal", "rahu kalam",
                     "shubh muhurat today", "auspicious time today", "today's yoga"]
```

### 5.3 Create `bot/nodes/panchang_node.py`:
```python
async def handle_panchang(state: BotState) -> dict:
    entities = state.get("extracted_entities", {})
    date = entities.get("date", "today")
    place = entities.get("place", "Delhi")

    result = await calculate_panchang(date, place)

    if result["success"]:
        data = result["data"]
        response = f"*Panchang for {data['date']}*\n"
        response += f"*Day:* {data['day']}\n\n"
        response += f"*Tithi:* {data['tithi']['name']} ({data['tithi']['paksha']})\n"
        response += f"*Nakshatra:* {data['nakshatra']['name']} (Pada {data['nakshatra']['pada']})\n"
        response += f"*Yoga:* {data['yoga']}\n"
        response += f"*Karan:* {', '.join(data['karan'])}\n"
        response += f"*Moon Sign:* {data['moon_sign']}\n"

        return {
            "tool_result": result,
            "response_text": response,
            "response_type": "text",
            "should_fallback": False,
        }
```

---

## Phase 6: Dasha & Transit Analysis (P2)

### 6.1 New Intent: `dasha_analysis`

**Query Types:**
```
- "What is my current Mahadasha?"
- "Rahu Dasha effects"
- "When will Saturn Dasha start?"
- "Jupiter transit effects"
- "Current Antardasha"
```

### 6.2 Create `bot/tools/dasha_tool.py`:

```python
"""
Vimshottari Dasha Calculator

Calculates:
- Mahadasha (Main period) - 120 year cycle
- Antardasha (Sub-period)
- Pratyantardasha (Sub-sub-period)

Based on Moon's Nakshatra at birth.
"""

# Vimshottari Dasha periods (in years)
DASHA_PERIODS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17
}

# Nakshatra to starting Dasha lord
NAKSHATRA_DASHA_LORD = {
    "Ashwini": "Ketu", "Magha": "Ketu", "Mula": "Ketu",
    "Bharani": "Venus", "Purva Phalguni": "Venus", "Purva Ashadha": "Venus",
    "Krittika": "Sun", "Uttara Phalguni": "Sun", "Uttara Ashadha": "Sun",
    "Rohini": "Moon", "Hasta": "Moon", "Shravana": "Moon",
    "Mrigashira": "Mars", "Chitra": "Mars", "Dhanishta": "Mars",
    "Ardra": "Rahu", "Swati": "Rahu", "Shatabhisha": "Rahu",
    "Punarvasu": "Jupiter", "Vishakha": "Jupiter", "Purva Bhadrapada": "Jupiter",
    "Pushya": "Saturn", "Anuradha": "Saturn", "Uttara Bhadrapada": "Saturn",
    "Ashlesha": "Mercury", "Jyeshtha": "Mercury", "Revati": "Mercury"
}

async def calculate_dasha(chart_data: dict, current_date: str = None) -> dict:
    """Calculate current Dasha periods."""

    moon_nakshatra = chart_data["moon_nakshatra"]
    birth_date = chart_data["birth_date"]

    # Get starting Dasha lord
    starting_lord = NAKSHATRA_DASHA_LORD[moon_nakshatra]

    # Calculate elapsed portion at birth based on Moon's exact position in Nakshatra
    # This determines how much of the first Dasha has passed

    # Calculate current Mahadasha, Antardasha
    current_mahadasha = get_current_mahadasha(birth_date, starting_lord, current_date)
    current_antardasha = get_current_antardasha(current_mahadasha)

    return {
        "mahadasha": {
            "lord": current_mahadasha["lord"],
            "start_date": current_mahadasha["start"],
            "end_date": current_mahadasha["end"],
            "effects": get_mahadasha_effects(current_mahadasha["lord"], chart_data),
            "remedies": get_dasha_remedies(current_mahadasha["lord"])
        },
        "antardasha": {
            "lord": current_antardasha["lord"],
            "start_date": current_antardasha["start"],
            "end_date": current_antardasha["end"],
            "effects": get_antardasha_effects(current_mahadasha["lord"], current_antardasha["lord"])
        },
        "upcoming_changes": get_upcoming_dasha_changes(birth_date, starting_lord),
        "full_dasha_sequence": generate_full_dasha_sequence(birth_date, starting_lord)
    }
```

---

## Phase 7: Vastu Basics (P2)

### 7.1 New Intent: `vastu_advice`

**Query Types:**
```
- "Vastu tips for home"
- "Which direction to face while working?"
- "Bedroom direction as per vastu"
- "Kitchen placement vastu"
- "Vastu for office"
```

### 7.2 Create `bot/tools/vastu_tool.py`:

```python
"""
Basic Vastu Shastra Tool

Provides direction-based recommendations for:
- Home layout
- Room placements
- Desk/bed direction
- Color recommendations
- Element balancing
"""

DIRECTION_MEANINGS = {
    "North": {"ruling_planet": "Mercury", "element": "Water", "color": "Green", "best_for": ["Living room", "Office", "Study"]},
    "East": {"ruling_planet": "Sun", "element": "Air", "color": "White", "best_for": ["Main entrance", "Puja room", "Windows"]},
    "South": {"ruling_planet": "Mars", "element": "Fire", "color": "Red", "best_for": ["Bedroom", "Storage"]},
    "West": {"ruling_planet": "Saturn", "element": "Water", "color": "Blue", "best_for": ["Dining", "Children's room"]},
    "Northeast": {"ruling_planet": "Jupiter", "element": "Water", "color": "Yellow", "best_for": ["Puja room", "Meditation", "Water storage"]},
    "Southeast": {"ruling_planet": "Venus", "element": "Fire", "color": "Orange", "best_for": ["Kitchen", "Electrical items"]},
    "Southwest": {"ruling_planet": "Rahu", "element": "Earth", "color": "Brown", "best_for": ["Master bedroom", "Heavy storage"]},
    "Northwest": {"ruling_planet": "Moon", "element": "Air", "color": "White", "best_for": ["Guest room", "Garage", "Toilet"]}
}

async def get_vastu_advice(query_type: str, specific_room: str = None) -> dict:
    """Get Vastu recommendations."""

    if query_type == "home":
        return get_home_vastu_tips()
    elif query_type == "office":
        return get_office_vastu_tips()
    elif query_type == "direction":
        return get_direction_recommendations(specific_room)
    elif query_type == "room":
        return get_room_placement_tips(specific_room)
```

---

## Implementation Checklist

### Phase 1: Life Predictions (Week 1-2)
- [ ] Add `life_prediction` intent to state.py
- [ ] Add pattern matching in intent.py
- [ ] Create life_prediction_node.py
- [ ] Create life_prediction_tool.py
- [ ] Add to graph.py routing
- [ ] Test all life prediction queries

### Phase 2: Doshas Detection (Week 2-3)
- [ ] Add `dosha_check` intent to state.py
- [ ] Add pattern matching in intent.py
- [ ] Create dosha_node.py
- [ ] Create dosha_tool.py with all dosha checks
- [ ] Add to graph.py routing
- [ ] Test: Manglik, Kaal Sarp, Sade Sati queries

### Phase 3: Remedies Engine (Week 3-4)
- [ ] Add `get_remedy` intent to state.py
- [ ] Add pattern matching in intent.py
- [ ] Create remedy_node.py
- [ ] Create remedy_tool.py
- [ ] Add gemstone, mantra, puja databases
- [ ] Test all remedy queries

### Phase 4: Muhurta Finder (Week 4-5)
- [ ] Add `find_muhurta` intent to state.py
- [ ] Add pattern matching in intent.py
- [ ] Create muhurta_node.py
- [ ] Create muhurta_tool.py
- [ ] Add auspicious date calculation logic
- [ ] Test muhurta queries

### Phase 5: Panchang Exposure (Week 5)
- [ ] Add `get_panchang` intent to state.py
- [ ] Add pattern matching in intent.py
- [ ] Create panchang_node.py
- [ ] Add Rahu Kaal calculation
- [ ] Test panchang queries

### Phase 6: Dasha Analysis (Week 5-6)
- [ ] Add `dasha_analysis` intent to state.py
- [ ] Create dasha_node.py
- [ ] Create dasha_tool.py with Vimshottari calculation
- [ ] Add transit analysis
- [ ] Test dasha queries

### Phase 7: Vastu Basics (Week 6)
- [ ] Add `vastu_advice` intent to state.py
- [ ] Create vastu_node.py
- [ ] Create vastu_tool.py
- [ ] Test vastu queries

---

## Database/Storage Needs

For user context and personalization:

```sql
-- User birth details (for repeated queries)
CREATE TABLE user_profiles (
    phone_number VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    birth_date DATE,
    birth_time TIME,
    birth_place VARCHAR(100),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    moon_sign VARCHAR(20),
    moon_nakshatra VARCHAR(30),
    ascendant VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cache kundli calculations
CREATE TABLE kundli_cache (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20),
    chart_data JSONB,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Priority Order for Implementation

1. **Life Predictions** - Highest user demand
2. **Dosha Detection** - "Am I Manglik?" is top query
3. **Remedies** - Natural follow-up to doshas
4. **Panchang** - Already implemented, just expose
5. **Muhurta** - Wedding dates are popular
6. **Dasha Analysis** - Complex but valuable
7. **Vastu** - Nice to have

---

## Estimated Effort

| Phase | Feature | Effort | Dependencies |
|-------|---------|--------|--------------|
| 1 | Life Predictions | 3-4 days | Kundli tool |
| 2 | Dosha Detection | 2-3 days | Kundli tool |
| 3 | Remedies Engine | 2-3 days | Dosha tool |
| 4 | Muhurta Finder | 3-4 days | Panchang tool |
| 5 | Panchang Exposure | 1 day | Already done |
| 6 | Dasha Analysis | 3-4 days | Kundli tool |
| 7 | Vastu Basics | 1-2 days | None |

**Total: ~15-20 days for full implementation**
