"""
Jyotish Rules Engine

Deterministic evaluation of Vedic astrology rules.
All rules are explicit with clear conditions and evidence.

Implements:
1. Planet Dignity (own/exalted/debilitated)
2. Yogas (limited, curated set - ~20-30 core rules)
3. Doshas (conservative set)
4. Vimshottari Dasha calculation
5. Ashtakoot Milan (36-point matching)

Each rule has:
- Clear conditions
- Evidence from chart
- Confidence score
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta

from bot.astro.schemas.chart import (
    ChartData,
    PlanetPosition,
    Planet,
    ZodiacSign,
    Nakshatra,
    ZODIAC_LORDS,
    NAKSHATRA_LORDS,
)
from bot.astro.schemas.rules import (
    RulesOutput,
    RuleFinding,
    YogaResult,
    DoshaResult,
    DashaResult,
    PlanetDignity,
    CompatibilityScore,
    KundliMatchResult,
    ConfidenceLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PLANET DIGNITY TABLES
# =============================================================================

# Exaltation signs
EXALTATION = {
    Planet.SUN: ZodiacSign.ARIES,
    Planet.MOON: ZodiacSign.TAURUS,
    Planet.MARS: ZodiacSign.CAPRICORN,
    Planet.MERCURY: ZodiacSign.VIRGO,
    Planet.JUPITER: ZodiacSign.CANCER,
    Planet.VENUS: ZodiacSign.PISCES,
    Planet.SATURN: ZodiacSign.LIBRA,
    Planet.RAHU: ZodiacSign.GEMINI,  # Debated, some say Taurus
    Planet.KETU: ZodiacSign.SAGITTARIUS,  # Debated
}

# Debilitation signs (opposite of exaltation)
DEBILITATION = {
    Planet.SUN: ZodiacSign.LIBRA,
    Planet.MOON: ZodiacSign.SCORPIO,
    Planet.MARS: ZodiacSign.CANCER,
    Planet.MERCURY: ZodiacSign.PISCES,
    Planet.JUPITER: ZodiacSign.CAPRICORN,
    Planet.VENUS: ZodiacSign.VIRGO,
    Planet.SATURN: ZodiacSign.ARIES,
    Planet.RAHU: ZodiacSign.SAGITTARIUS,
    Planet.KETU: ZodiacSign.GEMINI,
}

# Own signs (rulership)
OWN_SIGNS = {
    Planet.SUN: [ZodiacSign.LEO],
    Planet.MOON: [ZodiacSign.CANCER],
    Planet.MARS: [ZodiacSign.ARIES, ZodiacSign.SCORPIO],
    Planet.MERCURY: [ZodiacSign.GEMINI, ZodiacSign.VIRGO],
    Planet.JUPITER: [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES],
    Planet.VENUS: [ZodiacSign.TAURUS, ZodiacSign.LIBRA],
    Planet.SATURN: [ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS],
    Planet.RAHU: [],  # Shadow planet, no ownership
    Planet.KETU: [],
}

# Mool Trikona signs and degree ranges
MOOL_TRIKONA = {
    Planet.SUN: (ZodiacSign.LEO, 0, 20),
    Planet.MOON: (ZodiacSign.TAURUS, 3, 30),
    Planet.MARS: (ZodiacSign.ARIES, 0, 12),
    Planet.MERCURY: (ZodiacSign.VIRGO, 15, 20),
    Planet.JUPITER: (ZodiacSign.SAGITTARIUS, 0, 10),
    Planet.VENUS: (ZodiacSign.LIBRA, 0, 15),
    Planet.SATURN: (ZodiacSign.AQUARIUS, 0, 20),
}

# Natural benefics and malefics
NATURAL_BENEFICS = [Planet.JUPITER, Planet.VENUS, Planet.MERCURY]  # Mercury when alone
NATURAL_MALEFICS = [Planet.SATURN, Planet.MARS, Planet.RAHU, Planet.KETU]

# Vimshottari Dasha periods (years)
DASHA_YEARS = {
    Planet.KETU: 7,
    Planet.VENUS: 20,
    Planet.SUN: 6,
    Planet.MOON: 10,
    Planet.MARS: 7,
    Planet.RAHU: 18,
    Planet.JUPITER: 16,
    Planet.SATURN: 19,
    Planet.MERCURY: 17,
}

# Dasha sequence
DASHA_SEQUENCE = [
    Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, Planet.MARS,
    Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY
]

# =============================================================================
# ASHTAKOOT MILAN TABLES
# =============================================================================

VARNA_SCORES = {
    ("Brahmin", "Brahmin"): 1, ("Brahmin", "Kshatriya"): 1, ("Brahmin", "Vaishya"): 1, ("Brahmin", "Shudra"): 1,
    ("Kshatriya", "Brahmin"): 0, ("Kshatriya", "Kshatriya"): 1, ("Kshatriya", "Vaishya"): 1, ("Kshatriya", "Shudra"): 1,
    ("Vaishya", "Brahmin"): 0, ("Vaishya", "Kshatriya"): 0, ("Vaishya", "Vaishya"): 1, ("Vaishya", "Shudra"): 1,
    ("Shudra", "Brahmin"): 0, ("Shudra", "Kshatriya"): 0, ("Shudra", "Vaishya"): 0, ("Shudra", "Shudra"): 1,
}

VASHYA_SCORES = {
    ("Human", "Human"): 2, ("Human", "Quadruped"): 1, ("Human", "Water"): 0.5,
    ("Human", "Wild Animal"): 0, ("Human", "Insect"): 1,
    ("Quadruped", "Human"): 0, ("Quadruped", "Quadruped"): 2, ("Quadruped", "Water"): 1,
    ("Quadruped", "Wild Animal"): 0, ("Quadruped", "Insect"): 1,
    ("Water", "Human"): 0, ("Water", "Quadruped"): 1, ("Water", "Water"): 2,
    ("Water", "Wild Animal"): 0, ("Water", "Insect"): 1,
    ("Wild Animal", "Human"): 0.5, ("Wild Animal", "Quadruped"): 0.5, ("Wild Animal", "Water"): 1,
    ("Wild Animal", "Wild Animal"): 2, ("Wild Animal", "Insect"): 0,
    ("Insect", "Human"): 0, ("Insect", "Quadruped"): 1, ("Insect", "Water"): 1,
    ("Insect", "Wild Animal"): 0, ("Insect", "Insect"): 2
}

GANA_SCORES = {
    ("Deva", "Deva"): 6, ("Deva", "Manushya"): 6, ("Deva", "Rakshasa"): 1,
    ("Manushya", "Deva"): 5, ("Manushya", "Manushya"): 6, ("Manushya", "Rakshasa"): 0,
    ("Rakshasa", "Deva"): 1, ("Rakshasa", "Manushya"): 0, ("Rakshasa", "Rakshasa"): 6
}

MAITRI_SCORES = {
    ("Sun", "Sun"): 5, ("Sun", "Moon"): 5, ("Sun", "Mars"): 5, ("Sun", "Mercury"): 4,
    ("Sun", "Jupiter"): 5, ("Sun", "Venus"): 0, ("Sun", "Saturn"): 0,
    ("Moon", "Sun"): 5, ("Moon", "Moon"): 5, ("Moon", "Mars"): 4, ("Moon", "Mercury"): 1,
    ("Moon", "Jupiter"): 4, ("Moon", "Venus"): 0.5, ("Moon", "Saturn"): 0.5,
    ("Mars", "Sun"): 5, ("Mars", "Moon"): 4, ("Mars", "Mars"): 5, ("Mars", "Mercury"): 0.5,
    ("Mars", "Jupiter"): 5, ("Mars", "Venus"): 3, ("Mars", "Saturn"): 0.5,
    ("Mercury", "Sun"): 4, ("Mercury", "Moon"): 1, ("Mercury", "Mars"): 0.5,
    ("Mercury", "Mercury"): 5, ("Mercury", "Jupiter"): 0.5, ("Mercury", "Venus"): 5, ("Mercury", "Saturn"): 4,
    ("Jupiter", "Sun"): 5, ("Jupiter", "Moon"): 4, ("Jupiter", "Mars"): 5,
    ("Jupiter", "Mercury"): 0.5, ("Jupiter", "Jupiter"): 5, ("Jupiter", "Venus"): 0.5, ("Jupiter", "Saturn"): 3,
    ("Venus", "Sun"): 0, ("Venus", "Moon"): 0.5, ("Venus", "Mars"): 3, ("Venus", "Mercury"): 5,
    ("Venus", "Jupiter"): 0.5, ("Venus", "Venus"): 5, ("Venus", "Saturn"): 5,
    ("Saturn", "Sun"): 0, ("Saturn", "Moon"): 0.5, ("Saturn", "Mars"): 0.5,
    ("Saturn", "Mercury"): 4, ("Saturn", "Jupiter"): 3, ("Saturn", "Venus"): 5, ("Saturn", "Saturn"): 5
}

# Yoni compatibility (4 points max)
YONI_SCORES = {
    ("Horse", "Horse"): 4, ("Horse", "Buffalo"): 0, ("Elephant", "Elephant"): 4,
    ("Elephant", "Lion"): 0, ("Dog", "Dog"): 4, ("Cat", "Cat"): 4, ("Cat", "Rat"): 0,
    ("Rat", "Rat"): 4, ("Cow", "Cow"): 4, ("Cow", "Tiger"): 0, ("Tiger", "Tiger"): 4,
    ("Buffalo", "Buffalo"): 4, ("Lion", "Lion"): 4, ("Deer", "Deer"): 4, ("Deer", "Dog"): 0,
    ("Mongoose", "Mongoose"): 4, ("Mongoose", "Serpent"): 0, ("Serpent", "Serpent"): 4,
    ("Monkey", "Monkey"): 4, ("Goat", "Goat"): 4, ("Goat", "Mongoose"): 0, ("Sheep", "Sheep"): 4,
}

# Bhakoot score matrix
BHAKOOT_SCORES = {
    (1, 1): 7, (1, 2): 0, (1, 3): 7, (1, 4): 7, (1, 5): 0, (1, 6): 0,
    (1, 7): 7, (1, 8): 0, (1, 9): 0, (1, 10): 7, (1, 11): 7, (1, 12): 0,
}


class RulesEngine:
    """
    Jyotish Rules Evaluation Engine.

    Evaluates a curated set of rules against chart data.
    All rules are explicit and deterministic.
    """

    def __init__(self):
        """Initialize rules engine."""
        self.rules_version = "1.0.0"

    # =========================================================================
    # DIGNITY ANALYSIS
    # =========================================================================

    def calculate_dignity(self, position: PlanetPosition) -> PlanetDignity:
        """Calculate dignity status for a planet."""
        planet = position.planet
        sign = position.sign
        degree = position.sign_degree

        # Check Mool Trikona first (strongest after exaltation)
        if planet in MOOL_TRIKONA:
            mt_sign, mt_start, mt_end = MOOL_TRIKONA[planet]
            if sign == mt_sign and mt_start <= degree <= mt_end:
                return PlanetDignity(
                    planet=planet,
                    sign=sign,
                    dignity_status="mool_trikona",
                    dignity_score=1.5,
                    house_placement=position.house,
                    house_lordship=self._get_house_lordship(planet, sign),
                    is_functional_benefic=planet in NATURAL_BENEFICS
                )

        # Check exaltation
        if EXALTATION.get(planet) == sign:
            return PlanetDignity(
                planet=planet,
                sign=sign,
                dignity_status="exalted",
                dignity_score=2.0,
                house_placement=position.house,
                house_lordship=self._get_house_lordship(planet, sign),
                is_functional_benefic=planet in NATURAL_BENEFICS
            )

        # Check debilitation
        if DEBILITATION.get(planet) == sign:
            return PlanetDignity(
                planet=planet,
                sign=sign,
                dignity_status="debilitated",
                dignity_score=-2.0,
                house_placement=position.house,
                house_lordship=self._get_house_lordship(planet, sign),
                is_functional_benefic=planet in NATURAL_BENEFICS
            )

        # Check own sign
        if sign in OWN_SIGNS.get(planet, []):
            return PlanetDignity(
                planet=planet,
                sign=sign,
                dignity_status="own",
                dignity_score=1.0,
                house_placement=position.house,
                house_lordship=self._get_house_lordship(planet, sign),
                is_functional_benefic=planet in NATURAL_BENEFICS
            )

        # Neutral
        return PlanetDignity(
            planet=planet,
            sign=sign,
            dignity_status="neutral",
            dignity_score=0.0,
            house_placement=position.house,
            house_lordship=self._get_house_lordship(planet, sign),
            is_functional_benefic=planet in NATURAL_BENEFICS
        )

    def _get_house_lordship(self, planet: Planet, current_sign: ZodiacSign) -> List[int]:
        """Get houses ruled by this planet from current ascendant."""
        # This would need ascendant to calculate properly
        # Simplified version returns signs ruled
        return [i + 1 for i, s in enumerate(list(ZodiacSign)) if s in OWN_SIGNS.get(planet, [])]

    # =========================================================================
    # YOGA DETECTION (Curated ~20-30 rules)
    # =========================================================================

    def detect_yogas(self, chart: ChartData) -> List[YogaResult]:
        """
        Detect active yogas in chart.

        Only implements well-established yogas with clear conditions.
        """
        yogas = []
        planets = chart.planets

        # 1. Gaja Kesari Yoga
        yoga = self._check_gaja_kesari(chart)
        if yoga:
            yogas.append(yoga)

        # 2. Budhaditya Yoga
        yoga = self._check_budhaditya(chart)
        if yoga:
            yogas.append(yoga)

        # 3. Chandra-Mangal Yoga
        yoga = self._check_chandra_mangal(chart)
        if yoga:
            yogas.append(yoga)

        # 4. Panch Mahapurusha Yogas
        for yoga in self._check_mahapurusha_yogas(chart):
            yogas.append(yoga)

        # 5. Raja Yogas (Kendra-Trikona lords conjunction)
        for yoga in self._check_raja_yogas(chart):
            yogas.append(yoga)

        # 6. Dhana Yogas
        for yoga in self._check_dhana_yogas(chart):
            yogas.append(yoga)

        return yogas

    def _check_gaja_kesari(self, chart: ChartData) -> Optional[YogaResult]:
        """
        Gaja Kesari Yoga: Jupiter in kendra from Moon.
        Effect: Wisdom, wealth, reputation.
        """
        moon_house = chart.planets[Planet.MOON].house
        jupiter_house = chart.planets[Planet.JUPITER].house

        diff = (jupiter_house - moon_house) % 12
        kendras_from_moon = [0, 3, 6, 9]  # 1st, 4th, 7th, 10th from Moon

        if diff in kendras_from_moon:
            # Check strength
            jupiter_dignity = self.calculate_dignity(chart.planets[Planet.JUPITER])
            strength = 0.5 + (jupiter_dignity.dignity_score / 4)  # Normalize to 0-1

            return YogaResult(
                rule_name="Gaja Kesari Yoga",
                rule_category="yoga",
                is_active=True,
                conditions=[
                    "Jupiter in kendra (1st, 4th, 7th, or 10th) from Moon",
                    f"Jupiter in {chart.planets[Planet.JUPITER].sign.value}",
                    f"Moon in {chart.planets[Planet.MOON].sign.value}"
                ],
                evidence={
                    "jupiter_house": jupiter_house,
                    "moon_house": moon_house,
                    "house_difference": diff
                },
                confidence=ConfidenceLevel.HIGH,
                general_effect="Indicates wisdom, fame, and prosperity. Native gains respect and recognition.",
                yoga_type="raja_yoga",
                forming_planets=[Planet.JUPITER, Planet.MOON],
                houses_involved=[moon_house, jupiter_house],
                strength_score=max(0, min(1, strength)),
                benefic_malefic="benefic",
                source_text="Brihat Parashara Hora Shastra"
            )

        return None

    def _check_budhaditya(self, chart: ChartData) -> Optional[YogaResult]:
        """
        Budhaditya Yoga: Sun and Mercury conjunction.
        Effect: Intelligence, communication skills.
        """
        sun = chart.planets[Planet.SUN]
        mercury = chart.planets[Planet.MERCURY]

        if sun.house == mercury.house:
            # Check Mercury is not combust (too close to Sun)
            is_combust = mercury.is_combust
            strength = 0.7 if not is_combust else 0.3

            return YogaResult(
                rule_name="Budhaditya Yoga",
                rule_category="yoga",
                is_active=True,
                conditions=[
                    "Sun and Mercury in same house",
                    f"Both in {sun.sign.value}"
                ],
                evidence={
                    "sun_house": sun.house,
                    "mercury_house": mercury.house,
                    "mercury_combust": is_combust
                },
                confidence=ConfidenceLevel.HIGH if not is_combust else ConfidenceLevel.MEDIUM,
                general_effect="Grants intelligence, good communication, analytical ability. Combust Mercury reduces effect.",
                specific_context="Mercury combust" if is_combust else None,
                yoga_type="intelligence_yoga",
                forming_planets=[Planet.SUN, Planet.MERCURY],
                houses_involved=[sun.house],
                strength_score=strength,
                benefic_malefic="benefic",
                source_text="Classical texts"
            )

        return None

    def _check_chandra_mangal(self, chart: ChartData) -> Optional[YogaResult]:
        """
        Chandra-Mangal Yoga: Moon-Mars conjunction.
        Effect: Courage, wealth through effort.
        """
        moon = chart.planets[Planet.MOON]
        mars = chart.planets[Planet.MARS]

        if moon.house == mars.house:
            return YogaResult(
                rule_name="Chandra-Mangal Yoga",
                rule_category="yoga",
                is_active=True,
                conditions=[
                    "Moon and Mars in same house",
                    f"Both in {moon.sign.value}"
                ],
                evidence={
                    "moon_house": moon.house,
                    "mars_house": mars.house
                },
                confidence=ConfidenceLevel.HIGH,
                general_effect="Indicates earning through personal effort, courage, and determination.",
                yoga_type="dhana_yoga",
                forming_planets=[Planet.MOON, Planet.MARS],
                houses_involved=[moon.house],
                strength_score=0.6,
                benefic_malefic="mixed",
                source_text="Classical texts"
            )

        return None

    def _check_mahapurusha_yogas(self, chart: ChartData) -> List[YogaResult]:
        """
        Panch Mahapurusha Yogas: Mars, Mercury, Jupiter, Venus, Saturn
        in own/exalted sign AND in kendra.
        """
        yogas = []
        yoga_names = {
            Planet.MARS: "Ruchaka Yoga",
            Planet.MERCURY: "Bhadra Yoga",
            Planet.JUPITER: "Hamsa Yoga",
            Planet.VENUS: "Malavya Yoga",
            Planet.SATURN: "Sasha Yoga",
        }

        effects = {
            Planet.MARS: "Courage, leadership, military success",
            Planet.MERCURY: "Intelligence, business acumen, eloquence",
            Planet.JUPITER: "Spirituality, wisdom, good fortune",
            Planet.VENUS: "Beauty, luxury, artistic talent, romance",
            Planet.SATURN: "Power through discipline, authority",
        }

        kendras = [1, 4, 7, 10]

        for planet in [Planet.MARS, Planet.MERCURY, Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
            position = chart.planets[planet]
            dignity = self.calculate_dignity(position)

            if position.house in kendras and dignity.dignity_status in ["own", "exalted"]:
                yogas.append(YogaResult(
                    rule_name=yoga_names[planet],
                    rule_category="yoga",
                    is_active=True,
                    conditions=[
                        f"{planet.value} in kendra (house {position.house})",
                        f"{planet.value} in {dignity.dignity_status} sign ({position.sign.value})"
                    ],
                    evidence={
                        "planet": planet.value,
                        "house": position.house,
                        "sign": position.sign.value,
                        "dignity": dignity.dignity_status
                    },
                    confidence=ConfidenceLevel.HIGH,
                    general_effect=effects[planet],
                    yoga_type="mahapurusha_yoga",
                    forming_planets=[planet],
                    houses_involved=[position.house],
                    strength_score=0.8 if dignity.dignity_status == "exalted" else 0.7,
                    benefic_malefic="benefic",
                    source_text="Brihat Parashara Hora Shastra"
                ))

        return yogas

    def _check_raja_yogas(self, chart: ChartData) -> List[YogaResult]:
        """
        Raja Yogas: Lords of kendra and trikona houses in conjunction/aspect.
        """
        yogas = []

        # Get house lords
        kendras = [1, 4, 7, 10]
        trikonas = [1, 5, 9]  # 1 is both kendra and trikona

        kendra_lords = set()
        trikona_lords = set()

        for house_num, house in chart.houses.items():
            if house_num in kendras:
                kendra_lords.add(house.lord)
            if house_num in trikonas:
                trikona_lords.add(house.lord)

        # Check for conjunctions between kendra and trikona lords
        for kl in kendra_lords:
            for tl in trikona_lords:
                if kl != tl:
                    kl_house = chart.planets[kl].house
                    tl_house = chart.planets[tl].house

                    if kl_house == tl_house:
                        yogas.append(YogaResult(
                            rule_name=f"Raja Yoga ({kl.value}-{tl.value})",
                            rule_category="yoga",
                            is_active=True,
                            conditions=[
                                f"{kl.value} (kendra lord) conjunct {tl.value} (trikona lord)",
                                f"Conjunction in house {kl_house}"
                            ],
                            evidence={
                                "kendra_lord": kl.value,
                                "trikona_lord": tl.value,
                                "house": kl_house
                            },
                            confidence=ConfidenceLevel.HIGH,
                            general_effect="Indicates power, authority, success in career. One of the most important yogas.",
                            yoga_type="raja_yoga",
                            forming_planets=[kl, tl],
                            houses_involved=[kl_house],
                            strength_score=0.75,
                            benefic_malefic="benefic",
                            source_text="Brihat Parashara Hora Shastra"
                        ))

        return yogas

    def _check_dhana_yogas(self, chart: ChartData) -> List[YogaResult]:
        """
        Dhana Yogas: Wealth-producing combinations.
        """
        yogas = []

        # 2nd and 11th house lords conjunction
        second_lord = chart.houses[2].lord
        eleventh_lord = chart.houses[11].lord

        if chart.planets[second_lord].house == chart.planets[eleventh_lord].house:
            yogas.append(YogaResult(
                rule_name="Dhana Yoga (2-11)",
                rule_category="yoga",
                is_active=True,
                conditions=[
                    f"2nd lord ({second_lord.value}) conjunct 11th lord ({eleventh_lord.value})"
                ],
                evidence={
                    "second_lord": second_lord.value,
                    "eleventh_lord": eleventh_lord.value,
                    "house": chart.planets[second_lord].house
                },
                confidence=ConfidenceLevel.HIGH,
                general_effect="Indicates wealth accumulation through income and savings.",
                yoga_type="dhana_yoga",
                forming_planets=[second_lord, eleventh_lord],
                houses_involved=[chart.planets[second_lord].house],
                strength_score=0.7,
                benefic_malefic="benefic"
            ))

        return yogas

    # =========================================================================
    # DOSHA DETECTION (Conservative set)
    # =========================================================================

    def detect_doshas(self, chart: ChartData) -> List[DoshaResult]:
        """
        Detect doshas (afflictions) in chart.

        Only implements well-established doshas with clear definitions.
        Always includes cancellation factors.
        """
        doshas = []

        # 1. Manglik Dosha (Mars placement)
        dosha = self._check_manglik(chart)
        if dosha:
            doshas.append(dosha)

        # 2. Kaal Sarp Dosha
        dosha = self._check_kaal_sarp(chart)
        if dosha:
            doshas.append(dosha)

        return doshas

    def _check_manglik(self, chart: ChartData) -> Optional[DoshaResult]:
        """
        Manglik Dosha: Mars in 1, 2, 4, 7, 8, or 12th house.
        """
        mars = chart.planets[Planet.MARS]
        manglik_houses = [1, 2, 4, 7, 8, 12]

        if mars.house not in manglik_houses:
            return None

        # Check cancellation factors
        cancellations = []

        # Mars in own sign cancels
        if mars.sign in OWN_SIGNS.get(Planet.MARS, []):
            cancellations.append("Mars in own sign")

        # Mars in exaltation cancels
        if mars.sign == EXALTATION.get(Planet.MARS):
            cancellations.append("Mars in exaltation")

        # Jupiter aspect on Mars cancels
        jupiter = chart.planets[Planet.JUPITER]
        jupiter_aspects = [jupiter.house, (jupiter.house + 4) % 12 or 12, (jupiter.house + 8) % 12 or 12]
        if mars.house in jupiter_aspects:
            cancellations.append("Jupiter aspects Mars")

        # Venus in 7th cancels for marriage
        venus = chart.planets[Planet.VENUS]
        if venus.house == 7:
            cancellations.append("Venus in 7th house")

        is_cancelled = len(cancellations) > 0
        severity = "mild" if is_cancelled or mars.house in [2, 12] else "moderate"

        return DoshaResult(
            rule_name="Manglik Dosha",
            rule_category="dosha",
            is_active=not is_cancelled,
            conditions=[
                f"Mars in {mars.house}th house",
                f"Mars in {mars.sign.value}"
            ],
            evidence={
                "mars_house": mars.house,
                "mars_sign": mars.sign.value
            },
            confidence=ConfidenceLevel.HIGH if not is_cancelled else ConfidenceLevel.LOW,
            general_effect="May indicate delays or challenges in marriage. Effect depends on overall chart.",
            dosha_type="manglik",
            severity=severity,
            affected_houses=[7, 8],
            affected_planets=[Planet.MARS],
            can_be_cancelled=True,
            cancellation_factors=cancellations,
            disclaimer="Manglik dosha is one factor among many. Matching Manglik charts or other factors can neutralize this."
        )

    def _check_kaal_sarp(self, chart: ChartData) -> Optional[DoshaResult]:
        """
        Kaal Sarp Dosha: All planets between Rahu and Ketu.
        """
        rahu = chart.planets[Planet.RAHU]
        ketu = chart.planets[Planet.KETU]

        rahu_long = rahu.longitude
        ketu_long = ketu.longitude

        all_between = True
        for planet in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                       Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
            p_long = chart.planets[planet].longitude

            # Check if planet is between Rahu and Ketu
            if rahu_long < ketu_long:
                between = rahu_long <= p_long <= ketu_long
            else:
                between = p_long >= rahu_long or p_long <= ketu_long

            if not between:
                all_between = False
                break

        if not all_between:
            return None

        return DoshaResult(
            rule_name="Kaal Sarp Dosha",
            rule_category="dosha",
            is_active=True,
            conditions=[
                "All planets between Rahu and Ketu"
            ],
            evidence={
                "rahu_position": rahu.longitude,
                "ketu_position": ketu.longitude
            },
            confidence=ConfidenceLevel.MEDIUM,
            general_effect="May indicate karmic challenges. Effect varies based on axis and planets involved.",
            dosha_type="kaal_sarp",
            severity="moderate",
            affected_houses=[rahu.house, ketu.house],
            affected_planets=[Planet.RAHU, Planet.KETU],
            can_be_cancelled=True,
            cancellation_factors=["Partial Kaal Sarp if Moon conjunct Rahu/Ketu"],
            disclaimer="This is a complex dosha. Many successful people have this. Effect depends on overall chart strength."
        )

    # =========================================================================
    # VIMSHOTTARI DASHA CALCULATION
    # =========================================================================

    def calculate_dasha(self, chart: ChartData) -> Tuple[Optional[DashaResult], List[DashaResult]]:
        """
        Calculate Vimshottari Dasha periods.

        Returns (current_dasha, list_of_upcoming_dashas).
        """
        moon_nakshatra = chart.moon_nakshatra.name
        moon_degree_in_nak = chart.moon_nakshatra.degree_in_nakshatra

        # Get nakshatra lord (starting dasha)
        nakshatra_lord = NAKSHATRA_LORDS.get(moon_nakshatra, Planet.KETU)

        # Calculate balance at birth
        nakshatra_span = 13.3333
        balance_ratio = (nakshatra_span - moon_degree_in_nak) / nakshatra_span
        first_dasha_years = DASHA_YEARS[nakshatra_lord] * balance_ratio

        # Build dasha sequence from birth
        birth_date = chart.birth_details.date_of_birth
        today = date.today()

        # Find starting index in sequence
        start_idx = DASHA_SEQUENCE.index(nakshatra_lord)

        dashas = []
        current_start = datetime(birth_date.year, birth_date.month, birth_date.day)

        # First dasha (with balance)
        first_end = current_start + timedelta(days=first_dasha_years * 365.25)
        dashas.append({
            "lord": nakshatra_lord,
            "start": current_start.date(),
            "end": first_end.date(),
            "years": first_dasha_years
        })
        current_start = first_end

        # Subsequent dashas
        for i in range(1, 10):  # Full cycle
            idx = (start_idx + i) % 9
            lord = DASHA_SEQUENCE[idx]
            years = DASHA_YEARS[lord]
            end = current_start + timedelta(days=years * 365.25)
            dashas.append({
                "lord": lord,
                "start": current_start.date(),
                "end": end.date(),
                "years": years
            })
            current_start = end

        # Find current dasha
        current_dasha = None
        upcoming_dashas = []

        for d in dashas:
            if d["start"] <= today <= d["end"]:
                current_dasha = DashaResult(
                    dasha_lord=d["lord"],
                    start_date=d["start"],
                    end_date=d["end"],
                    current=True,
                    dasha_lord_strength=0.5,  # Would need more calculation
                    houses_activated=[chart.planets[d["lord"]].house],
                    expected_themes=[f"Themes of {d['lord'].value}"],
                    balance_at_birth=first_dasha_years if d == dashas[0] else None
                )
            elif d["start"] > today:
                upcoming_dashas.append(DashaResult(
                    dasha_lord=d["lord"],
                    start_date=d["start"],
                    end_date=d["end"],
                    current=False,
                    dasha_lord_strength=0.5,
                    houses_activated=[chart.planets[d["lord"]].house],
                    expected_themes=[f"Themes of {d['lord'].value}"]
                ))

        return current_dasha, upcoming_dashas[:5]  # Return next 5

    # =========================================================================
    # ASHTAKOOT MILAN (36-POINT MATCHING)
    # =========================================================================

    def calculate_compatibility(
        self,
        chart1: ChartData,
        chart2: ChartData
    ) -> KundliMatchResult:
        """
        Calculate Ashtakoot Milan compatibility score.
        """
        scores = []

        # 1. Varna (1 point)
        varna_score = VARNA_SCORES.get((chart1.varna, chart2.varna), 0)
        scores.append(CompatibilityScore(
            koota_name="Varna",
            max_points=1,
            obtained_points=varna_score,
            description="Spiritual and work compatibility",
            person1_value=chart1.varna,
            person2_value=chart2.varna,
            reasoning=f"{chart1.varna} with {chart2.varna}"
        ))

        # 2. Vashya (2 points)
        vashya_score = VASHYA_SCORES.get((chart1.vashya, chart2.vashya), 1)
        scores.append(CompatibilityScore(
            koota_name="Vashya",
            max_points=2,
            obtained_points=vashya_score,
            description="Mutual attraction and dominance",
            person1_value=chart1.vashya,
            person2_value=chart2.vashya,
            reasoning=f"{chart1.vashya} with {chart2.vashya}"
        ))

        # 3. Tara (3 points)
        n1_idx = list(Nakshatra).index(chart1.moon_nakshatra.name)
        n2_idx = list(Nakshatra).index(chart2.moon_nakshatra.name)
        diff = abs(n1_idx - n2_idx) % 9
        tara_score = 0 if diff in [3, 5, 7] else (1.5 if diff in [1, 6, 8] else 3)
        scores.append(CompatibilityScore(
            koota_name="Tara",
            max_points=3,
            obtained_points=tara_score,
            description="Birth star compatibility",
            person1_value=chart1.moon_nakshatra.name.value,
            person2_value=chart2.moon_nakshatra.name.value,
            reasoning=f"Nakshatra difference: {diff}"
        ))

        # 4. Yoni (4 points)
        yoni_key = (chart1.yoni, chart2.yoni)
        yoni_score = YONI_SCORES.get(yoni_key, YONI_SCORES.get((chart2.yoni, chart1.yoni), 2))
        scores.append(CompatibilityScore(
            koota_name="Yoni",
            max_points=4,
            obtained_points=yoni_score,
            description="Physical and sexual compatibility",
            person1_value=chart1.yoni,
            person2_value=chart2.yoni,
            reasoning=f"{chart1.yoni} with {chart2.yoni}"
        ))

        # 5. Graha Maitri (5 points)
        lord1 = ZODIAC_LORDS.get(chart1.moon_sign, Planet.MOON)
        lord2 = ZODIAC_LORDS.get(chart2.moon_sign, Planet.MOON)
        maitri_key = (lord1.value, lord2.value)
        maitri_score = MAITRI_SCORES.get(maitri_key, 2.5)
        scores.append(CompatibilityScore(
            koota_name="Graha Maitri",
            max_points=5,
            obtained_points=maitri_score,
            description="Mental and intellectual compatibility",
            person1_value=f"{chart1.moon_sign.value} (lord: {lord1.value})",
            person2_value=f"{chart2.moon_sign.value} (lord: {lord2.value})",
            reasoning=f"{lord1.value}-{lord2.value} relationship"
        ))

        # 6. Gana (6 points)
        gana_key = (chart1.gana, chart2.gana)
        gana_score = GANA_SCORES.get(gana_key, 3)
        scores.append(CompatibilityScore(
            koota_name="Gana",
            max_points=6,
            obtained_points=gana_score,
            description="Temperament compatibility",
            person1_value=chart1.gana,
            person2_value=chart2.gana,
            reasoning=f"{chart1.gana} with {chart2.gana}"
        ))

        # 7. Bhakoot (7 points)
        sign1_idx = list(ZodiacSign).index(chart1.moon_sign) + 1
        sign2_idx = list(ZodiacSign).index(chart2.moon_sign) + 1
        diff = ((sign2_idx - sign1_idx) % 12) + 1
        bhakoot_score = BHAKOOT_SCORES.get((1, diff), 0)
        bhakoot_dosha = bhakoot_score == 0
        scores.append(CompatibilityScore(
            koota_name="Bhakoot",
            max_points=7,
            obtained_points=bhakoot_score,
            description="Love and family prosperity",
            person1_value=chart1.moon_sign.value,
            person2_value=chart2.moon_sign.value,
            reasoning=f"Signs {sign1_idx} and {sign2_idx}, difference {diff}"
        ))

        # 8. Nadi (8 points)
        nadi_score = 0 if chart1.nadi == chart2.nadi else 8
        nadi_dosha = nadi_score == 0
        scores.append(CompatibilityScore(
            koota_name="Nadi",
            max_points=8,
            obtained_points=nadi_score,
            description="Health and genetic compatibility",
            person1_value=chart1.nadi,
            person2_value=chart2.nadi,
            reasoning=f"Same Nadi ({chart1.nadi})" if nadi_dosha else f"Different Nadis"
        ))

        # Calculate total
        total = sum(s.obtained_points for s in scores)
        percentage = round((total / 36) * 100, 1)

        # Verdict
        if total >= 25:
            verdict = "Excellent Match"
            recommendation = "Highly compatible for marriage"
        elif total >= 18:
            verdict = "Good Match"
            recommendation = "Compatible with minor adjustments"
        elif total >= 12:
            verdict = "Average Match"
            recommendation = "Can work with understanding and effort"
        else:
            verdict = "Below Average"
            recommendation = "Detailed analysis recommended before proceeding"

        return KundliMatchResult(
            person1_name=chart1.birth_details.name or "Person 1",
            person1_moon_sign=chart1.moon_sign,
            person1_nakshatra=chart1.moon_nakshatra.name.value,
            person2_name=chart2.birth_details.name or "Person 2",
            person2_moon_sign=chart2.moon_sign,
            person2_nakshatra=chart2.moon_nakshatra.name.value,
            scores=scores,
            total_score=total,
            percentage=percentage,
            verdict=verdict,
            recommendation=recommendation,
            nadi_dosha=nadi_dosha,
            bhakoot_dosha=bhakoot_dosha,
            has_critical_dosha=nadi_dosha or bhakoot_dosha
        )

    # =========================================================================
    # MAIN EVALUATION METHOD
    # =========================================================================

    def evaluate(self, chart: ChartData) -> RulesOutput:
        """
        Run all rules against chart and return structured findings.
        """
        # Calculate dignities
        dignities = [self.calculate_dignity(pos) for pos in chart.planets.values()]

        # Detect yogas
        yogas = self.detect_yogas(chart)

        # Detect doshas
        doshas = self.detect_doshas(chart)

        # Calculate dasha
        current_dasha, upcoming_dashas = self.calculate_dasha(chart)

        # Summary flags
        has_raja = any(y.yoga_type == "raja_yoga" for y in yogas)
        has_dhana = any(y.yoga_type == "dhana_yoga" for y in yogas)
        has_doshas = any(d.is_active for d in doshas)

        # Overall strength based on dignities
        avg_dignity = sum(d.dignity_score for d in dignities) / len(dignities) if dignities else 0
        overall_strength = "strong" if avg_dignity > 0.5 else ("weak" if avg_dignity < -0.5 else "moderate")

        return RulesOutput(
            rules_version=self.rules_version,
            yogas=yogas,
            doshas=doshas,
            dignities=dignities,
            current_dasha=current_dasha,
            upcoming_dashas=upcoming_dashas,
            has_raja_yogas=has_raja,
            has_dhana_yogas=has_dhana,
            has_significant_doshas=has_doshas,
            overall_chart_strength=overall_strength,
            uncertainties=["Birth time accuracy affects house-based calculations"]
        )
