"""
Knowledge Layer - Curated Jyotish Text Snippets

This module provides curated text snippets from classical Jyotish sources.
Used for RAG-style retrieval to ground LLM interpretations.

Principles:
1. Only trusted, vetted content
2. Organized by topic for easy retrieval
3. Used to support (not generate) interpretations
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from bot.astro.schemas.chart import Planet, ZodiacSign, Nakshatra


class TextSnippet(BaseModel):
    """A curated text snippet from Jyotish sources."""

    id: str
    topic: str
    subtopic: Optional[str] = None
    content: str
    source: str = Field(default="Classical Texts")
    is_verified: bool = Field(default=True)


# =============================================================================
# NAKSHATRA DESCRIPTIONS (Curated from classical texts)
# =============================================================================

NAKSHATRA_DATA: Dict[Nakshatra, Dict] = {
    Nakshatra.ASHWINI: {
        "description": "Swift and dynamic. Associated with healing, beginnings, and quick action.",
        "deity": "Ashwini Kumaras (Divine Physicians)",
        "symbol": "Horse's head",
        "traits": ["Quick thinker", "Healing ability", "Adventurous", "Independent"],
        "career_affinity": ["Healthcare", "Racing", "Transport", "Alternative medicine"],
        "lucky_color": "Red",
        "lucky_number": 3,
    },
    Nakshatra.BHARANI: {
        "description": "Represents transformation and responsibility. Strong determination.",
        "deity": "Yama (God of Death/Dharma)",
        "symbol": "Yoni (Female reproductive organ)",
        "traits": ["Determined", "Responsible", "Transformative", "Creative"],
        "career_affinity": ["Law", "Publishing", "Entertainment", "Finance"],
        "lucky_color": "Orange",
        "lucky_number": 9,
    },
    Nakshatra.KRITTIKA: {
        "description": "Sharp and fiery. Cuts through obstacles with precision.",
        "deity": "Agni (Fire God)",
        "symbol": "Razor or flame",
        "traits": ["Sharp intellect", "Determined", "Critical", "Purifying"],
        "career_affinity": ["Military", "Surgery", "Fire services", "Criticism"],
        "lucky_color": "Red",
        "lucky_number": 1,
    },
    Nakshatra.ROHINI: {
        "description": "Creative and nurturing. Associated with growth and beauty.",
        "deity": "Brahma (Creator)",
        "symbol": "Ox cart or chariot",
        "traits": ["Creative", "Beautiful", "Materialistic", "Nurturing"],
        "career_affinity": ["Arts", "Agriculture", "Fashion", "Hospitality"],
        "lucky_color": "Pink",
        "lucky_number": 6,
    },
    Nakshatra.MRIGASHIRA: {
        "description": "Curious and searching. Always seeking knowledge and experiences.",
        "deity": "Soma (Moon God)",
        "symbol": "Deer's head",
        "traits": ["Curious", "Restless", "Gentle", "Seeking"],
        "career_affinity": ["Research", "Travel", "Teaching", "Writing"],
        "lucky_color": "Green",
        "lucky_number": 5,
    },
    Nakshatra.ARDRA: {
        "description": "Intense and transformative. Associated with storms and renewal.",
        "deity": "Rudra (Storm God)",
        "symbol": "Teardrop or diamond",
        "traits": ["Intense", "Emotional", "Transformative", "Intellectual"],
        "career_affinity": ["Psychology", "Technology", "Research", "Humanitarian work"],
        "lucky_color": "Blue",
        "lucky_number": 7,
    },
    Nakshatra.PUNARVASU: {
        "description": "Renewal and return to light. Optimistic and philosophical.",
        "deity": "Aditi (Mother of Gods)",
        "symbol": "Bow and quiver",
        "traits": ["Optimistic", "Philosophical", "Nurturing", "Recovering"],
        "career_affinity": ["Teaching", "Counseling", "Archery", "Philosophy"],
        "lucky_color": "White",
        "lucky_number": 4,
    },
    Nakshatra.PUSHYA: {
        "description": "Most auspicious nakshatra. Nourishing and supportive.",
        "deity": "Brihaspati (Jupiter)",
        "symbol": "Lotus, circle, arrow",
        "traits": ["Supportive", "Reliable", "Spiritual", "Generous"],
        "career_affinity": ["Teaching", "Dairy", "Counseling", "Spiritual work"],
        "lucky_color": "Yellow",
        "lucky_number": 8,
    },
    Nakshatra.ASHLESHA: {
        "description": "Mystical and cunning. Deep wisdom and transformative power.",
        "deity": "Nagas (Serpent deities)",
        "symbol": "Coiled serpent",
        "traits": ["Mystical", "Intuitive", "Cunning", "Hypnotic"],
        "career_affinity": ["Occult", "Psychology", "Medicine", "Politics"],
        "lucky_color": "Purple",
        "lucky_number": 2,
    },
    Nakshatra.MAGHA: {
        "description": "Royal and ancestral. Connection to heritage and authority.",
        "deity": "Pitris (Ancestors)",
        "symbol": "Throne room",
        "traits": ["Regal", "Authoritative", "Traditional", "Proud"],
        "career_affinity": ["Government", "Management", "History", "Ceremonies"],
        "lucky_color": "Gold",
        "lucky_number": 10,
    },
    Nakshatra.PURVA_PHALGUNI: {
        "description": "Creative enjoyment and luxury. Love of pleasure.",
        "deity": "Bhaga (God of Fortune)",
        "symbol": "Front legs of bed/couch",
        "traits": ["Creative", "Romantic", "Artistic", "Pleasure-seeking"],
        "career_affinity": ["Entertainment", "Arts", "Romance", "Hospitality"],
        "lucky_color": "Peach",
        "lucky_number": 6,
    },
    Nakshatra.UTTARA_PHALGUNI: {
        "description": "Helpful and dutiful. Focused on service and contracts.",
        "deity": "Aryaman (God of Contracts)",
        "symbol": "Back legs of bed",
        "traits": ["Helpful", "Organized", "Contractual", "Service-oriented"],
        "career_affinity": ["HR", "Contract work", "Charity", "Administration"],
        "lucky_color": "Maroon",
        "lucky_number": 9,
    },
    Nakshatra.HASTA: {
        "description": "Skillful with hands. Craftsmanship and dexterity.",
        "deity": "Savitar (Sun God)",
        "symbol": "Open hand",
        "traits": ["Skillful", "Clever", "Healing hands", "Adaptable"],
        "career_affinity": ["Crafts", "Healing", "Writing", "Magic/Illusion"],
        "lucky_color": "Silver",
        "lucky_number": 1,
    },
    Nakshatra.CHITRA: {
        "description": "Beautiful and creative. The celestial architect.",
        "deity": "Tvashtar (Celestial Architect)",
        "symbol": "Bright jewel or pearl",
        "traits": ["Creative", "Beautiful", "Architectural", "Detail-oriented"],
        "career_affinity": ["Architecture", "Fashion", "Jewelry", "Interior design"],
        "lucky_color": "Red",
        "lucky_number": 7,
    },
    Nakshatra.SWATI: {
        "description": "Independent and adaptable. Like a blade of grass in wind.",
        "deity": "Vayu (Wind God)",
        "symbol": "Young plant swaying",
        "traits": ["Independent", "Flexible", "Business-minded", "Diplomatic"],
        "career_affinity": ["Business", "Trade", "Diplomacy", "Travel"],
        "lucky_color": "Blue",
        "lucky_number": 5,
    },
    Nakshatra.VISHAKHA: {
        "description": "Single-pointed focus. Goal-oriented and determined.",
        "deity": "Indra-Agni",
        "symbol": "Triumphal arch, potter's wheel",
        "traits": ["Determined", "Goal-oriented", "Competitive", "Transformative"],
        "career_affinity": ["Leadership", "Politics", "Sports", "Research"],
        "lucky_color": "Green",
        "lucky_number": 8,
    },
    Nakshatra.ANURADHA: {
        "description": "Devotion and friendship. Organizational ability.",
        "deity": "Mitra (God of Friendship)",
        "symbol": "Lotus",
        "traits": ["Devoted", "Friendly", "Organized", "Spiritual"],
        "career_affinity": ["Organizations", "Friendship networks", "Music", "Astrology"],
        "lucky_color": "Black",
        "lucky_number": 4,
    },
    Nakshatra.JYESHTHA: {
        "description": "Eldest and most experienced. Protective authority.",
        "deity": "Indra (King of Gods)",
        "symbol": "Circular talisman, earring",
        "traits": ["Protective", "Authoritative", "Experienced", "Possessive"],
        "career_affinity": ["Security", "Military", "Leadership", "Elder care"],
        "lucky_color": "Purple",
        "lucky_number": 3,
    },
    Nakshatra.MULA: {
        "description": "Getting to the root. Destruction leading to transformation.",
        "deity": "Nirrti (Goddess of Destruction)",
        "symbol": "Bunch of roots, lion's tail",
        "traits": ["Investigative", "Transformative", "Philosophical", "Destructive/Creative"],
        "career_affinity": ["Research", "Medicine (root cause)", "Philosophy", "Healing"],
        "lucky_color": "Brown",
        "lucky_number": 6,
    },
    Nakshatra.PURVA_ASHADHA: {
        "description": "Invincibility and early victory. Confident and purifying.",
        "deity": "Apas (Water deities)",
        "symbol": "Fan, winnowing basket",
        "traits": ["Confident", "Victorious", "Purifying", "Philosophical"],
        "career_affinity": ["Philosophy", "Water-related", "Debate", "Law"],
        "lucky_color": "Pink",
        "lucky_number": 2,
    },
    Nakshatra.UTTARA_ASHADHA: {
        "description": "Final victory. Universal achievement and leadership.",
        "deity": "Vishwadevas (Universal Gods)",
        "symbol": "Elephant tusk, planks of bed",
        "traits": ["Victorious", "Universal", "Leadership", "Ethical"],
        "career_affinity": ["Government", "Leadership", "Ethics", "Universal causes"],
        "lucky_color": "Orange",
        "lucky_number": 9,
    },
    Nakshatra.SHRAVANA: {
        "description": "Listening and learning. Connection and knowledge.",
        "deity": "Vishnu (Preserver)",
        "symbol": "Three footprints, ear",
        "traits": ["Learned", "Connected", "Listening", "Traditional"],
        "career_affinity": ["Teaching", "Media", "Counseling", "Knowledge work"],
        "lucky_color": "White",
        "lucky_number": 7,
    },
    Nakshatra.DHANISHTA: {
        "description": "Wealth and music. Adaptable and resourceful.",
        "deity": "Vasus (Eight elemental gods)",
        "symbol": "Drum or flute",
        "traits": ["Wealthy", "Musical", "Adaptable", "Resourceful"],
        "career_affinity": ["Music", "Finance", "Real estate", "Group activities"],
        "lucky_color": "Red",
        "lucky_number": 5,
    },
    Nakshatra.SHATABHISHA: {
        "description": "Hundred healers. Mysterious and healing.",
        "deity": "Varuna (God of Cosmic Waters)",
        "symbol": "Empty circle, 100 flowers",
        "traits": ["Healing", "Mysterious", "Solitary", "Truthful"],
        "career_affinity": ["Healing", "Technology", "Research", "Astrology"],
        "lucky_color": "Blue",
        "lucky_number": 10,
    },
    Nakshatra.PURVA_BHADRAPADA: {
        "description": "The burning pair. Intense transformation.",
        "deity": "Aja Ekapada (One-footed goat)",
        "symbol": "Front of funeral cot, sword",
        "traits": ["Intense", "Transformative", "Spiritual", "Ascetic"],
        "career_affinity": ["Spirituality", "Occult", "Research", "Social reform"],
        "lucky_color": "Silver",
        "lucky_number": 8,
    },
    Nakshatra.UTTARA_BHADRAPADA: {
        "description": "The warrior star. Deep wisdom and stability.",
        "deity": "Ahirbudhnya (Serpent of the depths)",
        "symbol": "Back of funeral cot, twins",
        "traits": ["Wise", "Stable", "Charitable", "Controlled"],
        "career_affinity": ["Charity", "Counseling", "Spirituality", "Research"],
        "lucky_color": "Green",
        "lucky_number": 4,
    },
    Nakshatra.REVATI: {
        "description": "The wealthy. Safe journeys and completion.",
        "deity": "Pushan (Nourisher, protector of travelers)",
        "symbol": "Fish or drum",
        "traits": ["Nurturing", "Protective", "Wealthy", "Completion"],
        "career_affinity": ["Travel", "Animal care", "Foster care", "Roads/Paths"],
        "lucky_color": "White",
        "lucky_number": 3,
    },
}

# =============================================================================
# PLANET SIGNIFICATIONS
# =============================================================================

PLANET_DATA: Dict[Planet, Dict] = {
    Planet.SUN: {
        "name": "Surya",
        "nature": "Malefic (Krura)",
        "significations": ["Soul", "Father", "Government", "Authority", "Health", "Ego", "Vitality"],
        "body_parts": ["Heart", "Spine", "Eyes (right)"],
        "gems": ["Ruby"],
        "metal": "Gold",
        "day": "Sunday",
        "direction": "East",
        "element": "Fire",
    },
    Planet.MOON: {
        "name": "Chandra",
        "nature": "Benefic (Saumya)",
        "significations": ["Mind", "Mother", "Emotions", "Public", "Liquids", "Travel", "Fertility"],
        "body_parts": ["Mind", "Blood", "Eyes (left)", "Lungs"],
        "gems": ["Pearl", "Moonstone"],
        "metal": "Silver",
        "day": "Monday",
        "direction": "Northwest",
        "element": "Water",
    },
    Planet.MARS: {
        "name": "Mangal/Kuja",
        "nature": "Malefic (Krura)",
        "significations": ["Energy", "Courage", "Siblings", "Property", "Disputes", "Surgery", "Military"],
        "body_parts": ["Muscles", "Blood", "Head", "Bone marrow"],
        "gems": ["Red Coral"],
        "metal": "Copper",
        "day": "Tuesday",
        "direction": "South",
        "element": "Fire",
    },
    Planet.MERCURY: {
        "name": "Budha",
        "nature": "Neutral (takes on nature of conjunct planets)",
        "significations": ["Intelligence", "Communication", "Business", "Writing", "Mathematics", "Youth"],
        "body_parts": ["Skin", "Nervous system", "Speech"],
        "gems": ["Emerald"],
        "metal": "Bronze/Alloys",
        "day": "Wednesday",
        "direction": "North",
        "element": "Earth",
    },
    Planet.JUPITER: {
        "name": "Guru/Brihaspati",
        "nature": "Benefic (Saumya)",
        "significations": ["Wisdom", "Teacher", "Children", "Dharma", "Expansion", "Luck", "Higher learning"],
        "body_parts": ["Liver", "Fat tissue", "Ears"],
        "gems": ["Yellow Sapphire", "Topaz"],
        "metal": "Gold",
        "day": "Thursday",
        "direction": "Northeast",
        "element": "Ether/Space",
    },
    Planet.VENUS: {
        "name": "Shukra",
        "nature": "Benefic (Saumya)",
        "significations": ["Love", "Beauty", "Art", "Spouse", "Luxury", "Vehicles", "Comfort"],
        "body_parts": ["Reproductive system", "Face", "Kidneys"],
        "gems": ["Diamond", "White Sapphire"],
        "metal": "Silver",
        "day": "Friday",
        "direction": "Southeast",
        "element": "Water",
    },
    Planet.SATURN: {
        "name": "Shani",
        "nature": "Malefic (Krura)",
        "significations": ["Karma", "Discipline", "Delays", "Service", "Longevity", "Labor", "Death"],
        "body_parts": ["Bones", "Teeth", "Legs", "Chronic diseases"],
        "gems": ["Blue Sapphire"],
        "metal": "Iron",
        "day": "Saturday",
        "direction": "West",
        "element": "Air",
    },
    Planet.RAHU: {
        "name": "Rahu (North Node)",
        "nature": "Malefic (Krura)",
        "significations": ["Illusion", "Foreign", "Technology", "Obsession", "Materialism", "Unconventional"],
        "body_parts": ["Nervous disorders", "Skin"],
        "gems": ["Hessonite (Gomed)"],
        "metal": "Lead",
        "day": "Saturday (some say none)",
        "direction": "Southwest",
        "element": "Air",
    },
    Planet.KETU: {
        "name": "Ketu (South Node)",
        "nature": "Malefic (Krura)",
        "significations": ["Spirituality", "Liberation", "Past karma", "Detachment", "Psychic abilities"],
        "body_parts": ["Spine", "Nervous system"],
        "gems": ["Cat's Eye"],
        "metal": "Lead",
        "day": "Tuesday (some say none)",
        "direction": "Northeast",
        "element": "Fire",
    },
}

# =============================================================================
# HOUSE SIGNIFICATIONS
# =============================================================================

HOUSE_DATA: Dict[int, Dict] = {
    1: {
        "name": "Lagna/Tanu Bhava",
        "significations": ["Self", "Body", "Personality", "Appearance", "Beginning", "Health"],
        "karaka": Planet.SUN,
    },
    2: {
        "name": "Dhana Bhava",
        "significations": ["Wealth", "Family", "Speech", "Food", "Face", "Right eye"],
        "karaka": Planet.JUPITER,
    },
    3: {
        "name": "Sahaja Bhava",
        "significations": ["Siblings", "Courage", "Short journeys", "Communication", "Hands", "Neighbors"],
        "karaka": Planet.MARS,
    },
    4: {
        "name": "Sukha Bhava",
        "significations": ["Mother", "Home", "Happiness", "Property", "Vehicles", "Education"],
        "karaka": Planet.MOON,
    },
    5: {
        "name": "Putra Bhava",
        "significations": ["Children", "Intelligence", "Creativity", "Romance", "Past life merit", "Speculation"],
        "karaka": Planet.JUPITER,
    },
    6: {
        "name": "Ripu/Ari Bhava",
        "significations": ["Enemies", "Disease", "Debt", "Service", "Competition", "Obstacles"],
        "karaka": Planet.MARS,
    },
    7: {
        "name": "Kalatra Bhava",
        "significations": ["Marriage", "Partnership", "Business", "Foreign travel", "Public dealings"],
        "karaka": Planet.VENUS,
    },
    8: {
        "name": "Mrityu/Randhra Bhava",
        "significations": ["Death", "Transformation", "Hidden things", "Inheritance", "Occult", "Research"],
        "karaka": Planet.SATURN,
    },
    9: {
        "name": "Dharma Bhava",
        "significations": ["Father", "Guru", "Religion", "Higher learning", "Fortune", "Long journeys"],
        "karaka": Planet.JUPITER,
    },
    10: {
        "name": "Karma Bhava",
        "significations": ["Career", "Status", "Authority", "Government", "Public image", "Fame"],
        "karaka": Planet.SUN,
    },
    11: {
        "name": "Labha Bhava",
        "significations": ["Gains", "Income", "Friends", "Wishes fulfilled", "Elder siblings", "Networks"],
        "karaka": Planet.JUPITER,
    },
    12: {
        "name": "Vyaya Bhava",
        "significations": ["Loss", "Expenses", "Foreign lands", "Moksha", "Sleep", "Feet", "Isolation"],
        "karaka": Planet.SATURN,
    },
}

# =============================================================================
# YOGA DESCRIPTIONS
# =============================================================================

YOGA_DESCRIPTIONS = {
    "Gaja Kesari Yoga": {
        "description": "Jupiter in kendra from Moon. One of the most auspicious yogas.",
        "effects": "Fame, eloquence, virtuous qualities, leadership ability",
        "source": "Brihat Parashara Hora Shastra",
    },
    "Budhaditya Yoga": {
        "description": "Sun and Mercury conjunction in same sign.",
        "effects": "Intelligence, good communication, analytical ability, fame",
        "source": "Classical texts",
    },
    "Chandra-Mangal Yoga": {
        "description": "Moon and Mars conjunction.",
        "effects": "Wealth through effort, business acumen, courage",
        "source": "Classical texts",
    },
    "Ruchaka Yoga": {
        "description": "Mars in own/exalted sign in kendra. One of five Mahapurusha Yogas.",
        "effects": "Courage, leadership, military success, physical strength",
        "source": "Brihat Parashara Hora Shastra",
    },
    "Bhadra Yoga": {
        "description": "Mercury in own/exalted sign in kendra. Mahapurusha Yoga.",
        "effects": "Intelligence, business success, eloquence, diplomacy",
        "source": "Brihat Parashara Hora Shastra",
    },
    "Hamsa Yoga": {
        "description": "Jupiter in own/exalted sign in kendra. Mahapurusha Yoga.",
        "effects": "Wisdom, righteousness, spiritual inclination, respect",
        "source": "Brihat Parashara Hora Shastra",
    },
    "Malavya Yoga": {
        "description": "Venus in own/exalted sign in kendra. Mahapurusha Yoga.",
        "effects": "Beauty, luxury, artistic talent, romantic success",
        "source": "Brihat Parashara Hora Shastra",
    },
    "Sasha Yoga": {
        "description": "Saturn in own/exalted sign in kendra. Mahapurusha Yoga.",
        "effects": "Authority through discipline, power, leadership of masses",
        "source": "Brihat Parashara Hora Shastra",
    },
}


class KnowledgeLayer:
    """
    Knowledge retrieval service for Jyotish interpretations.

    Provides curated text snippets for grounding LLM interpretations.
    """

    def __init__(self):
        """Initialize knowledge layer."""
        self.nakshatra_data = NAKSHATRA_DATA
        self.planet_data = PLANET_DATA
        self.house_data = HOUSE_DATA
        self.yoga_descriptions = YOGA_DESCRIPTIONS

    def get_nakshatra_info(self, nakshatra: Nakshatra) -> Dict:
        """Get curated information about a nakshatra."""
        return self.nakshatra_data.get(nakshatra, {})

    def get_planet_info(self, planet: Planet) -> Dict:
        """Get curated information about a planet."""
        return self.planet_data.get(planet, {})

    def get_house_info(self, house: int) -> Dict:
        """Get curated information about a house."""
        return self.house_data.get(house, {})

    def get_yoga_description(self, yoga_name: str) -> Dict:
        """Get curated description of a yoga."""
        return self.yoga_descriptions.get(yoga_name, {})

    def get_horoscope_text(self, nakshatra: Nakshatra) -> Dict:
        """Get horoscope-style prediction text for nakshatra."""
        data = self.get_nakshatra_info(nakshatra)
        return {
            "description": data.get("description", ""),
            "lucky_number": data.get("lucky_number", 1),
            "lucky_color": data.get("lucky_color", "White"),
            "traits": data.get("traits", []),
            "career_affinity": data.get("career_affinity", []),
        }

    def get_remedies_for_planet(self, planet: Planet) -> Dict:
        """Get traditional remedies for a planet."""
        data = self.planet_data.get(planet, {})
        return {
            "gem": data.get("gems", ["Unknown"])[0],
            "day": data.get("day", "Unknown"),
            "mantra": f"Om {data.get('name', planet.value)} Namaha",
            "charity": f"Donate on {data.get('day', 'any day')}",
        }

    def build_interpretation_context(
        self,
        planets: List[Planet] = None,
        houses: List[int] = None,
        nakshatras: List[Nakshatra] = None,
        yogas: List[str] = None
    ) -> str:
        """
        Build a context string for LLM interpretation.

        This provides factual grounding for interpretations.
        """
        context_parts = []

        if planets:
            for p in planets:
                info = self.get_planet_info(p)
                if info:
                    context_parts.append(
                        f"{p.value}: {', '.join(info.get('significations', [])[:5])}"
                    )

        if houses:
            for h in houses:
                info = self.get_house_info(h)
                if info:
                    context_parts.append(
                        f"House {h}: {', '.join(info.get('significations', [])[:5])}"
                    )

        if nakshatras:
            for n in nakshatras:
                info = self.get_nakshatra_info(n)
                if info:
                    context_parts.append(
                        f"{n.value}: {info.get('description', '')}"
                    )

        if yogas:
            for y in yogas:
                info = self.get_yoga_description(y)
                if info:
                    context_parts.append(
                        f"{y}: {info.get('effects', '')}"
                    )

        return "\n".join(context_parts)
