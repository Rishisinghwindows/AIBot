"""
Astrology Service

Provides astrology features including:
- Horoscope (daily/weekly/monthly)
- Birth Chart (Kundli)
- Kundli Matching
- Dosha Check (Manglik, Kaal Sarp, Sade Sati)
- Life Predictions
- Panchang
- Numerology
- Tarot Reading
"""

import logging
import random
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from app.utils.validators import (
    validate_date_string,
    validate_time_string,
    validate_zodiac_sign,
    ValidationError
)

logger = logging.getLogger(__name__)

# Zodiac signs
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Nakshatras (27 lunar mansions)
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Tarot cards
MAJOR_ARCANA = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
    "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
    "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
    "The Devil", "The Tower", "The Star", "The Moon", "The Sun",
    "Judgement", "The World"
]

# Horoscope templates
HOROSCOPE_TEMPLATES = {
    "positive": [
        "Today brings positive energy your way. {focus_area} will be particularly favorable.",
        "The stars align for success in {focus_area}. Trust your instincts today.",
        "A wonderful day ahead! {focus_area} looks especially promising.",
        "Good fortune smiles upon you. Focus on {focus_area} for best results.",
    ],
    "neutral": [
        "A balanced day awaits. Pay attention to {focus_area} for steady progress.",
        "Today calls for patience. {focus_area} may require extra effort.",
        "Mixed energies today. {focus_area} needs careful consideration.",
        "A day for reflection. Consider your approach to {focus_area}.",
    ],
    "challenging": [
        "Some challenges in {focus_area}, but your resilience will see you through.",
        "Be mindful of {focus_area} today. Caution brings rewards.",
        "A testing day for {focus_area}. Stay focused and patient.",
        "Obstacles in {focus_area} are opportunities for growth.",
    ]
}

FOCUS_AREAS = ["career", "relationships", "health", "finances", "personal growth", "creativity"]
LUCKY_COLORS = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange", "White", "Pink", "Gold", "Silver"]


@dataclass
class BirthDetails:
    """Birth details for astrological calculations."""
    date: str  # DD-MM-YYYY
    time: str  # HH:MM
    place: str
    name: Optional[str] = None


class AstrologyService:
    """Service for all astrology-related calculations and predictions."""

    async def get_horoscope(
        self,
        sign: str,
        period: str = "today"
    ) -> Dict[str, Any]:
        """
        Get horoscope for a zodiac sign.

        Args:
            sign: Zodiac sign name
            period: today, tomorrow, weekly, monthly

        Returns:
            Horoscope data
        """
        try:
            sign = validate_zodiac_sign(sign)
        except ValidationError as e:
            return {"success": False, "error": e.message}

        try:
            # Generate horoscope based on sign and period
            seed = hash(f"{sign}{period}{date.today().isoformat()}")
            random.seed(seed)

            mood = random.choice(["positive", "neutral", "challenging"])
            focus = random.choice(FOCUS_AREAS)
            template = random.choice(HOROSCOPE_TEMPLATES[mood])
            horoscope_text = template.format(focus_area=focus)

            # Add period-specific advice
            if period == "weekly":
                horoscope_text += f" This week, focus on building consistency in {random.choice(FOCUS_AREAS)}."
            elif period == "monthly":
                horoscope_text += f" This month brings opportunities in {random.choice(FOCUS_AREAS)}. Plan ahead for success."

            lucky_number = random.randint(1, 99)
            lucky_color = random.choice(LUCKY_COLORS)

            return {
                "success": True,
                "data": {
                    "sign": sign,
                    "period": period,
                    "horoscope": horoscope_text,
                    "lucky_number": lucky_number,
                    "lucky_color": lucky_color,
                    "mood": mood,
                    "focus_area": focus,
                    "date": date.today().isoformat(),
                    "advice": f"Focus on {focus} today for best results."
                }
            }
        except Exception as e:
            logger.error(f"Horoscope error: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_birth_chart(
        self,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Alias for calculate_kundli for API compatibility."""
        return await self.calculate_kundli(birth_date, birth_time, birth_place, name)

    async def calculate_kundli(
        self,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate birth chart (Kundli).

        Args:
            birth_date: Birth date (DD-MM-YYYY)
            birth_time: Birth time (HH:MM)
            birth_place: Birth place

        Returns:
            Kundli data with planetary positions
        """
        try:
            # Validate birth date
            try:
                day, month, year = validate_date_string(
                    birth_date, "birth_date", allow_future=False
                )
            except ValidationError as e:
                return {"success": False, "error": e.message}

            # Validate birth time
            try:
                hour, minute = validate_time_string(birth_time, "birth_time")
            except ValidationError as e:
                return {"success": False, "error": e.message}

            if not birth_place or not birth_place.strip():
                return {"success": False, "error": "Birth place is required"}

            # Calculate basic chart (simplified)
            seed = hash(f"{birth_date}{birth_time}{birth_place}")
            random.seed(seed)

            # Calculate sun sign based on birth date
            sun_sign_index = self._get_sun_sign_index(month, day)
            sun_sign = ZODIAC_SIGNS[sun_sign_index]

            # Other calculations (simplified)
            moon_sign_index = (sun_sign_index + random.randint(0, 11)) % 12
            moon_sign = ZODIAC_SIGNS[moon_sign_index]
            ascendant_index = (sun_sign_index + random.randint(0, 11)) % 12
            ascendant = ZODIAC_SIGNS[ascendant_index]
            nakshatra = random.choice(NAKSHATRAS)
            nakshatra_pada = random.randint(1, 4)

            # Vedic details
            varnas = ["Brahmin", "Kshatriya", "Vaishya", "Shudra"]
            nadis = ["Adi", "Madhya", "Antya"]
            yonis = ["Ashwa", "Gaja", "Mesha", "Sarpa", "Shwan", "Marjar", "Mushak", "Gau", "Mahisha", "Vyaghra", "Mrig", "Vanar", "Nakul", "Simha"]
            ganas = ["Deva", "Manushya", "Rakshasa"]
            vashyas = ["Chatushpad", "Manav", "Jalachara", "Vanachara", "Keeta"]

            # Calculate planetary positions
            planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
            planetary_positions = {}
            for planet in planets:
                p_sign_index = (sun_sign_index + random.randint(0, 11)) % 12
                p_nakshatra = random.choice(NAKSHATRAS)
                planetary_positions[planet] = {
                    "sign": ZODIAC_SIGNS[p_sign_index],
                    "nakshatra": p_nakshatra,
                    "degree": round(random.uniform(0, 30), 2)
                }

            return {
                "success": True,
                "data": {
                    "name": name or "User",
                    "birth_date": birth_date,
                    "birth_time": birth_time,
                    "birth_place": birth_place,
                    "sun_sign": sun_sign,
                    "moon_sign": moon_sign,
                    "ascendant": {"sign": ascendant},
                    "moon_nakshatra": nakshatra,
                    "nakshatra_pada": nakshatra_pada,
                    "varna": random.choice(varnas),
                    "nadi": random.choice(nadis),
                    "yoni": random.choice(yonis),
                    "gana": random.choice(ganas),
                    "vashya": random.choice(vashyas),
                    "planetary_positions": planetary_positions
                }
            }
        except Exception as e:
            logger.error(f"Kundli calculation error: {e}")
            return {"success": False, "error": str(e)}

    def _get_sun_sign_index(self, month: int, day: int) -> int:
        """Get sun sign index based on birth date."""
        dates = [
            (1, 20), (2, 19), (3, 21), (4, 20), (5, 21), (6, 21),
            (7, 23), (8, 23), (9, 23), (10, 23), (11, 22), (12, 22)
        ]
        for i, (m, d) in enumerate(dates):
            if month == m and day <= d:
                return (i - 1) % 12
            elif month == m:
                return i
        return 0

    async def calculate_kundli_matching(
        self,
        person1_dob: str,
        person2_dob: str,
        person1_name: str = "Person 1",
        person2_name: str = "Person 2",
        person1_time: str = "12:00",
        person2_time: str = "12:00",
        person1_place: str = "Delhi",
        person2_place: str = "Delhi"
    ) -> Dict[str, Any]:
        """
        Calculate Kundli matching (Ashtakoot Milan).

        Returns:
            Matching score out of 36 with detailed breakdown
        """
        try:
            # Get kundlis for both persons
            kundli1 = await self.calculate_kundli(person1_dob, person1_time, person1_place, person1_name)
            kundli2 = await self.calculate_kundli(person2_dob, person2_time, person2_place, person2_name)

            if not kundli1["success"] or not kundli2["success"]:
                return {"success": False, "error": "Could not calculate kundli for one or both persons"}

            # Ashtakoot scoring (8 aspects, max 36 points)
            kootas = {
                "varna": {"max": 1, "description": "Spiritual compatibility"},
                "vashya": {"max": 2, "description": "Dominance/control compatibility"},
                "tara": {"max": 3, "description": "Birth star compatibility"},
                "yoni": {"max": 4, "description": "Physical/sexual compatibility"},
                "graha_maitri": {"max": 5, "description": "Mental compatibility"},
                "gana": {"max": 6, "description": "Temperament matching"},
                "bhakoot": {"max": 7, "description": "Love and affection"},
                "nadi": {"max": 8, "description": "Health and genes"}
            }

            seed = hash(f"{person1_dob}{person2_dob}")
            random.seed(seed)

            total_score = 0
            scores = {}
            for koota, info in kootas.items():
                score = random.randint(0, info["max"])
                scores[koota] = {
                    "score": score,
                    "max": info["max"],
                    "description": info["description"]
                }
                total_score += score

            # Calculate percentage and verdict
            percentage = round((total_score / 36) * 100, 1)
            if total_score >= 28:
                verdict = "Excellent Match"
                recommendation = "This is an excellent match with high compatibility in all aspects."
            elif total_score >= 21:
                verdict = "Good Match"
                recommendation = "This is a good match. Minor differences can be worked on."
            elif total_score >= 14:
                verdict = "Average Match"
                recommendation = "Average compatibility. Consider consulting an astrologer for remedies."
            else:
                verdict = "Below Average"
                recommendation = "Low compatibility. Detailed analysis and remedies recommended."

            return {
                "success": True,
                "data": {
                    "person1": {
                        "name": person1_name,
                        "dob": person1_dob,
                        "moon_sign": kundli1["data"]["moon_sign"]
                    },
                    "person2": {
                        "name": person2_name,
                        "dob": person2_dob,
                        "moon_sign": kundli2["data"]["moon_sign"]
                    },
                    "scores": scores,
                    "total_score": total_score,
                    "max_score": 36,
                    "percentage": percentage,
                    "verdict": verdict,
                    "recommendation": recommendation
                }
            }
        except Exception as e:
            logger.error(f"Kundli matching error: {e}")
            return {"success": False, "error": str(e)}

    async def check_dosha(
        self,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        dosha_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check for doshas (Manglik, Kaal Sarp, Sade Sati).

        Args:
            birth_date: Birth date
            birth_time: Birth time
            birth_place: Birth place
            dosha_type: Specific dosha to check (manglik, kaal_sarp, sade_sati, pitra)

        Returns:
            Dosha analysis
        """
        try:
            seed = hash(f"{birth_date}{birth_time}{birth_place}")
            random.seed(seed)

            doshas = {}

            # Manglik Dosha
            if not dosha_type or dosha_type == "manglik":
                is_manglik = random.choice([True, False, False])  # 33% chance
                manglik_intensity = random.choice(["Low", "Medium", "High"]) if is_manglik else None
                doshas["manglik"] = {
                    "present": is_manglik,
                    "intensity": manglik_intensity,
                    "description": "Mars in 1st, 2nd, 4th, 7th, 8th, or 12th house" if is_manglik else "No Manglik dosha",
                    "remedy": "Perform Kumbh Vivah or chant Hanuman Chalisa" if is_manglik else None
                }

            # Kaal Sarp Dosha
            if not dosha_type or dosha_type == "kaal_sarp":
                is_kaal_sarp = random.choice([True, False, False, False])  # 25% chance
                kaal_sarp_type = random.choice(["Anant", "Kulik", "Vasuki", "Shankhpal", "Padma", "Mahapadma"]) if is_kaal_sarp else None
                doshas["kaal_sarp"] = {
                    "present": is_kaal_sarp,
                    "type": kaal_sarp_type,
                    "description": f"{kaal_sarp_type} Kaal Sarp Dosha" if is_kaal_sarp else "No Kaal Sarp dosha",
                    "remedy": "Perform Kaal Sarp Dosha Puja at Trimbakeshwar" if is_kaal_sarp else None
                }

            # Sade Sati
            if not dosha_type or dosha_type == "sade_sati":
                sade_sati_phase = random.choice([None, "Rising", "Peak", "Setting"])
                doshas["sade_sati"] = {
                    "active": sade_sati_phase is not None,
                    "phase": sade_sati_phase,
                    "description": f"Currently in {sade_sati_phase} phase of Sade Sati" if sade_sati_phase else "Sade Sati not active",
                    "remedy": "Worship Lord Shani, donate black items on Saturday" if sade_sati_phase else None
                }

            # Pitra Dosha
            if not dosha_type or dosha_type == "pitra":
                is_pitra = random.choice([True, False, False])
                doshas["pitra"] = {
                    "present": is_pitra,
                    "description": "Ancestral karma affecting current life" if is_pitra else "No Pitra dosha",
                    "remedy": "Perform Pitra Shanti Puja, Tarpan on Amavasya" if is_pitra else None
                }

            return {
                "success": True,
                "data": {
                    "birth_date": birth_date,
                    "birth_time": birth_time,
                    "birth_place": birth_place,
                    "doshas": doshas,
                    "overall_recommendation": "Consult a qualified astrologer for personalized remedies."
                }
            }
        except Exception as e:
            logger.error(f"Dosha check error: {e}")
            return {"success": False, "error": str(e)}

    async def get_life_prediction(
        self,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        prediction_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get life predictions (marriage, career, children, etc.).

        Args:
            prediction_type: general, marriage, career, children, wealth, health, foreign

        Returns:
            Life prediction
        """
        try:
            seed = hash(f"{birth_date}{birth_time}{birth_place}{prediction_type}")
            random.seed(seed)

            predictions = {
                "marriage": {
                    "title": "Marriage Prediction",
                    "favorable_period": f"Age {random.randint(24, 32)}-{random.randint(33, 38)}",
                    "partner_traits": random.choice([
                        "Intelligent and career-oriented",
                        "Artistic and creative",
                        "Traditional and family-oriented",
                        "Adventurous and independent"
                    ]),
                    "compatibility_signs": random.sample(ZODIAC_SIGNS, 3),
                    "advice": "Focus on self-improvement before seeking partnership."
                },
                "career": {
                    "title": "Career Prediction",
                    "favorable_fields": random.sample([
                        "Technology", "Medicine", "Law", "Business", "Arts",
                        "Education", "Finance", "Government", "Research"
                    ], 3),
                    "growth_period": f"Age {random.randint(28, 35)}-{random.randint(40, 50)}",
                    "challenges": random.choice([
                        "Initial slow growth but steady rise",
                        "Competition from peers",
                        "Need for additional skills"
                    ]),
                    "advice": "Continuous learning and networking will boost your career."
                },
                "children": {
                    "title": "Children Prediction",
                    "indication": random.choice([
                        "Blessed with children, likely 1-2",
                        "Strong indication for 2-3 children",
                        "One child indicated, possibly after remedies"
                    ]),
                    "favorable_time": f"Age {random.randint(26, 32)}-{random.randint(35, 40)}",
                    "advice": "Worship Lord Ganesha and Santoshi Mata for blessings."
                },
                "wealth": {
                    "title": "Wealth Prediction",
                    "wealth_potential": random.choice(["High", "Moderate", "Good with effort"]),
                    "sources": random.sample([
                        "Business", "Job", "Investments", "Property", "Inheritance"
                    ], 2),
                    "peak_period": f"Age {random.randint(35, 45)}-{random.randint(50, 60)}",
                    "advice": "Diversify investments and avoid speculation."
                },
                "health": {
                    "title": "Health Prediction",
                    "constitution": random.choice(["Strong", "Moderate", "Needs attention"]),
                    "areas_of_concern": random.sample([
                        "Digestive system", "Respiratory", "Joints", "Stress-related", "Eyes"
                    ], 2),
                    "favorable_practices": ["Yoga", "Meditation", "Regular exercise"],
                    "advice": "Maintain regular health checkups and balanced diet."
                },
                "foreign": {
                    "title": "Foreign Settlement Prediction",
                    "indication": random.choice([
                        "Strong chances of foreign travel/settlement",
                        "Moderate chances, mostly for work",
                        "Short-term foreign stays likely"
                    ]),
                    "favorable_directions": random.sample(["North", "South", "East", "West"], 2),
                    "favorable_period": f"Age {random.randint(25, 35)}-{random.randint(40, 50)}",
                    "advice": "Learn new languages and stay open to opportunities."
                }
            }

            if prediction_type == "general":
                return {
                    "success": True,
                    "data": {
                        "birth_date": birth_date,
                        "prediction_type": "general",
                        "predictions": predictions
                    }
                }
            elif prediction_type in predictions:
                return {
                    "success": True,
                    "data": {
                        "birth_date": birth_date,
                        "prediction_type": prediction_type,
                        "prediction": predictions[prediction_type]
                    }
                }
            else:
                return {"success": False, "error": f"Unknown prediction type: {prediction_type}"}

        except Exception as e:
            logger.error(f"Life prediction error: {e}")
            return {"success": False, "error": str(e)}

    async def get_panchang(
        self,
        date_str: Optional[str] = None,
        place: str = "Delhi"
    ) -> Dict[str, Any]:
        """
        Get Panchang (Hindu calendar) for a date.

        Returns:
            Panchang details including tithi, nakshatra, yoga, karan
        """
        try:
            if date_str:
                parts = date_str.replace("/", "-").split("-")
                if len(parts) == 3:
                    target_date = date(int(parts[2]) if len(parts[2]) == 4 else 2000 + int(parts[2]),
                                       int(parts[1]), int(parts[0]))
                else:
                    target_date = date.today()
            else:
                target_date = date.today()

            seed = hash(f"{target_date.isoformat()}{place}")
            random.seed(seed)

            # Tithi (15 in each fortnight)
            tithis = [
                "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
                "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
                "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
            ]
            paksha = random.choice(["Shukla (Waxing)", "Krishna (Waning)"])
            tithi = random.choice(tithis)

            # Nakshatra
            nakshatra = random.choice(NAKSHATRAS)
            nakshatra_pada = random.randint(1, 4)

            # Yoga (27 yogas)
            yogas = [
                "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
                "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
                "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra"
            ]
            yoga = random.choice(yogas)

            # Karan (11 karans)
            karans = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"]
            karan1 = random.choice(karans)
            karan2 = random.choice(karans)

            # Moon sign for the day
            moon_sign = random.choice(ZODIAC_SIGNS)

            # Sunrise/sunset times (approximate for India)
            sunrise_hour = random.randint(5, 6)
            sunrise = f"{sunrise_hour}:{random.randint(10, 50):02d} AM"
            sunset_hour = random.randint(5, 7)
            sunset = f"{sunset_hour}:{random.randint(10, 50):02d} PM"

            # Rahu Kaal
            rahu_times = {
                0: "4:30 PM - 6:00 PM",  # Sunday
                1: "7:30 AM - 9:00 AM",  # Monday
                2: "3:00 PM - 4:30 PM",  # Tuesday
                3: "12:00 PM - 1:30 PM",  # Wednesday
                4: "1:30 PM - 3:00 PM",  # Thursday
                5: "10:30 AM - 12:00 PM",  # Friday
                6: "9:00 AM - 10:30 AM"  # Saturday
            }
            rahu_kaal = rahu_times[target_date.weekday()]

            return {
                "success": True,
                "data": {
                    "date": target_date.isoformat(),
                    "day": target_date.strftime("%A"),
                    "location": place,
                    "tithi": {
                        "name": tithi,
                        "paksha": paksha
                    },
                    "nakshatra": {
                        "name": nakshatra,
                        "pada": nakshatra_pada
                    },
                    "yoga": yoga,
                    "karan": [karan1, karan2],
                    "moon_sign": moon_sign,
                    "sunrise": sunrise,
                    "sunset": sunset,
                    "rahu_kaal": rahu_kaal,
                    "auspicious_time": f"{random.randint(9, 11)}:00 AM - {random.randint(2, 5)}:00 PM"
                }
            }
        except Exception as e:
            logger.error(f"Panchang error: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_numerology(
        self,
        name: Optional[str] = None,
        birth_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate numerology for name and birth date.

        Returns:
            Name number, life path number, and interpretations
        """
        try:
            # Calculate name number (Pythagorean system)
            letter_values = {
                'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
                'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
                's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8
            }

            name_number = None
            if name:
                name_sum = sum(letter_values.get(c.lower(), 0) for c in name if c.isalpha())
                name_number = self._reduce_to_single(name_sum) if name_sum > 0 else None

            # Calculate life path number from birth date
            life_path_number = None
            if birth_date:
                digits = [int(d) for d in birth_date if d.isdigit()]
                life_path_number = self._reduce_to_single(sum(digits))

            # Number meanings
            meanings = {
                1: {"trait": "Leader", "description": "Natural born leader, independent, ambitious"},
                2: {"trait": "Peacemaker", "description": "Diplomatic, cooperative, sensitive"},
                3: {"trait": "Creative", "description": "Expressive, artistic, optimistic"},
                4: {"trait": "Builder", "description": "Practical, hardworking, disciplined"},
                5: {"trait": "Adventurer", "description": "Freedom-loving, versatile, curious"},
                6: {"trait": "Nurturer", "description": "Responsible, caring, family-oriented"},
                7: {"trait": "Seeker", "description": "Analytical, spiritual, introspective"},
                8: {"trait": "Achiever", "description": "Ambitious, successful, material-focused"},
                9: {"trait": "Humanitarian", "description": "Compassionate, generous, idealistic"}
            }

            result = {
                "success": True,
                "data": {}
            }

            if name and name_number:
                result["data"]["name"] = name
                result["data"]["name_number"] = name_number
                result["data"]["name_meaning"] = meanings.get(name_number, {"trait": "Special", "description": "Unique qualities"})

            if life_path_number:
                result["data"]["birth_date"] = birth_date
                result["data"]["life_path_number"] = life_path_number
                result["data"]["life_path_meaning"] = meanings.get(life_path_number, {"trait": "Special", "description": "Unique qualities"})

            # Calculate lucky numbers based on available numbers
            base_number = name_number or life_path_number or 5  # Default to 5 if neither available
            result["data"]["lucky_numbers"] = [base_number, (base_number + 3) % 9 + 1, (base_number + 6) % 9 + 1]

            return result
        except Exception as e:
            logger.error(f"Numerology error: {e}")
            return {"success": False, "error": str(e)}

    def _reduce_to_single(self, num: int) -> int:
        """Reduce a number to single digit (1-9) by adding digits."""
        while num > 9:
            num = sum(int(d) for d in str(num))
        return num

    async def draw_tarot(
        self,
        question: Optional[str] = None,
        spread_type: str = "three_card"
    ) -> Dict[str, Any]:
        """
        Draw tarot cards and provide interpretation.

        Args:
            question: User's question
            spread_type: single, three_card, celtic_cross

        Returns:
            Drawn cards with interpretation
        """
        try:
            # Determine number of cards based on spread
            if spread_type == "single":
                num_cards = 1
                positions = ["Your Card"]
            elif spread_type == "three_card":
                num_cards = 3
                positions = ["Past", "Present", "Future"]
            elif spread_type == "celtic_cross":
                num_cards = 10
                positions = [
                    "Present", "Challenge", "Past", "Future", "Above",
                    "Below", "Advice", "External", "Hopes/Fears", "Outcome"
                ]
            else:
                num_cards = 3
                positions = ["Past", "Present", "Future"]

            # Draw random cards
            seed = hash(f"{question}{datetime.now().isoformat()}")
            random.seed(seed)
            drawn_cards = random.sample(MAJOR_ARCANA, min(num_cards, len(MAJOR_ARCANA)))

            cards = []
            for i, card in enumerate(drawn_cards):
                is_reversed = random.choice([True, False])
                cards.append({
                    "position": positions[i] if i < len(positions) else f"Card {i+1}",
                    "card": card,
                    "reversed": is_reversed,
                    "meaning": self._get_tarot_meaning(card, is_reversed)
                })

            # Generate interpretation
            interpretation = self._generate_tarot_interpretation(cards, question)

            return {
                "success": True,
                "data": {
                    "spread_type": spread_type,
                    "question": question,
                    "cards": cards,
                    "interpretation": interpretation
                }
            }
        except Exception as e:
            logger.error(f"Tarot error: {e}")
            return {"success": False, "error": str(e)}

    def _get_tarot_meaning(self, card: str, reversed: bool) -> str:
        """Get meaning for a tarot card."""
        meanings = {
            "The Fool": ("New beginnings, innocence, spontaneity", "Recklessness, fear of change"),
            "The Magician": ("Manifestation, resourcefulness, power", "Manipulation, untapped talents"),
            "The High Priestess": ("Intuition, mystery, inner knowledge", "Secrets, disconnection from intuition"),
            "The Empress": ("Abundance, nurturing, creativity", "Dependence, smothering, emptiness"),
            "The Emperor": ("Authority, structure, leadership", "Tyranny, rigidity, lack of discipline"),
            "The Lovers": ("Love, harmony, choices", "Imbalance, misalignment, poor choices"),
            "The Chariot": ("Determination, willpower, success", "Aggression, lack of direction"),
            "Strength": ("Courage, patience, inner strength", "Self-doubt, weakness, insecurity"),
            "The Hermit": ("Soul-searching, introspection, guidance", "Isolation, loneliness, withdrawal"),
            "Wheel of Fortune": ("Change, cycles, destiny", "Bad luck, resistance to change"),
            "Justice": ("Fairness, truth, law", "Unfairness, dishonesty, lack of accountability"),
            "The Hanged Man": ("Surrender, letting go, new perspective", "Stalling, resistance, indecision"),
            "Death": ("Endings, transformation, transition", "Resistance to change, fear of endings"),
            "Temperance": ("Balance, moderation, patience", "Imbalance, excess, lack of harmony"),
            "The Devil": ("Shadow self, attachment, addiction", "Releasing limiting beliefs, freedom"),
            "The Tower": ("Sudden change, upheaval, revelation", "Fear of change, avoiding disaster"),
            "The Star": ("Hope, faith, renewal", "Lack of faith, despair, disconnection"),
            "The Moon": ("Illusion, fear, subconscious", "Release of fear, clarity"),
            "The Sun": ("Joy, success, vitality", "Inner child issues, overly optimistic"),
            "Judgement": ("Reflection, reckoning, awakening", "Self-doubt, refusal to learn"),
            "The World": ("Completion, achievement, wholeness", "Incompletion, lack of closure")
        }
        upright, rev = meanings.get(card, ("Unique energy", "Blocked energy"))
        return rev if reversed else upright

    def _generate_tarot_interpretation(self, cards: List[Dict], question: Optional[str]) -> str:
        """Generate overall tarot interpretation."""
        if len(cards) == 1:
            card = cards[0]
            return f"The {card['card']} {'(reversed)' if card['reversed'] else ''} suggests: {card['meaning']}. Trust your intuition as you move forward."

        # Multi-card interpretation
        past = cards[0] if len(cards) > 0 else None
        present = cards[1] if len(cards) > 1 else None
        future = cards[2] if len(cards) > 2 else None

        parts = []
        if past:
            parts.append(f"Your past influence ({past['card']}) shows: {past['meaning']}.")
        if present:
            parts.append(f"Currently ({present['card']}): {present['meaning']}.")
        if future:
            parts.append(f"Looking ahead ({future['card']}): {future['meaning']}.")

        parts.append("Reflect on these messages and trust your inner wisdom.")
        return " ".join(parts)

    async def ask_astrologer(
        self,
        question: str,
        user_sign: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer general astrology questions.

        Returns:
            AI-generated astrology answer
        """
        try:
            # This would typically use an LLM, but for now we provide template answers
            question_lower = question.lower()

            # Common astrology Q&A
            if "retrograde" in question_lower:
                answer = "Mercury retrograde is when Mercury appears to move backward in its orbit. It's a time to reflect, review, and revisit rather than start new ventures. Communication and technology may face challenges. Use this period for introspection and tying up loose ends."
            elif "gemstone" in question_lower or "stone" in question_lower:
                if user_sign:
                    stones = {
                        "Aries": "Red Coral (Moonga)",
                        "Taurus": "Diamond (Heera)",
                        "Gemini": "Emerald (Panna)",
                        "Cancer": "Pearl (Moti)",
                        "Leo": "Ruby (Manik)",
                        "Virgo": "Emerald (Panna)",
                        "Libra": "Diamond (Heera)",
                        "Scorpio": "Red Coral (Moonga)",
                        "Sagittarius": "Yellow Sapphire (Pukhraj)",
                        "Capricorn": "Blue Sapphire (Neelam)",
                        "Aquarius": "Blue Sapphire (Neelam)",
                        "Pisces": "Yellow Sapphire (Pukhraj)"
                    }
                    stone = stones.get(user_sign.capitalize(), "consult an astrologer for your birth chart")
                    answer = f"For {user_sign.capitalize()}, the recommended gemstone is {stone}. Always wear gemstones after consulting with a qualified astrologer who can analyze your complete birth chart."
                else:
                    answer = "The right gemstone depends on your birth chart. Generally, each zodiac sign has associated gemstones, but a detailed analysis of planetary positions is essential. Please share your zodiac sign or birth details for a specific recommendation."
            elif "manglik" in question_lower or "mangal" in question_lower:
                answer = "Manglik dosha occurs when Mars is placed in the 1st, 2nd, 4th, 7th, 8th, or 12th house in the birth chart. It can affect marriage compatibility. Remedies include Kumbh Vivah (marriage to a banana tree or pot), wearing red coral, or marrying another Manglik. The intensity varies based on other planetary aspects."
            elif "sade sati" in question_lower:
                answer = "Sade Sati is a 7.5-year period when Saturn transits through the 12th, 1st, and 2nd houses from your moon sign. It brings challenges but also opportunities for growth. Remedies include worshipping Lord Shani, reciting Shani mantras, and donating black items on Saturdays."
            else:
                answer = f"Thank you for your astrology question: '{question}'. Astrology is a vast subject combining planetary positions, houses, and their interactions. For a detailed answer, please provide your birth details (date, time, place) so I can analyze your specific chart. In general, remember that astrology provides guidance, but free will and karma shape your destiny."

            return {
                "success": True,
                "data": {
                    "question": question,
                    "answer": answer,
                    "user_sign": user_sign
                }
            }
        except Exception as e:
            logger.error(f"Ask astrologer error: {e}")
            return {"success": False, "error": str(e)}


# Helper functions for calculating moon sign and nakshatra from birth details


def calculate_moon_sign(birth_date: str, birth_time: str) -> Optional[str]:
    """
    Calculate moon sign from birth date and time.

    This is a simplified calculation. For accurate results,
    a full ephemeris calculation would be needed.

    Args:
        birth_date: Birth date in DD-MM-YYYY format
        birth_time: Birth time in HH:MM format

    Returns:
        Moon sign name or None if calculation fails
    """
    try:
        # Parse date
        parts = birth_date.replace("/", "-").split("-")
        if len(parts) != 3:
            return None

        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])

        # Parse time
        time_parts = birth_time.split(":")
        if len(time_parts) != 2:
            return None

        hour, minute = int(time_parts[0]), int(time_parts[1])

        # Simplified calculation based on lunar cycle
        # The moon moves through all 12 signs in ~27.3 days
        # So roughly 2.27 days per sign

        # Use a deterministic but varied calculation
        import hashlib
        seed_str = f"{year}-{month:02d}-{day:02d}-{hour:02d}-{minute:02d}"
        hash_value = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)

        # Calculate based on date within lunar month (simplified)
        day_offset = (year * 365 + month * 30 + day + hour / 24) % 27.3
        moon_index = int((day_offset / 27.3) * 12 + hash_value % 3) % 12

        return ZODIAC_SIGNS[moon_index]
    except Exception:
        return None


def calculate_nakshatra(birth_date: str, birth_time: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Calculate nakshatra and pada from birth date and time.

    This is a simplified calculation. For accurate results,
    a full ephemeris calculation would be needed.

    Args:
        birth_date: Birth date in DD-MM-YYYY format
        birth_time: Birth time in HH:MM format

    Returns:
        Tuple of (nakshatra name, pada number 1-4) or (None, None) if calculation fails
    """
    try:
        # Parse date
        parts = birth_date.replace("/", "-").split("-")
        if len(parts) != 3:
            return None, None

        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])

        # Parse time
        time_parts = birth_time.split(":")
        if len(time_parts) != 2:
            return None, None

        hour, minute = int(time_parts[0]), int(time_parts[1])

        # Simplified calculation based on lunar position
        # The moon traverses 27 nakshatras in ~27.3 days
        # So roughly 1 nakshatra per day

        import hashlib
        seed_str = f"{year}-{month:02d}-{day:02d}-{hour:02d}-{minute:02d}-nakshatra"
        hash_value = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)

        # Calculate nakshatra index
        day_offset = (year * 365 + month * 30 + day + hour / 24 + minute / 1440)
        nakshatra_position = (day_offset % 27.3)
        nakshatra_index = int(nakshatra_position + hash_value % 2) % 27

        # Calculate pada (1-4)
        pada = int((nakshatra_position % 1) * 4) + 1
        pada = min(4, max(1, pada))

        return NAKSHATRAS[nakshatra_index], pada
    except Exception:
        return None, None


def get_sun_sign_from_date(month: int, day: int) -> str:
    """
    Get sun sign (zodiac sign) from birth month and day.

    Args:
        month: Birth month (1-12)
        day: Birth day (1-31)

    Returns:
        Sun sign name
    """
    # Zodiac date boundaries
    zodiac_dates = [
        (1, 20, "Aquarius"), (2, 19, "Pisces"), (3, 21, "Aries"),
        (4, 20, "Taurus"), (5, 21, "Gemini"), (6, 21, "Cancer"),
        (7, 23, "Leo"), (8, 23, "Virgo"), (9, 23, "Libra"),
        (10, 23, "Scorpio"), (11, 22, "Sagittarius"), (12, 22, "Capricorn"),
    ]

    for i, (m, d, sign) in enumerate(zodiac_dates):
        if month == m and day < d:
            # Use previous sign
            prev_index = (i - 1) % len(zodiac_dates)
            return zodiac_dates[prev_index][2]
        elif month == m and day >= d:
            return sign

    # Default for edge cases
    return "Capricorn"


# Singleton instance
_astrology_service: Optional[AstrologyService] = None


def get_astrology_service() -> AstrologyService:
    """Get singleton astrology service instance."""
    global _astrology_service
    if _astrology_service is None:
        _astrology_service = AstrologyService()
    return _astrology_service