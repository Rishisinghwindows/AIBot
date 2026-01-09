"""
Food Discovery Node Handler

Handles food and restaurant related queries.
Provides restaurant search and discovery with links to Zomato/Swiggy for ordering.
"""

import logging
import re
import httpx
from typing import Optional
from bot.state import BotState
from bot.tools.food_tool import (
    search_restaurants,
    get_restaurant_details,
    format_restaurant_response,
    format_restaurant_detail,
    CUISINES,
)
from bot.stores.pending_location_store import get_pending_location_store

logger = logging.getLogger(__name__)

INTENT = "food_order"


def _extract_city(query: str) -> Optional[str]:
    """Extract city name from query in multiple languages."""
    # Map various names/scripts to standard city names
    city_aliases = {
        # English variations
        "bangalore": "Bengaluru",
        "bombay": "Mumbai",
        "madras": "Chennai",
        "calcutta": "Kolkata",
        "trivandrum": "Thiruvananthapuram",
        "cochin": "Kochi",
        "vizag": "Visakhapatnam",
        "gurugram": "Gurgaon",
        # Hindi
        "मुंबई": "Mumbai",
        "दिल्ली": "Delhi",
        "बेंगलुरु": "Bengaluru",
        "बैंगलोर": "Bengaluru",
        "चेन्नई": "Chennai",
        "कोलकाता": "Kolkata",
        "हैदराबाद": "Hyderabad",
        "पुणे": "Pune",
        "अहमदाबाद": "Ahmedabad",
        "जयपुर": "Jaipur",
        "लखनऊ": "Lucknow",
        "नोएडा": "Noida",
        "गुड़गांव": "Gurgaon",
        # Kannada
        "ಬೆಂಗಳೂರು": "Bengaluru",
        "ಮುಂಬೈ": "Mumbai",
        "ದೆಹಲಿ": "Delhi",
        "ಚೆನ್ನೈ": "Chennai",
        "ಹೈದರಾಬಾದ್": "Hyderabad",
        "ಮೈಸೂರು": "Mysore",
        "ಮಂಗಳೂರು": "Mangalore",
        "ಹುಬ್ಬಳ್ಳಿ": "Hubli",
        # Odia
        "ଭୁବନେଶ୍ୱର": "Bhubaneswar",
        "କଟକ": "Cuttack",
        "ମୁମ୍ବାଇ": "Mumbai",
        "ଦିଲ୍ଲୀ": "Delhi",
        "ବେଙ୍ଗାଲୁରୁ": "Bengaluru",
        "ହାଇଦ୍ରାବାଦ": "Hyderabad",
        # Tamil
        "சென்னை": "Chennai",
        "மும்பை": "Mumbai",
        "பெங்களூர்": "Bengaluru",
        "ஹைதராபாத்": "Hyderabad",
        "கொச்சி": "Kochi",
        "மதுரை": "Madurai",
        "கோயம்புத்தூர்": "Coimbatore",
        # Telugu
        "హైదరాబాద్": "Hyderabad",
        "విశాఖపట్నం": "Visakhapatnam",
        "చెన్నై": "Chennai",
        "బెంగళూరు": "Bengaluru",
        "ముంబై": "Mumbai",
        # Bengali
        "কলকাতা": "Kolkata",
        "মুম্বই": "Mumbai",
        "দিল্লি": "Delhi",
        "বেঙ্গালুরু": "Bengaluru",
        "চেন্নাই": "Chennai",
        # Marathi
        "मुंबई": "Mumbai",
        "पुणे": "Pune",
        "नागपूर": "Nagpur",
    }

    cities = [
        "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "kolkata",
        "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow", "noida",
        "gurgaon", "gurugram", "ghaziabad", "faridabad", "chandigarh",
        "kochi", "cochin", "thiruvananthapuram", "trivandrum", "indore",
        "bhopal", "nagpur", "vadodara", "surat", "rajkot", "coimbatore",
        "madurai", "visakhapatnam", "vizag", "patna", "ranchi", "bhubaneswar",
        "guwahati", "dehradun", "shimla", "manali", "jaipur", "udaipur",
        "jodhpur", "agra", "varanasi", "amritsar", "ludhiana", "mysore",
        "mangalore", "hubli", "belgaum", "goa", "cuttack",
    ]

    # Check for native script city names first
    for script_city, english_city in city_aliases.items():
        if script_city in query:
            return english_city

    # Check for English city names
    query_lower = query.lower()
    for city in cities:
        if city in query_lower:
            return city_aliases.get(city, city.title())

    return None


def _extract_cuisine(query: str) -> Optional[str]:
    """Extract cuisine type from query."""
    query_lower = query.lower()
    for cuisine in CUISINES:
        if cuisine in query_lower:
            return cuisine
    return None


def _extract_dish(query: str) -> Optional[str]:
    """Extract specific dish from query."""
    dishes = [
        "biryani", "pizza", "burger", "dosa", "idli", "paratha", "noodles",
        "momos", "pasta", "kebab", "tandoori", "tikka", "paneer", "chicken",
        "mutton", "fish", "prawn", "thali", "pav bhaji", "vada pav",
        "chole bhature", "samosa", "pakora", "chaat", "pani puri", "sev puri",
        "rolls", "shawarma", "fries", "sandwich", "wrap", "salad", "soup",
        "ice cream", "cake", "brownie", "gulab jamun", "rasgulla", "jalebi",
        "coffee", "tea", "chai", "lassi", "milkshake", "smoothie", "juice",
        "fried rice", "manchurian", "chilli chicken", "butter chicken",
        "dal makhani", "palak paneer", "malai kofta", "naan", "roti", "rice",
    ]

    query_lower = query.lower()
    for dish in dishes:
        if dish in query_lower:
            return dish
    return None


async def _get_city_from_location(location: dict) -> Optional[str]:
    """
    Get city name from location coordinates using reverse geocoding.

    Args:
        location: Dict with 'latitude' and 'longitude' keys

    Returns:
        City name or None if not found
    """
    try:
        lat = location.get("latitude")
        lon = location.get("longitude")

        if not lat or not lon:
            return None

        # Use Nominatim (OpenStreetMap) for reverse geocoding
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "D23Bot/1.0"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})

                # Try different address fields for city
                city = (
                    address.get("city") or
                    address.get("town") or
                    address.get("municipality") or
                    address.get("county") or
                    address.get("state_district")
                )

                if city:
                    logger.info(f"Reverse geocoding: ({lat}, {lon}) -> {city}")
                    return city

        return None

    except Exception as e:
        logger.error(f"Error in reverse geocoding: {e}")
        return None


def _is_detail_query(query: str) -> Optional[str]:
    """
    Check if query is asking for restaurant details.
    Returns restaurant name if found, None otherwise.
    """
    query_lower = query.lower()

    # Patterns for detail queries
    detail_patterns = [
        r"details?\s+(?:of|about|for)\s+(.+?)(?:\s+in\s+|\s+at\s+|$)",
        r"(?:more|info|information)\s+(?:about|on)\s+(.+?)(?:\s+in\s+|\s+at\s+|$)",
        r"tell\s+(?:me\s+)?about\s+(.+?)(?:\s+restaurant|\s+in\s+|\s+at\s+|$)",
        r"(.+?)\s+details",
        r"(.+?)\s+(?:restaurant\s+)?info",
    ]

    for pattern in detail_patterns:
        match = re.search(pattern, query_lower)
        if match:
            restaurant_name = match.group(1).strip()
            # Clean up common words
            for word in ["restaurant", "the", "about", "please"]:
                restaurant_name = restaurant_name.replace(word, "").strip()
            if restaurant_name and len(restaurant_name) > 2:
                return restaurant_name

    return None


async def handle_food(state: BotState) -> dict:
    """
    Handle food and restaurant queries.

    Supports:
    - Restaurant search by city
    - Cuisine filtering
    - Dish-based search
    - Restaurant details

    Args:
        state: Current bot state

    Returns:
        Updated state with restaurant information
    """
    query = state.get("current_query", "")

    try:
        # Check if this is a restaurant detail query
        restaurant_name = _is_detail_query(query)
        if restaurant_name:
            city = _extract_city(query)
            # Try to find restaurant in all cities if no city specified
            cities_to_search = [city] if city else ["mumbai", "delhi", "bengaluru", "chennai", "hyderabad", "bhubaneswar"]

            for search_city in cities_to_search:
                if search_city:
                    restaurant = await get_restaurant_details(restaurant_name, search_city)
                    if restaurant:
                        response_text = format_restaurant_detail(restaurant)
                        return {
                            "response_text": response_text,
                            "response_type": "text",
                            "should_fallback": False,
                            "intent": INTENT,
                            "tool_result": restaurant,
                        }

            # Restaurant not found
            return {
                "response_text": f"Sorry, I couldn't find details for '{restaurant_name}'. Try searching for restaurants in a specific city first.",
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        # Extract filters from query
        city = _extract_city(query)
        cuisine = _extract_cuisine(query)
        dish = _extract_dish(query)

        # Default city if none found
        if not city:
            # Check if there's a location in state
            location = state.get("whatsapp_message", {}).get("location")
            if location:
                # Clear the pending search since we received the location
                phone = state.get("whatsapp_message", {}).get("from_number", "")
                if phone:
                    pending_store = get_pending_location_store()
                    await pending_store.get_pending_search(phone)  # Consume and clear
                    logger.info(f"Cleared pending food search for {phone}")

                # Use reverse geocoding to get city from coordinates
                city = await _get_city_from_location(location)
                if not city:
                    city = "Bengaluru"  # Default fallback
            else:
                # Check if user is asking for "near me" type query
                near_me_patterns = ["near me", "nearby", "close to me", "around me", "mere paas", "मेरे पास", "ನನ್ನ ಬಳಿ", "ମୋ ପାଖରେ"]
                is_near_me = any(p in query.lower() for p in near_me_patterns)

                if is_near_me:
                    # Save pending search so we can continue when location is received
                    phone = state.get("whatsapp_message", {}).get("from_number", "")
                    if phone:
                        pending_store = get_pending_location_store()
                        await pending_store.save_pending_search(
                            phone=phone,
                            search_query="__food__",
                            original_message=query,
                        )
                        logger.info(f"Saved pending food search for {phone}")

                    return {
                        "response_text": "📍 Share your location to find restaurants near you!\n\n"
                                        "Or type a city name like \"Restaurants in Mumbai\"",
                        "response_type": "location_request",
                        "should_fallback": False,
                        "intent": INTENT,
                    }
                else:
                    return {
                        "response_text": "🍽️ Please specify a city for restaurant search.\n\nExample:\n• \"Restaurants in Mumbai\"\n• \"Pizza in Bangalore\"\n• \"Biryani near Hyderabad\"\n\n"
                                        "Or share your 📍 location to find restaurants near you!",
                        "response_type": "text",
                        "should_fallback": False,
                        "intent": INTENT,
                    }

        # Search restaurants
        search_query = dish if dish else None
        result = await search_restaurants(
            city=city,
            cuisine=cuisine,
            query=search_query,
            max_results=5,
        )

        response_text = format_restaurant_response(result)

        return {
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "tool_result": result,
        }

    except Exception as e:
        logger.error(f"Error in handle_food: {e}")
        return {
            "response_text": "Sorry, I couldn't search for restaurants right now. Please try again later.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
