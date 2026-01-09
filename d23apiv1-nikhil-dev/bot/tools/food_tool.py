"""
Food Discovery Tool

Searches for restaurants and food options using web search.
Provides restaurant info with deep links to Zomato/Swiggy for ordering.

Note: Direct ordering via Zomato MCP is not available for third-party apps.
This tool provides discovery and redirects users to ordering platforms.
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from bot.config import settings

logger = logging.getLogger(__name__)

# Popular cuisines in India
CUISINES = [
    "north indian", "south indian", "chinese", "italian", "mexican",
    "thai", "japanese", "korean", "continental", "mughlai", "punjabi",
    "bengali", "gujarati", "rajasthani", "kerala", "hyderabadi", "biryani",
    "pizza", "burger", "fast food", "street food", "cafe", "desserts",
    "ice cream", "bakery", "healthy", "salads", "seafood", "vegetarian",
]

# Sample restaurant data for demo (would be replaced with real API/scraping)
SAMPLE_RESTAURANTS: Dict[str, List[Dict]] = {
    "bengaluru": [
        {
            "name": "Meghana Foods",
            "cuisine": "Biryani, Andhra",
            "rating": 4.5,
            "price_for_two": 600,
            "address": "Residency Road, Bengaluru",
            "delivery_time": "30-35 min",
            "offers": ["50% off up to ₹100", "Free delivery"],
            "popular_dishes": ["Chicken Biryani", "Mutton Biryani", "Andhra Meals"],
            "zomato_link": "https://www.zomato.com/bangalore/meghana-foods-residency-road",
            "swiggy_link": "https://www.swiggy.com/restaurants/meghana-foods-residency-road-bangalore",
        },
        {
            "name": "Truffles",
            "cuisine": "American, Burgers",
            "rating": 4.4,
            "price_for_two": 800,
            "address": "Koramangala, Bengaluru",
            "delivery_time": "35-40 min",
            "offers": ["20% off on orders above ₹500"],
            "popular_dishes": ["Truffles Burger", "Pasta", "Steak"],
            "zomato_link": "https://www.zomato.com/bangalore/truffles-koramangala",
            "swiggy_link": "https://www.swiggy.com/restaurants/truffles-koramangala-bangalore",
        },
        {
            "name": "Empire Restaurant",
            "cuisine": "Biryani, North Indian",
            "rating": 4.2,
            "price_for_two": 500,
            "address": "Church Street, Bengaluru",
            "delivery_time": "25-30 min",
            "offers": ["Free delivery on first order"],
            "popular_dishes": ["Empire Special Biryani", "Kebabs", "Rumali Roti"],
            "zomato_link": "https://www.zomato.com/bangalore/empire-restaurant-church-street",
            "swiggy_link": "https://www.swiggy.com/restaurants/empire-restaurant-church-street-bangalore",
        },
        {
            "name": "MTR - Mavalli Tiffin Rooms",
            "cuisine": "South Indian",
            "rating": 4.6,
            "price_for_two": 400,
            "address": "Lalbagh Road, Bengaluru",
            "delivery_time": "30-35 min",
            "offers": [],
            "popular_dishes": ["Masala Dosa", "Rava Idli", "Filter Coffee"],
            "zomato_link": "https://www.zomato.com/bangalore/mtr-lalbagh-road",
            "swiggy_link": "https://www.swiggy.com/restaurants/mtr-lalbagh-road-bangalore",
        },
        {
            "name": "Vidyarthi Bhavan",
            "cuisine": "South Indian",
            "rating": 4.5,
            "price_for_two": 300,
            "address": "Gandhi Bazaar, Bengaluru",
            "delivery_time": "35-40 min",
            "offers": [],
            "popular_dishes": ["Benne Masala Dosa", "Khara Bath", "Kesari Bath"],
            "zomato_link": "https://www.zomato.com/bangalore/vidyarthi-bhavan-gandhi-bazaar",
            "swiggy_link": "https://www.swiggy.com/restaurants/vidyarthi-bhavan-gandhi-bazaar-bangalore",
        },
    ],
    "mumbai": [
        {
            "name": "Bademiya",
            "cuisine": "Mughlai, Kebabs",
            "rating": 4.3,
            "price_for_two": 700,
            "address": "Colaba, Mumbai",
            "delivery_time": "30-35 min",
            "offers": ["10% off on orders above ₹400"],
            "popular_dishes": ["Seekh Kebab Roll", "Chicken Tikka", "Baida Roti"],
            "zomato_link": "https://www.zomato.com/mumbai/bademiya-colaba",
            "swiggy_link": "https://www.swiggy.com/restaurants/bademiya-colaba-mumbai",
        },
        {
            "name": "Cafe Leopold",
            "cuisine": "Continental, Indian",
            "rating": 4.1,
            "price_for_two": 1200,
            "address": "Colaba, Mumbai",
            "delivery_time": "40-45 min",
            "offers": [],
            "popular_dishes": ["Butter Chicken", "Fish & Chips", "Beer"],
            "zomato_link": "https://www.zomato.com/mumbai/cafe-leopold-colaba",
            "swiggy_link": "https://www.swiggy.com/restaurants/cafe-leopold-colaba-mumbai",
        },
        {
            "name": "Swati Snacks",
            "cuisine": "Gujarati, Street Food",
            "rating": 4.5,
            "price_for_two": 500,
            "address": "Tardeo, Mumbai",
            "delivery_time": "35-40 min",
            "offers": ["Free delivery"],
            "popular_dishes": ["Panki", "Dahi Batata Puri", "Sev Puri"],
            "zomato_link": "https://www.zomato.com/mumbai/swati-snacks-tardeo",
            "swiggy_link": "https://www.swiggy.com/restaurants/swati-snacks-tardeo-mumbai",
        },
        {
            "name": "Britannia & Co.",
            "cuisine": "Parsi, Iranian",
            "rating": 4.4,
            "price_for_two": 800,
            "address": "Ballard Estate, Mumbai",
            "delivery_time": "45-50 min",
            "offers": [],
            "popular_dishes": ["Berry Pulao", "Salli Boti", "Caramel Custard"],
            "zomato_link": "https://www.zomato.com/mumbai/britannia-co-ballard-estate",
            "swiggy_link": "https://www.swiggy.com/restaurants/britannia-ballard-estate-mumbai",
        },
    ],
    "delhi": [
        {
            "name": "Karim's",
            "cuisine": "Mughlai, North Indian",
            "rating": 4.4,
            "price_for_two": 600,
            "address": "Jama Masjid, Old Delhi",
            "delivery_time": "35-40 min",
            "offers": ["20% off up to ₹150"],
            "popular_dishes": ["Mutton Burra", "Chicken Jahangiri", "Seekh Kebab"],
            "zomato_link": "https://www.zomato.com/ncr/karims-jama-masjid-old-delhi",
            "swiggy_link": "https://www.swiggy.com/restaurants/karims-jama-masjid-delhi",
        },
        {
            "name": "Paranthe Wali Gali",
            "cuisine": "North Indian, Street Food",
            "rating": 4.2,
            "price_for_two": 300,
            "address": "Chandni Chowk, Delhi",
            "delivery_time": "30-35 min",
            "offers": [],
            "popular_dishes": ["Aloo Parantha", "Paneer Parantha", "Rabdi"],
            "zomato_link": "https://www.zomato.com/ncr/paranthe-wali-gali-chandni-chowk",
            "swiggy_link": "https://www.swiggy.com/restaurants/paranthe-wali-gali-chandni-chowk-delhi",
        },
        {
            "name": "Bukhara",
            "cuisine": "North Indian, Mughlai",
            "rating": 4.7,
            "price_for_two": 6000,
            "address": "ITC Maurya, Chanakyapuri",
            "delivery_time": "50-60 min",
            "offers": [],
            "popular_dishes": ["Dal Bukhara", "Sikandari Raan", "Tandoori Jhinga"],
            "zomato_link": "https://www.zomato.com/ncr/bukhara-itc-maurya-chanakyapuri",
            "swiggy_link": "https://www.swiggy.com/restaurants/bukhara-chanakyapuri-delhi",
        },
        {
            "name": "Haldiram's",
            "cuisine": "North Indian, Street Food",
            "rating": 4.1,
            "price_for_two": 400,
            "address": "Chandni Chowk, Delhi",
            "delivery_time": "25-30 min",
            "offers": ["Free delivery on orders above ₹199"],
            "popular_dishes": ["Chole Bhature", "Pav Bhaji", "Sweets"],
            "zomato_link": "https://www.zomato.com/ncr/haldirams-chandni-chowk",
            "swiggy_link": "https://www.swiggy.com/restaurants/haldirams-chandni-chowk-delhi",
        },
    ],
    "chennai": [
        {
            "name": "Saravana Bhavan",
            "cuisine": "South Indian",
            "rating": 4.3,
            "price_for_two": 400,
            "address": "T. Nagar, Chennai",
            "delivery_time": "30-35 min",
            "offers": ["10% off on first order"],
            "popular_dishes": ["Ghee Roast Dosa", "Mini Tiffin", "Curd Rice"],
            "zomato_link": "https://www.zomato.com/chennai/saravana-bhavan-t-nagar",
            "swiggy_link": "https://www.swiggy.com/restaurants/saravana-bhavan-t-nagar-chennai",
        },
        {
            "name": "Murugan Idli Shop",
            "cuisine": "South Indian",
            "rating": 4.5,
            "price_for_two": 300,
            "address": "Besant Nagar, Chennai",
            "delivery_time": "25-30 min",
            "offers": [],
            "popular_dishes": ["Soft Idli", "Podi Idli", "Sambar"],
            "zomato_link": "https://www.zomato.com/chennai/murugan-idli-shop-besant-nagar",
            "swiggy_link": "https://www.swiggy.com/restaurants/murugan-idli-shop-besant-nagar-chennai",
        },
        {
            "name": "Anjappar",
            "cuisine": "Chettinad",
            "rating": 4.2,
            "price_for_two": 700,
            "address": "Anna Nagar, Chennai",
            "delivery_time": "35-40 min",
            "offers": ["20% off up to ₹120"],
            "popular_dishes": ["Chettinad Chicken", "Mutton Chukka", "Parotta"],
            "zomato_link": "https://www.zomato.com/chennai/anjappar-anna-nagar",
            "swiggy_link": "https://www.swiggy.com/restaurants/anjappar-anna-nagar-chennai",
        },
    ],
    "hyderabad": [
        {
            "name": "Paradise Biryani",
            "cuisine": "Biryani, Hyderabadi",
            "rating": 4.3,
            "price_for_two": 600,
            "address": "Secunderabad, Hyderabad",
            "delivery_time": "30-35 min",
            "offers": ["Free delivery on orders above ₹299"],
            "popular_dishes": ["Chicken Biryani", "Mutton Biryani", "Kebabs"],
            "zomato_link": "https://www.zomato.com/hyderabad/paradise-secunderabad",
            "swiggy_link": "https://www.swiggy.com/restaurants/paradise-secunderabad-hyderabad",
        },
        {
            "name": "Bawarchi",
            "cuisine": "Biryani, North Indian",
            "rating": 4.2,
            "price_for_two": 500,
            "address": "RTC Cross Roads, Hyderabad",
            "delivery_time": "25-30 min",
            "offers": ["50% off up to ₹100"],
            "popular_dishes": ["Special Biryani", "Chicken 65", "Haleem"],
            "zomato_link": "https://www.zomato.com/hyderabad/bawarchi-rtc-cross-roads",
            "swiggy_link": "https://www.swiggy.com/restaurants/bawarchi-rtc-cross-roads-hyderabad",
        },
        {
            "name": "Shah Ghouse",
            "cuisine": "Biryani, Hyderabadi",
            "rating": 4.4,
            "price_for_two": 550,
            "address": "Tolichowki, Hyderabad",
            "delivery_time": "30-35 min",
            "offers": [],
            "popular_dishes": ["Mutton Biryani", "Paya", "Haleem"],
            "zomato_link": "https://www.zomato.com/hyderabad/shah-ghouse-tolichowki",
            "swiggy_link": "https://www.swiggy.com/restaurants/shah-ghouse-tolichowki-hyderabad",
        },
    ],
    "bhubaneswar": [
        {
            "name": "Dalma",
            "cuisine": "Odia, Indian",
            "rating": 4.4,
            "price_for_two": 500,
            "address": "Saheed Nagar, Bhubaneswar",
            "delivery_time": "30-35 min",
            "offers": ["20% off on first order"],
            "popular_dishes": ["Dalma", "Pakhala Bhata", "Machha Besara", "Chhena Poda"],
            "zomato_link": "https://www.zomato.com/bhubaneswar/dalma-saheed-nagar",
            "swiggy_link": "https://www.swiggy.com/restaurants/dalma-saheed-nagar-bhubaneswar",
        },
        {
            "name": "Odisha Hotel",
            "cuisine": "Odia, Seafood",
            "rating": 4.3,
            "price_for_two": 400,
            "address": "Master Canteen, Bhubaneswar",
            "delivery_time": "25-30 min",
            "offers": [],
            "popular_dishes": ["Pakhala", "Machha Jhola", "Mutton Curry", "Chingudi Tarkari"],
            "zomato_link": "https://www.zomato.com/bhubaneswar/odisha-hotel-master-canteen",
            "swiggy_link": "https://www.swiggy.com/restaurants/odisha-hotel-master-canteen-bhubaneswar",
        },
        {
            "name": "Hare Krishna",
            "cuisine": "Pure Veg, South Indian",
            "rating": 4.5,
            "price_for_two": 350,
            "address": "Janpath, Bhubaneswar",
            "delivery_time": "30-35 min",
            "offers": ["Free delivery"],
            "popular_dishes": ["Thali", "Dosa", "Idli", "Rasmalai"],
            "zomato_link": "https://www.zomato.com/bhubaneswar/hare-krishna-janpath",
            "swiggy_link": "https://www.swiggy.com/restaurants/hare-krishna-janpath-bhubaneswar",
        },
        {
            "name": "Truptee",
            "cuisine": "Odia, North Indian",
            "rating": 4.2,
            "price_for_two": 450,
            "address": "Rasulgarh, Bhubaneswar",
            "delivery_time": "35-40 min",
            "offers": ["10% off on orders above ₹300"],
            "popular_dishes": ["Odia Thali", "Santula", "Ghanta", "Kheer"],
            "zomato_link": "https://www.zomato.com/bhubaneswar/truptee-rasulgarh",
            "swiggy_link": "https://www.swiggy.com/restaurants/truptee-rasulgarh-bhubaneswar",
        },
    ],
}

# City aliases
CITY_ALIASES = {
    "bangalore": "bengaluru",
    "bombay": "mumbai",
    "madras": "chennai",
    "calcutta": "kolkata",
}


def normalize_city(city: str) -> str:
    """Normalize city name to match our data."""
    city_lower = city.lower().strip()
    return CITY_ALIASES.get(city_lower, city_lower)


async def search_restaurants(
    city: str,
    cuisine: Optional[str] = None,
    query: Optional[str] = None,
    max_results: int = 5,
) -> Dict[str, Any]:
    """
    Search for restaurants in a city.

    Args:
        city: City name
        cuisine: Optional cuisine filter
        query: Optional search query (dish or restaurant name)
        max_results: Maximum results to return

    Returns:
        Dict with restaurants and metadata
    """
    city_normalized = normalize_city(city)
    restaurants = SAMPLE_RESTAURANTS.get(city_normalized, [])

    if not restaurants:
        # Try to find partial match
        for city_key in SAMPLE_RESTAURANTS:
            if city_normalized in city_key or city_key in city_normalized:
                restaurants = SAMPLE_RESTAURANTS[city_key]
                break

    # Filter by cuisine if specified
    if cuisine and restaurants:
        cuisine_lower = cuisine.lower()
        restaurants = [
            r for r in restaurants
            if cuisine_lower in r.get("cuisine", "").lower()
        ]

    # Filter by query (dish or restaurant name)
    if query and restaurants:
        query_lower = query.lower()
        restaurants = [
            r for r in restaurants
            if query_lower in r.get("name", "").lower()
            or any(query_lower in dish.lower() for dish in r.get("popular_dishes", []))
            or query_lower in r.get("cuisine", "").lower()
        ]

    # Sort by rating
    restaurants = sorted(restaurants, key=lambda x: x.get("rating", 0), reverse=True)

    return {
        "city": city,
        "cuisine": cuisine,
        "query": query,
        "count": len(restaurants[:max_results]),
        "restaurants": restaurants[:max_results],
    }


async def get_restaurant_details(restaurant_name: str, city: str) -> Optional[Dict]:
    """Get details for a specific restaurant."""
    city_normalized = normalize_city(city)
    restaurants = SAMPLE_RESTAURANTS.get(city_normalized, [])

    name_lower = restaurant_name.lower()
    for r in restaurants:
        if name_lower in r.get("name", "").lower():
            return r

    return None


def format_restaurant_response(result: Dict[str, Any]) -> str:
    """Format restaurant search results for WhatsApp."""
    restaurants = result.get("restaurants", [])
    city = result.get("city", "")
    cuisine = result.get("cuisine", "")
    query = result.get("query", "")

    if not restaurants:
        return f"No restaurants found in {city}" + (f" for '{cuisine}'" if cuisine else "") + ". Try a different search!"

    header = f"🍽️ *Restaurants in {city.title()}*"
    if cuisine:
        header += f" ({cuisine.title()})"
    if query:
        header += f"\n🔍 Search: {query}"
    header += "\n\n"

    response = header

    for i, r in enumerate(restaurants, 1):
        name = r.get("name", "Unknown")
        cuisine_type = r.get("cuisine", "")
        rating = r.get("rating", 0)
        price = r.get("price_for_two", 0)
        delivery = r.get("delivery_time", "")
        offers = r.get("offers", [])
        dishes = r.get("popular_dishes", [])[:3]

        response += f"*{i}. {name}*\n"
        response += f"⭐ {rating} | 🍴 {cuisine_type}\n"
        response += f"💰 ₹{price} for two | 🕐 {delivery}\n"

        if offers:
            response += f"🎁 {offers[0]}\n"

        if dishes:
            response += f"🍛 {', '.join(dishes)}\n"

        response += "\n"

    response += "📱 *To order:*\n"
    response += "• Open Zomato or Swiggy app\n"
    response += "• Search for the restaurant\n"
    response += "• Add items and checkout\n\n"
    response += "_Ask \"details of <restaurant name>\" for more info!_"

    return response


def format_restaurant_detail(restaurant: Dict) -> str:
    """Format single restaurant details."""
    name = restaurant.get("name", "Unknown")
    cuisine = restaurant.get("cuisine", "")
    rating = restaurant.get("rating", 0)
    price = restaurant.get("price_for_two", 0)
    address = restaurant.get("address", "")
    delivery = restaurant.get("delivery_time", "")
    offers = restaurant.get("offers", [])
    dishes = restaurant.get("popular_dishes", [])
    zomato = restaurant.get("zomato_link", "")
    swiggy = restaurant.get("swiggy_link", "")

    response = f"🍽️ *{name}*\n\n"
    response += f"⭐ Rating: {rating}/5\n"
    response += f"🍴 Cuisine: {cuisine}\n"
    response += f"💰 ₹{price} for two\n"
    response += f"📍 {address}\n"
    response += f"🕐 Delivery: {delivery}\n\n"

    if offers:
        response += "*🎁 Offers:*\n"
        for offer in offers:
            response += f"• {offer}\n"
        response += "\n"

    if dishes:
        response += "*🍛 Popular Dishes:*\n"
        for dish in dishes:
            response += f"• {dish}\n"
        response += "\n"

    response += "*📱 Order Now:*\n"
    if zomato:
        response += f"• Zomato: {zomato}\n"
    if swiggy:
        response += f"• Swiggy: {swiggy}\n"

    return response
