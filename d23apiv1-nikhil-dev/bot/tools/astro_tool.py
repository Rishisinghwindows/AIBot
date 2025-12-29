"""
Comprehensive Vedic Astrology Tool

All calculations are done locally using Swiss Ephemeris (pyswisseph).
No external APIs required.

Features:
1. Birth Chart (Kundli) - Complete Vedic birth chart with planetary positions
2. Kundli Matching (Ashtakoot Milan) - 36-point compatibility analysis
3. Panchang - Daily Vedic calendar (Tithi, Nakshatra, Yoga, Karan, Paksha)
4. Horoscope - Nakshatra-based daily predictions
5. Numerology - Name and birth date analysis
6. Tarot Reading - AI-generated tarot interpretations
"""

import random
from typing import Optional, Dict, Tuple, Any
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from bot.config import get_settings
from bot.state import ToolResult

# Try to import Swiss Ephemeris, fall back to simplified calculations if not available
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False

# Try to import geopy for geocoding
try:
    from geopy.geocoders import Nominatim
    HAS_GEOPY = True
except ImportError:
    HAS_GEOPY = False


# =============================================================================
# CONSTANTS & LOOKUP TABLES
# =============================================================================

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

ZODIAC_SIGNS_HINDI = [
    "Mesh", "Vrishabh", "Mithun", "Kark", "Singh", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"
]

# Hindi script Rashi names
ZODIAC_SIGNS_HINDI_SCRIPT = [
    "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"
]

# Kannada script Rashi names
ZODIAC_SIGNS_KANNADA_SCRIPT = [
    "ಮೇಷ", "ವೃಷಭ", "ಮಿಥುನ", "ಕರ್ಕ", "ಸಿಂಹ", "ಕನ್ಯಾ",
    "ತುಲಾ", "ವೃಶ್ಚಿಕ", "ಧನು", "ಮಕರ", "ಕುಂಭ", "ಮೀನ"
]

# Tamil script Rashi names
ZODIAC_SIGNS_TAMIL_SCRIPT = [
    "மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி",
    "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"
]

# Telugu script Rashi names
ZODIAC_SIGNS_TELUGU_SCRIPT = [
    "మేషం", "వృషభం", "మిథునం", "కర్కాటకం", "సింహం", "కన్య",
    "తుల", "వృశ్చికం", "ధనస్సు", "మకరం", "కుంభం", "మీనం"
]

# Bengali script Rashi names
ZODIAC_SIGNS_BENGALI_SCRIPT = [
    "মেষ", "বৃষ", "মিথুন", "কর্কট", "সিংহ", "কন্যা",
    "তুলা", "বৃশ্চিক", "ধনু", "মকর", "কুম্ভ", "মীন"
]

# Malayalam script Rashi names
ZODIAC_SIGNS_MALAYALAM_SCRIPT = [
    "മേടം", "ഇടവം", "മിഥുനം", "കർക്കടകം", "ചിങ്ങം", "കന്നി",
    "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം"
]

# Punjabi (Gurmukhi) script Rashi names
ZODIAC_SIGNS_PUNJABI_SCRIPT = [
    "ਮੇਖ", "ਬ੍ਰਿਖ", "ਮਿਥੁਨ", "ਕਰਕ", "ਸਿੰਘ", "ਕੰਨਿਆ",
    "ਤੁਲਾ", "ਬ੍ਰਿਸ਼ਚਕ", "ਧਨੁ", "ਮਕਰ", "ਕੁੰਭ", "ਮੀਨ"
]

# Odia script Rashi names
ZODIAC_SIGNS_ODIA_SCRIPT = [
    "ମେଷ", "ବୃଷ", "ମିଥୁନ", "କର୍କଟ", "ସିଂହ", "କନ୍ୟା",
    "ତୁଳା", "ବୃଶ୍ଚିକ", "ଧନୁ", "ମକର", "କୁମ୍ଭ", "ମୀନ"
]

# Combined dictionary for all scripts
ALL_ZODIAC_SCRIPTS = {
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_HINDI_SCRIPT)},
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_KANNADA_SCRIPT)},
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_TAMIL_SCRIPT)},
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_TELUGU_SCRIPT)},
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_BENGALI_SCRIPT)},
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_MALAYALAM_SCRIPT)},
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_PUNJABI_SCRIPT)},
    **{sign: ZODIAC_SIGNS[i] for i, sign in enumerate(ZODIAC_SIGNS_ODIA_SCRIPT)},
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Nakshatra predictions data
NAKSHATRA_DATA = {
    "Ashwini": {"description": "Dynamic and spontaneous. Focus on beginnings.", "lucky_number": 3, "lucky_color": "Yellow", "advice": "Take bold steps forward!"},
    "Bharani": {"description": "Determined and strong-willed. Be cautious of overcommitment.", "lucky_number": 9, "lucky_color": "Orange", "advice": "Balance your energy for effective outcomes."},
    "Krittika": {"description": "Sharp and fiery. A day to focus on cutting through challenges.", "lucky_number": 1, "lucky_color": "Red", "advice": "Use your energy wisely."},
    "Rohini": {"description": "Creative and nurturing. Enjoy the comforts of life.", "lucky_number": 6, "lucky_color": "Pink", "advice": "Focus on building relationships."},
    "Mrigashira": {"description": "Curious and exploratory. A great day for learning.", "lucky_number": 5, "lucky_color": "Green", "advice": "Stay curious and keep exploring."},
    "Ardra": {"description": "Dynamic and intense. Embrace the changes in your life.", "lucky_number": 7, "lucky_color": "Blue", "advice": "Channel your energy productively."},
    "Punarvasu": {"description": "Optimistic and nurturing. Look forward to new opportunities.", "lucky_number": 4, "lucky_color": "White", "advice": "Be open to second chances."},
    "Pushya": {"description": "Supportive and reliable. Focus on building a strong foundation.", "lucky_number": 8, "lucky_color": "Yellow", "advice": "Offer help to those in need."},
    "Ashlesha": {"description": "Intelligent and resourceful. A good day for problem-solving.", "lucky_number": 2, "lucky_color": "Purple", "advice": "Trust your instincts and intuition."},
    "Magha": {"description": "Proud and regal. A day to embrace leadership roles.", "lucky_number": 10, "lucky_color": "Gold", "advice": "Take charge with confidence."},
    "Purva Phalguni": {"description": "Playful and indulgent. A day for relaxation and joy.", "lucky_number": 6, "lucky_color": "Peach", "advice": "Spend time with loved ones."},
    "Uttara Phalguni": {"description": "Generous and organized. A great day to plan ahead.", "lucky_number": 9, "lucky_color": "Maroon", "advice": "Help others while managing your priorities."},
    "Hasta": {"description": "Skillful and clever. A day to complete tasks efficiently.", "lucky_number": 1, "lucky_color": "Silver", "advice": "Use your talents to solve challenges."},
    "Chitra": {"description": "Creative and vibrant. A good day to showcase your talents.", "lucky_number": 7, "lucky_color": "Red", "advice": "Let your creativity shine."},
    "Swati": {"description": "Independent and adaptable. A great day for new ventures.", "lucky_number": 5, "lucky_color": "Blue", "advice": "Trust your ability to adapt."},
    "Vishakha": {"description": "Ambitious and determined. A day to push towards your goals.", "lucky_number": 8, "lucky_color": "Green", "advice": "Stay focused and determined."},
    "Anuradha": {"description": "Supportive and disciplined. Focus on teamwork.", "lucky_number": 4, "lucky_color": "Black", "advice": "Collaborate with others for success."},
    "Jyeshtha": {"description": "Powerful and protective. A day to assert your boundaries.", "lucky_number": 3, "lucky_color": "Purple", "advice": "Stand firm and be assertive."},
    "Mula": {"description": "Deep and transformative. Embrace the changes within.", "lucky_number": 6, "lucky_color": "Brown", "advice": "Let go of what no longer serves you."},
    "Purva Ashadha": {"description": "Optimistic and forward-looking. A great day for planning.", "lucky_number": 2, "lucky_color": "Pink", "advice": "Set clear goals for the future."},
    "Uttara Ashadha": {"description": "Determined and focused. A good day for hard work.", "lucky_number": 9, "lucky_color": "Orange", "advice": "Persevere and you will succeed."},
    "Shravana": {"description": "Wise and thoughtful. Focus on gaining knowledge.", "lucky_number": 7, "lucky_color": "White", "advice": "Take time to learn and reflect."},
    "Dhanishta": {"description": "Energetic and ambitious. A great day for achieving goals.", "lucky_number": 5, "lucky_color": "Red", "advice": "Act with confidence and energy."},
    "Shatabhisha": {"description": "Mysterious and introspective. A day to focus inward.", "lucky_number": 10, "lucky_color": "Blue", "advice": "Take time for self-reflection."},
    "Purva Bhadrapada": {"description": "Visionary and thoughtful. A great day to plan long-term.", "lucky_number": 8, "lucky_color": "Silver", "advice": "Think big and set ambitious goals."},
    "Uttara Bhadrapada": {"description": "Compassionate and steady. Focus on emotional balance.", "lucky_number": 4, "lucky_color": "Green", "advice": "Be patient and empathetic."},
    "Revati": {"description": "Gentle and nurturing. A day to care for others.", "lucky_number": 3, "lucky_color": "White", "advice": "Offer kindness and support to those in need."}
}

# Varna mapping (based on Moon sign)
VARNA_MAPPING = {
    "Brahmin": ["Cancer", "Scorpio", "Pisces"],
    "Kshatriya": ["Aries", "Leo", "Sagittarius"],
    "Vaishya": ["Taurus", "Virgo", "Capricorn"],
    "Shudra": ["Gemini", "Libra", "Aquarius"]
}

# Nadi mapping (based on Nakshatra)
NADI_MAPPING = {
    "Adi": ["Ashwini", "Ardra", "Punarvasu", "Uttara Phalguni", "Hasta", "Jyeshtha", "Mula", "Shatabhisha", "Purva Bhadrapada"],
    "Madhya": ["Bharani", "Mrigashira", "Pushya", "Purva Phalguni", "Chitra", "Anuradha", "Purva Ashadha", "Dhanishta", "Uttara Bhadrapada"],
    "Antya": ["Krittika", "Rohini", "Ashlesha", "Magha", "Swati", "Vishakha", "Uttara Ashadha", "Shravana", "Revati"]
}

# Yoni mapping (Nakshatra to Animal)
YONI_MAPPING = {
    "Ashwini": "Horse", "Bharani": "Elephant", "Krittika": "Sheep", "Rohini": "Serpent",
    "Mrigashira": "Serpent", "Ardra": "Dog", "Punarvasu": "Cat", "Pushya": "Goat",
    "Ashlesha": "Cat", "Magha": "Rat", "Purva Phalguni": "Rat", "Uttara Phalguni": "Cow",
    "Hasta": "Buffalo", "Chitra": "Tiger", "Swati": "Buffalo", "Vishakha": "Tiger",
    "Anuradha": "Deer", "Jyeshtha": "Deer", "Mula": "Dog", "Purva Ashadha": "Monkey",
    "Uttara Ashadha": "Mongoose", "Shravana": "Monkey", "Dhanishta": "Lion",
    "Shatabhisha": "Horse", "Purva Bhadrapada": "Lion", "Uttara Bhadrapada": "Cow",
    "Revati": "Elephant"
}

# Gana mapping (Nakshatra to Temperament)
GANA_MAPPING = {
    "Deva": ["Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Swati", "Anuradha", "Shravana", "Revati"],
    "Manushya": ["Bharani", "Rohini", "Ardra", "Purva Phalguni", "Uttara Phalguni", "Purva Ashadha", "Uttara Ashadha", "Purva Bhadrapada", "Uttara Bhadrapada"],
    "Rakshasa": ["Krittika", "Ashlesha", "Magha", "Chitra", "Vishakha", "Jyeshtha", "Mula", "Dhanishta", "Shatabhisha"]
}

# Vashya mapping
VASHYA_MAPPING = {
    "Human": ["Gemini", "Virgo", "Libra", "Aquarius"],
    "Quadruped": ["Aries", "Taurus", "Sagittarius", "Capricorn"],
    "Water": ["Cancer", "Pisces"],
    "Wild Animal": ["Leo"],
    "Insect": ["Scorpio"]
}

# Rashi Lord mapping
RASHI_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
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
    "Trayodashi", "Chaturdashi", "Purnima", "Pratipada", "Dvitiya", "Tritiya",
    "Chaturthi", "Panchami", "Shasthi", "Saptami", "Ashtami", "Navami",
    "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

# Karan names
KARANS = [
    ["Kimstughna", "Bava"], ["Baalav", "Kaulav"], ["Taitil", "Gar"], ["Vanij", "Vishti"],
    ["Bava", "Baalav"], ["Kaulav", "Taitil"], ["Gar", "Vanij"], ["Vishti", "Bava"],
    ["Baalav", "Kaulav"], ["Taitil", "Gar"], ["Vanij", "Vishti"], ["Bava", "Baalav"],
    ["Kaulav", "Taitil"], ["Gar", "Vanij"], ["Vishti", "Bava"],
    # Krishna Paksha
    ["Baalav", "Kaulav"], ["Taitil", "Gar"], ["Vanij", "Vishti"], ["Bava", "Baalav"],
    ["Kaulav", "Taitil"], ["Gar", "Vanij"], ["Vishti", "Bava"], ["Baalav", "Kaulav"],
    ["Taitil", "Gar"], ["Vanij", "Vishti"], ["Bava", "Baalav"], ["Kaulav", "Taitil"],
    ["Gar", "Vanij"], ["Vishti", "Shakuni"], ["Chatushpada", "Naga"]
]

# Kundli Milan Score Matrices
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

# Yoni compatibility scores
YONI_SCORES = {
    ("Horse", "Horse"): 4, ("Horse", "Elephant"): 2, ("Horse", "Goat"): 2, ("Horse", "Serpent"): 3,
    ("Horse", "Dog"): 2, ("Horse", "Cat"): 2, ("Horse", "Rat"): 2, ("Horse", "Cow"): 1,
    ("Horse", "Buffalo"): 0, ("Horse", "Tiger"): 1, ("Horse", "Monkey"): 3, ("Horse", "Mongoose"): 2,
    ("Horse", "Lion"): 1, ("Horse", "Deer"): 2, ("Horse", "Sheep"): 2,
    ("Elephant", "Elephant"): 4, ("Elephant", "Goat"): 3, ("Elephant", "Serpent"): 3,
    ("Elephant", "Dog"): 2, ("Elephant", "Cat"): 2, ("Elephant", "Rat"): 2, ("Elephant", "Cow"): 2,
    ("Elephant", "Buffalo"): 3, ("Elephant", "Tiger"): 1, ("Elephant", "Monkey"): 3,
    ("Elephant", "Mongoose"): 2, ("Elephant", "Lion"): 0, ("Elephant", "Deer"): 2, ("Elephant", "Sheep"): 3,
    ("Goat", "Goat"): 4, ("Goat", "Serpent"): 2, ("Goat", "Dog"): 1, ("Goat", "Cat"): 2,
    ("Goat", "Rat"): 1, ("Goat", "Cow"): 3, ("Goat", "Buffalo"): 3, ("Goat", "Tiger"): 1,
    ("Goat", "Monkey"): 3, ("Goat", "Mongoose"): 0, ("Goat", "Lion"): 2, ("Goat", "Deer"): 2, ("Goat", "Sheep"): 4,
    ("Serpent", "Serpent"): 4, ("Serpent", "Dog"): 2, ("Serpent", "Cat"): 1, ("Serpent", "Rat"): 1,
    ("Serpent", "Cow"): 1, ("Serpent", "Buffalo"): 2, ("Serpent", "Tiger"): 2, ("Serpent", "Monkey"): 2,
    ("Serpent", "Mongoose"): 0, ("Serpent", "Lion"): 1, ("Serpent", "Deer"): 2, ("Serpent", "Sheep"): 2,
    ("Dog", "Dog"): 4, ("Dog", "Cat"): 2, ("Dog", "Rat"): 1, ("Dog", "Cow"): 2, ("Dog", "Buffalo"): 1,
    ("Dog", "Tiger"): 2, ("Dog", "Monkey"): 2, ("Dog", "Mongoose"): 1, ("Dog", "Lion"): 1,
    ("Dog", "Deer"): 1, ("Dog", "Sheep"): 1,
    ("Cat", "Cat"): 4, ("Cat", "Rat"): 0, ("Cat", "Cow"): 2, ("Cat", "Buffalo"): 2, ("Cat", "Tiger"): 1,
    ("Cat", "Monkey"): 3, ("Cat", "Mongoose"): 2, ("Cat", "Lion"): 1, ("Cat", "Deer"): 2, ("Cat", "Sheep"): 2,
    ("Rat", "Rat"): 4, ("Rat", "Cow"): 2, ("Rat", "Buffalo"): 2, ("Rat", "Tiger"): 1, ("Rat", "Monkey"): 2,
    ("Rat", "Mongoose"): 1, ("Rat", "Lion"): 2, ("Rat", "Deer"): 1, ("Rat", "Sheep"): 1,
    ("Cow", "Cow"): 4, ("Cow", "Buffalo"): 3, ("Cow", "Tiger"): 0, ("Cow", "Monkey"): 2,
    ("Cow", "Mongoose"): 2, ("Cow", "Lion"): 1, ("Cow", "Deer"): 2, ("Cow", "Sheep"): 3,
    ("Buffalo", "Buffalo"): 4, ("Buffalo", "Tiger"): 1, ("Buffalo", "Monkey"): 1, ("Buffalo", "Mongoose"): 2,
    ("Buffalo", "Lion"): 3, ("Buffalo", "Deer"): 1, ("Buffalo", "Sheep"): 3,
    ("Tiger", "Tiger"): 4, ("Tiger", "Monkey"): 1, ("Tiger", "Mongoose"): 2, ("Tiger", "Lion"): 1,
    ("Tiger", "Deer"): 0, ("Tiger", "Sheep"): 1,
    ("Monkey", "Monkey"): 4, ("Monkey", "Mongoose"): 3, ("Monkey", "Lion"): 2, ("Monkey", "Deer"): 2, ("Monkey", "Sheep"): 3,
    ("Mongoose", "Mongoose"): 4, ("Mongoose", "Lion"): 2, ("Mongoose", "Deer"): 1, ("Mongoose", "Sheep"): 0,
    ("Lion", "Lion"): 4, ("Lion", "Deer"): 0, ("Lion", "Sheep"): 2,
    ("Deer", "Deer"): 4, ("Deer", "Sheep"): 2,
    ("Sheep", "Sheep"): 4
}

# Bhakoot score matrix (all 144 combinations)
BHAKOOT_SCORES = {
    ("Aries", "Aries"): 7, ("Aries", "Taurus"): 0, ("Aries", "Gemini"): 7, ("Aries", "Cancer"): 7,
    ("Aries", "Leo"): 0, ("Aries", "Virgo"): 0, ("Aries", "Libra"): 7, ("Aries", "Scorpio"): 0,
    ("Aries", "Sagittarius"): 0, ("Aries", "Capricorn"): 7, ("Aries", "Aquarius"): 7, ("Aries", "Pisces"): 0,
    ("Taurus", "Taurus"): 7, ("Taurus", "Gemini"): 0, ("Taurus", "Cancer"): 7, ("Taurus", "Leo"): 7,
    ("Taurus", "Virgo"): 0, ("Taurus", "Libra"): 0, ("Taurus", "Scorpio"): 7, ("Taurus", "Sagittarius"): 0,
    ("Taurus", "Capricorn"): 0, ("Taurus", "Aquarius"): 7, ("Taurus", "Pisces"): 7,
    ("Gemini", "Gemini"): 7, ("Gemini", "Cancer"): 0, ("Gemini", "Leo"): 7, ("Gemini", "Virgo"): 7,
    ("Gemini", "Libra"): 0, ("Gemini", "Scorpio"): 0, ("Gemini", "Sagittarius"): 7, ("Gemini", "Capricorn"): 0,
    ("Gemini", "Aquarius"): 0, ("Gemini", "Pisces"): 7,
    ("Cancer", "Cancer"): 7, ("Cancer", "Leo"): 0, ("Cancer", "Virgo"): 7, ("Cancer", "Libra"): 7,
    ("Cancer", "Scorpio"): 0, ("Cancer", "Sagittarius"): 0, ("Cancer", "Capricorn"): 7, ("Cancer", "Aquarius"): 0,
    ("Cancer", "Pisces"): 0,
    ("Leo", "Leo"): 7, ("Leo", "Virgo"): 0, ("Leo", "Libra"): 7, ("Leo", "Scorpio"): 7,
    ("Leo", "Sagittarius"): 0, ("Leo", "Capricorn"): 0, ("Leo", "Aquarius"): 7, ("Leo", "Pisces"): 0,
    ("Virgo", "Virgo"): 7, ("Virgo", "Libra"): 0, ("Virgo", "Scorpio"): 7, ("Virgo", "Sagittarius"): 7,
    ("Virgo", "Capricorn"): 0, ("Virgo", "Aquarius"): 0, ("Virgo", "Pisces"): 7,
    ("Libra", "Libra"): 7, ("Libra", "Scorpio"): 0, ("Libra", "Sagittarius"): 7, ("Libra", "Capricorn"): 7,
    ("Libra", "Aquarius"): 0, ("Libra", "Pisces"): 0,
    ("Scorpio", "Scorpio"): 7, ("Scorpio", "Sagittarius"): 0, ("Scorpio", "Capricorn"): 7, ("Scorpio", "Aquarius"): 7,
    ("Scorpio", "Pisces"): 0,
    ("Sagittarius", "Sagittarius"): 7, ("Sagittarius", "Capricorn"): 0, ("Sagittarius", "Aquarius"): 7,
    ("Sagittarius", "Pisces"): 7,
    ("Capricorn", "Capricorn"): 7, ("Capricorn", "Aquarius"): 0, ("Capricorn", "Pisces"): 7,
    ("Aquarius", "Aquarius"): 7, ("Aquarius", "Pisces"): 0,
    ("Pisces", "Pisces"): 7
}

# Tarot cards
TAROT_MAJOR_ARCANA = [
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
    "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
    "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
    "The Devil", "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World"
]

TAROT_MINOR_SUITS = ["Wands", "Cups", "Swords", "Pentacles"]
TAROT_RANKS = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Page", "Knight", "Queen", "King"]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_lat_lon(place: str) -> Tuple[float, float]:
    """Get latitude and longitude for a place using geocoding."""
    if HAS_GEOPY:
        try:
            geolocator = Nominatim(user_agent="whatsapp_astro_bot", timeout=10)
            location = geolocator.geocode(place)
            if location:
                return location.latitude, location.longitude
        except Exception:
            pass

    # Fallback to common Indian cities
    cities = {
        "delhi": (28.6139, 77.2090), "mumbai": (19.0760, 72.8777), "bangalore": (12.9716, 77.5946),
        "chennai": (13.0827, 80.2707), "kolkata": (22.5726, 88.3639), "hyderabad": (17.3850, 78.4867),
        "pune": (18.5204, 73.8567), "ahmedabad": (23.0225, 72.5714), "jaipur": (26.9124, 75.7873),
        "lucknow": (26.8467, 80.9462), "new york": (40.7128, -74.0060), "london": (51.5074, -0.1278),
    }
    place_lower = place.lower().strip()
    for city, coords in cities.items():
        if city in place_lower:
            return coords

    # Default to Delhi
    return (28.6139, 77.2090)


def get_zodiac_sign(degree: float) -> str:
    """Get zodiac sign from degree (0-360)."""
    return ZODIAC_SIGNS[int(degree // 30) % 12]


def get_nakshatra(degree: float) -> Tuple[str, int]:
    """Get Nakshatra and Pada from degree."""
    nakshatra_index = int((degree % 360) // 13.3333)
    nakshatra = NAKSHATRAS[nakshatra_index % 27]
    pada = int(((degree % 13.3333) // 3.3333) + 1)
    return nakshatra, pada


def get_varna(moon_sign: str) -> str:
    """Get Varna based on Moon sign."""
    for varna, signs in VARNA_MAPPING.items():
        if moon_sign in signs:
            return varna
    return "Unknown"


def get_nadi(nakshatra: str) -> str:
    """Get Nadi based on Nakshatra."""
    for nadi, nakshatras in NADI_MAPPING.items():
        if nakshatra in nakshatras:
            return nadi
    return "Unknown"


def get_yoni(nakshatra: str) -> str:
    """Get Yoni (animal) based on Nakshatra."""
    return YONI_MAPPING.get(nakshatra, "Unknown")


def get_gana(nakshatra: str) -> str:
    """Get Gana based on Nakshatra."""
    for gana, nakshatras in GANA_MAPPING.items():
        if nakshatra in nakshatras:
            return gana
    return "Unknown"


def get_vashya(moon_sign: str) -> str:
    """Get Vashya category based on Moon sign."""
    for vashya, signs in VASHYA_MAPPING.items():
        if moon_sign in signs:
            return vashya
    return "Unknown"


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats."""
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_time(time_str: str) -> Tuple[int, int, int]:
    """Parse time string and return (hour, minute, second)."""
    time_str = time_str.strip().upper()

    # Handle AM/PM
    is_pm = "PM" in time_str
    is_am = "AM" in time_str
    time_str = time_str.replace("AM", "").replace("PM", "").strip()

    # Parse time components
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


# =============================================================================
# 1. BIRTH CHART (KUNDLI) CALCULATION
# =============================================================================

async def calculate_kundli(
    birth_date: str,
    birth_time: str,
    birth_place: str,
    name: Optional[str] = None
) -> ToolResult:
    """
    Calculate complete Vedic birth chart (Kundli).

    Uses Swiss Ephemeris for accurate planetary positions.
    """
    try:
        # Parse date
        dt = parse_date(birth_date)
        if not dt:
            return ToolResult(success=False, data=None, error="Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY", tool_name="kundli")

        # Parse time
        hour, minute, second = parse_time(birth_time)
        dt = dt.replace(hour=hour, minute=minute, second=second)

        # Get location
        latitude, longitude = get_lat_lon(birth_place)

        if HAS_SWISSEPH:
            # Use Swiss Ephemeris for accurate calculations
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            # Convert to Julian day
            julian_day = swe.julday(dt.year, dt.month, dt.day, hour + minute/60.0 + second/3600.0)

            # Calculate houses
            cusps, ascmc = swe.houses_ex(julian_day, latitude, longitude, b'P', swe.FLG_SIDEREAL)
            ascendant_position = ascmc[0]

            # Calculate planetary positions
            planets_swe = {
                "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
                "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
                "Rahu": swe.MEAN_NODE
            }

            planetary_positions = {}
            for planet_name, planet_id in planets_swe.items():
                position = swe.calc_ut(julian_day, planet_id, swe.FLG_SIDEREAL)[0][0] % 360
                nakshatra, pada = get_nakshatra(position)
                planetary_positions[planet_name] = {
                    "degree": round(position, 2),
                    "sign": get_zodiac_sign(position),
                    "nakshatra": nakshatra,
                    "pada": pada
                }

            # Calculate Ketu (180° from Rahu)
            rahu_pos = planetary_positions["Rahu"]["degree"]
            ketu_pos = (rahu_pos + 180) % 360
            nakshatra, pada = get_nakshatra(ketu_pos)
            planetary_positions["Ketu"] = {
                "degree": round(ketu_pos, 2),
                "sign": get_zodiac_sign(ketu_pos),
                "nakshatra": nakshatra,
                "pada": pada
            }

            # Get Moon details for additional calculations
            moon_degree = planetary_positions["Moon"]["degree"]
            moon_sign = planetary_positions["Moon"]["sign"]
            moon_nakshatra = planetary_positions["Moon"]["nakshatra"]

            # Calculate houses
            houses = {}
            house_names = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"]
            for i, house_name in enumerate(house_names):
                houses[house_name] = {
                    "degree": round(cusps[i], 2),
                    "sign": get_zodiac_sign(cusps[i])
                }
        else:
            # Simplified calculation without Swiss Ephemeris
            # Use approximate positions based on date
            day_of_year = dt.timetuple().tm_yday

            # Approximate Sun position
            sun_degree = (day_of_year * 360 / 365.25) % 360

            # Approximate Moon position (moves ~13° per day)
            moon_degree = ((day_of_year * 13.2) + (hour / 24 * 13.2)) % 360

            planetary_positions = {
                "Sun": {"degree": round(sun_degree, 2), "sign": get_zodiac_sign(sun_degree), "nakshatra": get_nakshatra(sun_degree)[0], "pada": get_nakshatra(sun_degree)[1]},
                "Moon": {"degree": round(moon_degree, 2), "sign": get_zodiac_sign(moon_degree), "nakshatra": get_nakshatra(moon_degree)[0], "pada": get_nakshatra(moon_degree)[1]},
            }

            moon_sign = planetary_positions["Moon"]["sign"]
            moon_nakshatra = planetary_positions["Moon"]["nakshatra"]
            ascendant_position = (sun_degree + (hour * 15)) % 360

            houses = {f"{i+1}th" if i > 0 else "1st": {"degree": round((ascendant_position + i*30) % 360, 2), "sign": get_zodiac_sign((ascendant_position + i*30) % 360)} for i in range(12)}

        # Calculate additional Vedic attributes
        ascendant_nakshatra, ascendant_pada = get_nakshatra(ascendant_position)
        varna = get_varna(moon_sign)
        nadi = get_nadi(moon_nakshatra)
        yoni = get_yoni(moon_nakshatra)
        gana = get_gana(moon_nakshatra)
        vashya = get_vashya(moon_sign)

        result_data = {
            "name": name,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_place": birth_place,
            "location": {"latitude": latitude, "longitude": longitude},
            "ascendant": {
                "sign": get_zodiac_sign(ascendant_position),
                "degree": round(ascendant_position, 2),
                "nakshatra": ascendant_nakshatra,
                "pada": ascendant_pada
            },
            "sun_sign": planetary_positions.get("Sun", {}).get("sign", "Unknown"),
            "moon_sign": moon_sign,
            "moon_nakshatra": moon_nakshatra,
            "varna": varna,
            "nadi": nadi,
            "yoni": yoni,
            "gana": gana,
            "vashya": vashya,
            "planetary_positions": planetary_positions,
            "houses": houses
        }

        return ToolResult(success=True, data=result_data, error=None, tool_name="kundli")

    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e), tool_name="kundli")


# =============================================================================
# 2. KUNDLI MATCHING (ASHTAKOOT MILAN)
# =============================================================================

async def calculate_kundli_milan(
    person1_name: str,
    person1_dob: str,
    person1_time: str,
    person1_place: str,
    person2_name: str,
    person2_dob: str,
    person2_time: str,
    person2_place: str
) -> ToolResult:
    """
    Calculate Ashtakoot Milan (36-point compatibility score).
    """
    try:
        # Calculate both Kundlis
        kundli1_result = await calculate_kundli(person1_dob, person1_time or "12:00:00", person1_place, person1_name)
        kundli2_result = await calculate_kundli(person2_dob, person2_time or "12:00:00", person2_place, person2_name)

        if not kundli1_result["success"] or not kundli2_result["success"]:
            return ToolResult(success=False, data=None, error="Failed to calculate one or both Kundlis", tool_name="kundli_milan")

        k1 = kundli1_result["data"]
        k2 = kundli2_result["data"]

        # Extract required data
        varna1, varna2 = k1["varna"], k2["varna"]
        nadi1, nadi2 = k1["nadi"], k2["nadi"]
        nakshatra1, nakshatra2 = k1["moon_nakshatra"], k2["moon_nakshatra"]
        rashi1, rashi2 = k1["moon_sign"], k2["moon_sign"]

        # Calculate 8 Kootas

        # 1. Varna Koota (1 point)
        varna_score = 1.0 if varna1 == varna2 else (0.0 if (varna1 == "Brahmin" and varna2 == "Shudra") else 0.5)

        # 2. Vashya Koota (2 points)
        vashya1, vashya2 = get_vashya(rashi1), get_vashya(rashi2)
        vashya_score = VASHYA_SCORES.get((vashya1, vashya2), VASHYA_SCORES.get((vashya2, vashya1), 1))

        # 3. Tara Koota (3 points)
        try:
            idx1 = NAKSHATRAS.index(nakshatra1)
            idx2 = NAKSHATRAS.index(nakshatra2)
            diff = abs(idx1 - idx2) % 9
            tara_score = 0.0 if diff in [3, 5, 7] else (1.5 if diff in [1, 6, 8] else 3.0)
        except ValueError:
            tara_score = 1.5

        # 4. Yoni Koota (4 points)
        yoni1, yoni2 = get_yoni(nakshatra1), get_yoni(nakshatra2)
        yoni_score = YONI_SCORES.get((yoni1, yoni2), YONI_SCORES.get((yoni2, yoni1), 2))

        # 5. Graha Maitri Koota (5 points)
        lord1, lord2 = RASHI_LORD.get(rashi1, "Sun"), RASHI_LORD.get(rashi2, "Sun")
        maitri_score = MAITRI_SCORES.get((lord1, lord2), MAITRI_SCORES.get((lord2, lord1), 2.5))

        # 6. Gana Koota (6 points)
        gana1, gana2 = get_gana(nakshatra1), get_gana(nakshatra2)
        gana_score = GANA_SCORES.get((gana1, gana2), 3)

        # 7. Bhakoot Koota (7 points)
        bhakoot_score = BHAKOOT_SCORES.get((rashi1, rashi2), BHAKOOT_SCORES.get((rashi2, rashi1), 0))

        # 8. Nadi Koota (8 points)
        nadi_score = 0.0 if nadi1 == nadi2 else 8.0

        # Total score
        total_score = round(varna_score + vashya_score + tara_score + yoni_score + maitri_score + gana_score + bhakoot_score + nadi_score, 2)

        # Compatibility verdict
        if total_score >= 25:
            verdict = "Excellent Match"
            recommendation = "Highly recommended for marriage"
        elif total_score >= 18:
            verdict = "Good Match"
            recommendation = "Suitable for marriage with some adjustments"
        elif total_score >= 12:
            verdict = "Average Match"
            recommendation = "Marriage possible with remedies"
        else:
            verdict = "Below Average"
            recommendation = "Consult an astrologer for detailed analysis"

        result_data = {
            "person1": {"name": person1_name, "dob": person1_dob, "moon_sign": rashi1, "nakshatra": nakshatra1},
            "person2": {"name": person2_name, "dob": person2_dob, "moon_sign": rashi2, "nakshatra": nakshatra2},
            "scores": {
                "varna": {"score": varna_score, "max": 1, "description": "Spiritual compatibility"},
                "vashya": {"score": vashya_score, "max": 2, "description": "Mutual attraction & control"},
                "tara": {"score": tara_score, "max": 3, "description": "Birth star compatibility"},
                "yoni": {"score": yoni_score, "max": 4, "description": "Physical compatibility"},
                "graha_maitri": {"score": maitri_score, "max": 5, "description": "Mental compatibility"},
                "gana": {"score": gana_score, "max": 6, "description": "Temperament matching"},
                "bhakoot": {"score": bhakoot_score, "max": 7, "description": "Love & family life"},
                "nadi": {"score": nadi_score, "max": 8, "description": "Health & genetic compatibility"}
            },
            "total_score": total_score,
            "max_score": 36,
            "percentage": round((total_score / 36) * 100, 1),
            "verdict": verdict,
            "recommendation": recommendation
        }

        return ToolResult(success=True, data=result_data, error=None, tool_name="kundli_milan")

    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e), tool_name="kundli_milan")


# =============================================================================
# 3. PANCHANG (DAILY VEDIC CALENDAR)
# =============================================================================

async def calculate_panchang(
    date: str,
    place: str = "Delhi"
) -> ToolResult:
    """
    Calculate Panchang (5-element Vedic calendar) for a given date.
    """
    try:
        dt = parse_date(date)
        if not dt:
            dt = datetime.now()

        latitude, longitude = get_lat_lon(place)

        if HAS_SWISSEPH:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            julian_day = swe.julday(dt.year, dt.month, dt.day, 12.0)  # Noon

            sun_longitude = swe.calc_ut(julian_day, swe.SUN, swe.FLG_SIDEREAL)[0][0] % 360
            moon_longitude = swe.calc_ut(julian_day, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360
        else:
            # Approximate calculations
            day_of_year = dt.timetuple().tm_yday
            sun_longitude = (day_of_year * 360 / 365.25) % 360
            moon_longitude = ((day_of_year * 13.2) + 180) % 360

        # Calculate Tithi
        angle_diff = (moon_longitude - sun_longitude) % 360
        tithi_number = int(angle_diff / 12) + 1
        if tithi_number > 30:
            tithi_number = 30
        tithi_name = TITHI_NAMES[tithi_number - 1]

        # Calculate Nakshatra
        nakshatra_name, pada = get_nakshatra(moon_longitude)

        # Calculate Yoga
        total_longitude = (sun_longitude + moon_longitude) % 360
        yoga_index = int(total_longitude // 13.3333) % 27
        yoga_name = YOGA_NAMES[yoga_index]

        # Calculate Karan
        karan = KARANS[(tithi_number - 1) % len(KARANS)]

        # Calculate Paksha
        paksha = "Shukla Paksha" if angle_diff < 180 else "Krishna Paksha"

        # Moon sign
        moon_sign = get_zodiac_sign(moon_longitude)

        result_data = {
            "date": dt.strftime("%Y-%m-%d"),
            "day": dt.strftime("%A"),
            "place": place,
            "tithi": {
                "name": tithi_name,
                "number": tithi_number,
                "paksha": paksha
            },
            "nakshatra": {
                "name": nakshatra_name,
                "pada": pada
            },
            "yoga": yoga_name,
            "karan": karan,
            "moon_sign": moon_sign,
            "sun_longitude": round(sun_longitude, 2),
            "moon_longitude": round(moon_longitude, 2)
        }

        return ToolResult(success=True, data=result_data, error=None, tool_name="panchang")

    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e), tool_name="panchang")


# =============================================================================
# 4. HOROSCOPE (NAKSHATRA-BASED)
# =============================================================================

async def get_horoscope(
    sign: Optional[str] = None,
    nakshatra: Optional[str] = None,
    period: str = "today",
    language: str = "English"
) -> ToolResult:
    """
    Get horoscope prediction based on zodiac sign or nakshatra.
    Responds in the specified language.
    """
    try:
        sign = sign.strip() if sign else None

        # Validate and normalize sign
        if sign:
            original_sign = sign
            sign_normalized = None

            # Check all Indian language scripts (Hindi, Kannada, Tamil, Telugu, Bengali, Malayalam, Punjabi, Odia)
            if sign in ALL_ZODIAC_SCRIPTS:
                sign_normalized = ALL_ZODIAC_SCRIPTS[sign]

            # Check romanized Hindi names (e.g., Dhanu, Mesh)
            if not sign_normalized:
                for i, hindi_name in enumerate(ZODIAC_SIGNS_HINDI):
                    if sign.lower() == hindi_name.lower():
                        sign_normalized = ZODIAC_SIGNS[i]
                        break

            # Check English names (e.g., Sagittarius, Aries)
            if not sign_normalized:
                sign_cap = sign.capitalize()
                if sign_cap in ZODIAC_SIGNS:
                    sign_normalized = sign_cap

            if sign_normalized:
                sign = sign_normalized
            else:
                return ToolResult(success=False, data=None, error=f"Invalid zodiac sign: {original_sign}", tool_name="horoscope")

        # Get nakshatra prediction
        if nakshatra and nakshatra in NAKSHATRA_DATA:
            prediction = NAKSHATRA_DATA[nakshatra]
        elif sign:
            # Use AI to generate horoscope for the sign
            settings = get_settings()
            llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.8, api_key=settings.OPENAI_API_KEY)

            # Language instruction for non-English responses
            language_instruction = ""
            if language != "English":
                language_instruction = f"""
IMPORTANT: You MUST respond entirely in {language}. Use the native script of {language} (e.g., Devanagari for Hindi, Bengali script for Bengali, Tamil script for Tamil, etc.).
Do NOT use English except for the zodiac sign name if needed."""

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert Vedic astrologer. Generate a {period} horoscope for {sign}.

Include:
- Overall energy and theme for the {period}
- Love & Relationships
- Career & Finance
- Health tips
- Lucky number (1-9), lucky color, and lucky time
- A positive affirmation

Keep it concise but insightful (150-200 words). Use warm, encouraging tone.
{language_instruction}"""),
                ("human", "Generate {period} horoscope for {sign}")
            ])

            chain = prompt | llm
            result = await chain.ainvoke({"sign": sign, "period": period, "language_instruction": language_instruction})

            return ToolResult(
                success=True,
                data={
                    "sign": sign,
                    "period": period,
                    "horoscope": result.content,
                    "generated": True
                },
                error=None,
                tool_name="horoscope"
            )
        else:
            return ToolResult(success=False, data=None, error="Please provide a zodiac sign", tool_name="horoscope")

        return ToolResult(
            success=True,
            data={
                "nakshatra": nakshatra,
                "description": prediction.get("description", ""),
                "lucky_number": prediction.get("lucky_number", 1),
                "lucky_color": prediction.get("lucky_color", "White"),
                "advice": prediction.get("advice", ""),
                "period": period
            },
            error=None,
            tool_name="horoscope"
        )

    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e), tool_name="horoscope")


# =============================================================================
# 5. NUMEROLOGY
# =============================================================================

async def calculate_numerology(
    name: str,
    birth_date: Optional[str] = None
) -> ToolResult:
    """
    Calculate numerology numbers from name and birth date.
    """
    try:
        # Pythagorean numerology system
        pythagorean = {
            'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
            'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
            's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8
        }

        # Calculate name number
        name_sum = sum(pythagorean.get(c.lower(), 0) for c in name if c.isalpha())
        while name_sum > 9 and name_sum not in [11, 22, 33]:
            name_sum = sum(int(d) for d in str(name_sum))
        name_number = name_sum

        # Calculate life path number from birth date
        life_path_number = None
        if birth_date:
            dt = parse_date(birth_date)
            if dt:
                digits = f"{dt.year}{dt.month:02d}{dt.day:02d}"
                total = sum(int(d) for d in digits)
                while total > 9 and total not in [11, 22, 33]:
                    total = sum(int(d) for d in str(total))
                life_path_number = total

        # Number meanings
        number_meanings = {
            1: {"trait": "Leadership", "description": "Independent, ambitious, pioneering spirit"},
            2: {"trait": "Cooperation", "description": "Diplomatic, sensitive, supportive"},
            3: {"trait": "Expression", "description": "Creative, optimistic, inspiring"},
            4: {"trait": "Stability", "description": "Practical, hardworking, disciplined"},
            5: {"trait": "Freedom", "description": "Adventurous, versatile, dynamic"},
            6: {"trait": "Responsibility", "description": "Nurturing, caring, family-oriented"},
            7: {"trait": "Analysis", "description": "Thoughtful, spiritual, introspective"},
            8: {"trait": "Power", "description": "Ambitious, authoritative, material success"},
            9: {"trait": "Humanitarianism", "description": "Compassionate, generous, idealistic"},
            11: {"trait": "Intuition (Master)", "description": "Visionary, inspirational, enlightened"},
            22: {"trait": "Master Builder", "description": "Practical visionary, powerful manifestor"},
            33: {"trait": "Master Teacher", "description": "Spiritual leader, healer, uplifter"}
        }

        result_data = {
            "name": name,
            "name_number": name_number,
            "name_meaning": number_meanings.get(name_number, {}),
            "birth_date": birth_date,
            "life_path_number": life_path_number,
            "life_path_meaning": number_meanings.get(life_path_number, {}) if life_path_number else None,
            "lucky_numbers": [name_number, (name_number + 3) % 9 + 1, (name_number + 6) % 9 + 1]
        }

        return ToolResult(success=True, data=result_data, error=None, tool_name="numerology")

    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e), tool_name="numerology")


# =============================================================================
# 6. TAROT READING
# =============================================================================

async def draw_tarot(
    question: Optional[str] = None,
    spread_type: str = "three_card"
) -> ToolResult:
    """
    Generate a tarot reading with randomly drawn cards.
    """
    try:
        # Build full deck
        deck = TAROT_MAJOR_ARCANA.copy()
        for suit in TAROT_MINOR_SUITS:
            for rank in TAROT_RANKS:
                deck.append(f"{rank} of {suit}")

        # Determine spread
        if spread_type == "single":
            num_cards = 1
            positions = ["The Card"]
        elif spread_type == "celtic_cross":
            num_cards = 10
            positions = ["Present", "Challenge", "Foundation", "Recent Past", "Crown",
                        "Near Future", "Your Attitude", "Environment", "Hopes/Fears", "Outcome"]
        else:  # three_card
            num_cards = 3
            positions = ["Past", "Present", "Future"]

        # Draw cards
        drawn = random.sample(deck, num_cards)
        reversed_flags = [random.choice([True, False]) for _ in range(num_cards)]

        cards = []
        for i in range(num_cards):
            cards.append({
                "position": positions[i],
                "card": drawn[i],
                "reversed": reversed_flags[i],
                "orientation": "Reversed" if reversed_flags[i] else "Upright"
            })

        # Generate interpretation using AI
        settings = get_settings()
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.8, api_key=settings.OPENAI_API_KEY)

        cards_text = "\n".join([f"- {c['position']}: {c['card']} ({c['orientation']})" for c in cards])
        question_text = f"Question: {question}" if question else "General reading"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intuitive tarot reader. Interpret this reading:

{cards_text}

{question_text}

Provide:
1. Brief meaning for each card in its position
2. How the cards connect to tell a story
3. Key message and guidance
4. An empowering closing thought

Be insightful and compassionate. Keep response under 300 words."""),
            ("human", "Interpret this tarot spread")
        ])

        chain = prompt | llm
        interpretation = await chain.ainvoke({"cards_text": cards_text, "question_text": question_text})

        result_data = {
            "spread_type": spread_type,
            "question": question,
            "cards": cards,
            "interpretation": interpretation.content
        }

        return ToolResult(success=True, data=result_data, error=None, tool_name="tarot")

    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e), tool_name="tarot")


# =============================================================================
# 7. ASK ASTROLOGER (AI Q&A)
# =============================================================================

async def ask_astrologer(question: str, user_sign: Optional[str] = None) -> ToolResult:
    """
    AI-powered astrology Q&A.
    """
    try:
        if not question or len(question.strip()) < 5:
            return ToolResult(success=False, data=None, error="Please ask a specific question", tool_name="ask_astrologer")

        settings = get_settings()
        llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.7, api_key=settings.OPENAI_API_KEY)

        context = f"\nUser's zodiac sign: {user_sign}" if user_sign else ""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Vedic astrologer with deep knowledge of:
- Zodiac signs and their traits
- Planetary influences (grahas)
- Nakshatras (lunar mansions)
- Kundli interpretation
- Remedies (gemstones, mantras, rituals)
- Muhurta (auspicious timing)
- Compatibility analysis
{context}

Answer the question with accuracy and wisdom. Be helpful and encouraging."""),
            ("human", "{question}")
        ])

        chain = prompt | llm
        answer = await chain.ainvoke({"question": question, "context": context})

        return ToolResult(
            success=True,
            data={"question": question, "answer": answer.content, "user_sign": user_sign},
            error=None,
            tool_name="ask_astrologer"
        )

    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e), tool_name="ask_astrologer")
