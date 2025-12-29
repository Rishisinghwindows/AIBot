"""
Serper Google Search API Tool

Wrapper for Serper API for Google search functionality.
Get API key from: https://serper.dev/
"""

import httpx
import logging
import math
from typing import Optional, List, Dict, Any

from bot.config import settings
from bot.state import ToolResult

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"

# Free reverse geocoding API
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Overpass API for OpenStreetMap queries
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.

    Returns distance in kilometers.
    """
    # Radius of Earth in km
    R = 6371.0

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def _format_distance(distance_km: float) -> str:
    """Format distance for display."""
    if distance_km < 1:
        return f"{int(distance_km * 1000)}m"
    else:
        return f"{distance_km:.1f}km"


def _generate_google_maps_link(latitude: float, longitude: float, place_name: str = "") -> str:
    """Generate Google Maps link for a location."""
    # Use place name for better search if available, otherwise use coordinates
    if place_name:
        # URL encode the place name
        import urllib.parse
        encoded_name = urllib.parse.quote(place_name)
        return f"https://www.google.com/maps/search/?api=1&query={encoded_name}&query_place_id={latitude},{longitude}"
    else:
        return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"


# Map common search terms to OSM amenity/shop tags
PLACE_TYPE_MAPPING = {
    # Food & Drink
    "restaurant": ["amenity=restaurant"],
    "hotel": ["tourism=hotel", "tourism=guest_house", "tourism=motel"],
    "cafe": ["amenity=cafe"],
    "bar": ["amenity=bar", "amenity=pub"],
    "food": ["amenity=restaurant", "amenity=fast_food", "amenity=cafe"],
    "fast food": ["amenity=fast_food"],
    "bakery": ["shop=bakery"],
    "sweet": ["shop=confectionery", "shop=pastry"],
    "tea": ["amenity=cafe", "shop=tea"],
    "coffee": ["amenity=cafe"],
    "dhaba": ["amenity=restaurant", "amenity=fast_food"],

    # Shopping
    "shop": ["shop=supermarket", "shop=convenience", "shop=general"],
    "supermarket": ["shop=supermarket"],
    "grocery": ["shop=supermarket", "shop=convenience", "shop=grocery"],
    "mall": ["shop=mall", "shop=department_store"],
    "market": ["amenity=marketplace", "shop=supermarket"],
    "clothes": ["shop=clothes"],
    "electronics": ["shop=electronics"],
    "mobile": ["shop=mobile_phone"],
    "pharmacy": ["amenity=pharmacy"],
    "medical": ["amenity=pharmacy", "amenity=clinic"],
    "chemist": ["amenity=pharmacy"],

    # Services
    "atm": ["amenity=atm"],
    "bank": ["amenity=bank"],
    "petrol": ["amenity=fuel"],
    "fuel": ["amenity=fuel"],
    "gas station": ["amenity=fuel"],
    "parking": ["amenity=parking"],
    "mechanic": ["shop=car_repair", "shop=motorcycle_repair"],
    "garage": ["shop=car_repair"],
    "salon": ["shop=hairdresser", "shop=beauty"],
    "barber": ["shop=hairdresser"],

    # Health
    "hospital": ["amenity=hospital"],
    "clinic": ["amenity=clinic", "amenity=doctors"],
    "doctor": ["amenity=doctors", "amenity=clinic"],
    "dentist": ["amenity=dentist"],

    # Transport
    "bus": ["amenity=bus_station", "highway=bus_stop"],
    "train": ["railway=station"],
    "metro": ["railway=station", "station=subway"],

    # Others
    "mandir": ["amenity=place_of_worship"],
    "temple": ["amenity=place_of_worship"],
    "mosque": ["amenity=place_of_worship"],
    "church": ["amenity=place_of_worship"],
    "school": ["amenity=school"],
    "college": ["amenity=college", "amenity=university"],
    "gym": ["leisure=fitness_centre", "leisure=sports_centre"],
    "park": ["leisure=park"],
    "cinema": ["amenity=cinema"],
    "theater": ["amenity=theatre"],
}


async def _search_places_by_coordinates(
    query: str,
    latitude: float,
    longitude: float,
    max_results: int = 5,
    radius_meters: int = 10000,  # 10km radius
) -> ToolResult:
    """
    Search for places near coordinates using Overpass API (OpenStreetMap).

    Args:
        query: What to search for (e.g., "restaurant", "hotel")
        latitude: User's latitude
        longitude: User's longitude
        max_results: Maximum results to return
        radius_meters: Search radius in meters

    Returns:
        ToolResult with nearby places
    """
    try:
        # Find matching OSM tags for the query
        query_lower = query.lower().strip()
        osm_tags = None

        for keyword, tags in PLACE_TYPE_MAPPING.items():
            if keyword in query_lower or query_lower in keyword:
                osm_tags = tags
                break

        # Default to common amenities if no match
        if not osm_tags:
            osm_tags = [
                f"name~'{query}'",  # Search by name
            ]

        # Build simplified Overpass query (nodes only for faster response)
        tag_queries = []
        for tag in osm_tags[:2]:  # Limit to first 2 tags to reduce query size
            if "=" in tag:
                key, value = tag.split("=", 1)
                # Use nodes only for faster queries
                tag_queries.append(f'node["{key}"="{value}"](around:{radius_meters},{latitude},{longitude});')
            else:
                # Name search
                tag_queries.append(f'node[{tag},i](around:{radius_meters},{latitude},{longitude});')

        overpass_query = f"""
        [out:json][timeout:25];
        (
            {chr(10).join(tag_queries)}
        );
        out center {max_results * 3};
        """

        logger.info(f"Overpass query for '{query}' at {latitude},{longitude} within {radius_meters}m")

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                OVERPASS_URL,
                data={"data": overpass_query},
                headers={"User-Agent": "D23Bot/1.0"}
            )

            if response.status_code != 200:
                logger.error(f"Overpass API error: {response.status_code}")
                # Fallback to Serper with distance filtering
                logger.info(f"Falling back to Serper for '{query}'")
                location_name = await _reverse_geocode(latitude, longitude)
                return await _serper_places_with_distance_filter(
                    query=query,
                    user_lat=latitude,
                    user_lon=longitude,
                    location_name=location_name,
                    radius_km=radius_meters / 1000,
                    max_results=max_results,
                )

            data = response.json()
            elements = data.get("elements", [])

            # Format results with distance calculation
            results = []
            for elem in elements:
                tags = elem.get("tags", {})
                name = tags.get("name") or tags.get("name:en") or tags.get("brand") or "Unknown"

                # Skip if no name
                if name == "Unknown":
                    continue

                # Get coordinates
                if elem.get("type") == "way":
                    center = elem.get("center", {})
                    elem_lat = center.get("lat")
                    elem_lon = center.get("lon")
                else:
                    elem_lat = elem.get("lat")
                    elem_lon = elem.get("lon")

                # Skip if no coordinates
                if not elem_lat or not elem_lon:
                    continue

                # Calculate distance from user's location
                distance_km = _calculate_distance(latitude, longitude, elem_lat, elem_lon)

                # Skip if beyond radius (sometimes Overpass returns extra results)
                if distance_km > (radius_meters / 1000):
                    continue

                # Build address from tags
                address_parts = []
                if tags.get("addr:street"):
                    address_parts.append(tags.get("addr:street"))
                if tags.get("addr:city"):
                    address_parts.append(tags.get("addr:city"))
                if tags.get("addr:district"):
                    address_parts.append(tags.get("addr:district"))
                if tags.get("addr:state"):
                    address_parts.append(tags.get("addr:state"))

                address = ", ".join(address_parts) if address_parts else tags.get("address", "")

                # Generate Google Maps link
                maps_link = _generate_google_maps_link(elem_lat, elem_lon, name)

                results.append({
                    "title": name,
                    "address": address,
                    "rating": None,  # OSM doesn't have ratings
                    "reviews": None,
                    "phone": tags.get("phone") or tags.get("contact:phone"),
                    "website": tags.get("website") or tags.get("contact:website"),
                    "category": tags.get("amenity") or tags.get("shop") or tags.get("tourism"),
                    "hours": tags.get("opening_hours"),
                    "latitude": elem_lat,
                    "longitude": elem_lon,
                    "distance_km": distance_km,
                    "distance_text": _format_distance(distance_km),
                    "maps_link": maps_link,
                })

            # Sort by distance (closest first) and limit results
            results.sort(key=lambda x: x["distance_km"])
            results = results[:max_results]

            # Get location name for display
            location_name = await _reverse_geocode(latitude, longitude)

            if results:
                logger.info(f"Found {len(results)} places for '{query}' near {latitude},{longitude}")
                return ToolResult(
                    success=True,
                    data={
                        "query": query,
                        "places": results,
                        "location_name": location_name,
                    },
                    error=None,
                    tool_name="overpass_places",
                )
            else:
                # No results from Overpass within 10km radius
                # Fallback to Serper with distance filtering to try broader search
                logger.info(f"No Overpass results within {radius_meters/1000}km, trying Serper fallback for '{query}'")
                return await _serper_places_with_distance_filter(
                    query=query,
                    user_lat=latitude,
                    user_lon=longitude,
                    location_name=location_name,
                    radius_km=radius_meters / 1000,
                    max_results=max_results,
                )

    except Exception as e:
        logger.error(f"Overpass search failed: {e}")
        # Fallback to Serper with distance filtering
        logger.info(f"Exception fallback to Serper for '{query}'")
        location_name = await _reverse_geocode(latitude, longitude) if latitude and longitude else "your location"
        return await _serper_places_with_distance_filter(
            query=query,
            user_lat=latitude,
            user_lon=longitude,
            location_name=location_name,
            radius_km=radius_meters / 1000,
            max_results=max_results,
        )


async def _serper_places_with_distance_filter(
    query: str,
    user_lat: float,
    user_lon: float,
    location_name: str,
    radius_km: float = 10.0,
    max_results: int = 5,
) -> ToolResult:
    """
    Serper Places search with distance filtering to maintain 10km radius accuracy.

    Args:
        query: Search query
        user_lat: User's latitude
        user_lon: User's longitude
        location_name: Location name for display
        radius_km: Maximum radius in kilometers
        max_results: Maximum results to return

    Returns:
        ToolResult with filtered places within radius
    """
    if not settings.SERPER_API_KEY:
        return ToolResult(
            success=False,
            data={
                "query": query,
                "places": [],
                "location_name": location_name,
            },
            error="Search service unavailable",
            tool_name="serper_places",
        )

    try:
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json",
        }

        # Search with location context
        search_query = f"{query} near {location_name}" if location_name else query

        payload = {
            "q": search_query,
            "gl": "in",
            "num": 20,  # Get more results to filter by distance
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://google.serper.dev/places",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"Serper API error: {response.status_code}")
                return ToolResult(
                    success=False,
                    data={
                        "query": query,
                        "places": [],
                        "location_name": location_name,
                    },
                    error="Search service error",
                    tool_name="serper_places",
                )

            data = response.json()
            places = data.get("places", [])

            # Filter by distance and add distance info
            filtered_results = []
            for place in places:
                # Serper provides GPS coordinates
                place_lat = place.get("latitude")
                place_lon = place.get("longitude")

                if place_lat and place_lon:
                    # Calculate distance
                    distance_km = _calculate_distance(user_lat, user_lon, place_lat, place_lon)

                    # Only include if within radius
                    if distance_km <= radius_km:
                        maps_link = _generate_google_maps_link(place_lat, place_lon, place.get("title", ""))

                        filtered_results.append({
                            "title": place.get("title", ""),
                            "address": place.get("address", ""),
                            "rating": place.get("rating"),
                            "reviews": place.get("ratingCount"),
                            "phone": place.get("phoneNumber"),
                            "website": place.get("website"),
                            "category": place.get("category"),
                            "hours": place.get("openingHours"),
                            "latitude": place_lat,
                            "longitude": place_lon,
                            "distance_km": distance_km,
                            "distance_text": _format_distance(distance_km),
                            "maps_link": maps_link,
                        })

            # Sort by distance and limit
            filtered_results.sort(key=lambda x: x["distance_km"])
            filtered_results = filtered_results[:max_results]

            logger.info(f"Serper: Found {len(filtered_results)} places within {radius_km}km for '{query}'")

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "places": filtered_results,
                    "location_name": location_name,
                    "radius_km": radius_km,
                },
                error=None,
                tool_name="serper_places",
            )

    except Exception as e:
        logger.error(f"Serper search with distance filter failed: {e}")
        return ToolResult(
            success=False,
            data={
                "query": query,
                "places": [],
                "location_name": location_name,
            },
            error="Search service error",
            tool_name="serper_places",
        )


async def _serper_places_search(
    query: str,
    country: str = "in",
    max_results: int = 5,
    location_name: str = None,
) -> ToolResult:
    """Serper Places API search (fallback)."""
    if not settings.SERPER_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Serper API key not configured",
            tool_name="serper_places",
        )

    try:
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json",
        }

        payload = {
            "q": query,
            "gl": country,
            "num": max_results,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://google.serper.dev/places",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Serper API error: {response.status_code}",
                    tool_name="serper_places",
                )

            data = response.json()
            places = data.get("places", [])[:max_results]

            results = []
            for place in places:
                results.append({
                    "title": place.get("title", ""),
                    "address": place.get("address", ""),
                    "rating": place.get("rating"),
                    "reviews": place.get("ratingCount"),
                    "phone": place.get("phoneNumber"),
                    "website": place.get("website"),
                    "category": place.get("category"),
                    "hours": place.get("openingHours"),
                })

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "places": results,
                    "location_name": location_name,
                },
                error=None,
                tool_name="serper_places",
            )

    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="serper_places",
        )


async def _reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Convert coordinates to location name using OpenStreetMap Nominatim.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        Location name (village/town/city, district, state) or None if failed
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "format": "json",
                    "zoom": 18,  # Maximum zoom for village/hamlet level detail
                    "addressdetails": 1,  # Get full address breakdown
                },
                headers={
                    "User-Agent": "D23Bot/1.0"  # Required by Nominatim
                }
            )

            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})

                logger.info(f"Nominatim address response: {address}")

                # Get location hierarchy - prioritize smallest unit first
                village = address.get("village")
                hamlet = address.get("hamlet")
                neighbourhood = address.get("neighbourhood")
                suburb = address.get("suburb")
                town = address.get("town")
                city = address.get("city")
                county = address.get("county")  # Block/Tehsil level
                state_district = address.get("state_district")  # District level
                state = address.get("state", "")

                # Build location string with priority: Village > Hamlet > Neighbourhood > Town > City
                location_parts = []

                # Primary location - most specific first
                primary = village or hamlet or neighbourhood or town or suburb or city or county
                if primary:
                    location_parts.append(primary)

                # Add district for disambiguation if different from primary
                # e.g., "Sadhopur Jiwan, Vaishali" vs "Sadhopur Jiwan, Patna"
                if state_district and state_district != primary:
                    location_parts.append(state_district)
                elif county and county != primary and not state_district:
                    location_parts.append(county)

                # Add state
                if state:
                    location_parts.append(state)

                result = ", ".join(location_parts) if location_parts else None
                logger.info(f"Reverse geocode result: {result}")
                return result

    except Exception as e:
        logger.warning(f"Reverse geocoding failed: {e}")

    return None


async def search_google(
    query: str,
    max_results: int = 5,
    search_type: str = "search",
    country: str = "in",
    locale: str = "en",
) -> ToolResult:
    """
    Search Google using Serper API.

    Args:
        query: Search query
        max_results: Maximum number of results (default 5)
        search_type: Type of search - "search", "images", "news", "places"
        country: Country code for localized results (default "in" for India)
        locale: Language locale (default "en")

    Returns:
        ToolResult with search results or error
    """
    if not settings.SERPER_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Serper API key not configured",
            tool_name="serper_search",
        )

    try:
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json",
        }

        payload = {
            "q": query,
            "gl": country,
            "hl": locale,
            "num": max_results,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                SERPER_API_URL,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"Serper API error: {response.text}")
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Serper API error: {response.status_code}",
                    tool_name="serper_search",
                )

            data = response.json()

            # Extract organic results
            organic_results = data.get("organic", [])[:max_results]

            # Format results
            results = []
            for item in organic_results:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position"),
                })

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "answer": data.get("answerBox", {}).get("answer") or data.get("answerBox", {}).get("snippet"),
                    "results": results,
                    "knowledge_graph": data.get("knowledgeGraph"),
                    "related_searches": data.get("relatedSearches", []),
                },
                error=None,
                tool_name="serper_search",
            )

    except Exception as e:
        logger.error(f"Serper search failed: {e}")
        return ToolResult(
            success=False,
            data=None,
            error=f"Serper search failed for query '{query}': {e}",
            tool_name="serper_search",
        )


async def search_places(
    query: str,
    max_results: int = 5,
    country: str = "in",
    latitude: float = None,
    longitude: float = None,
) -> ToolResult:
    """
    Search for local places using coordinates or text query.

    If lat/lon provided: Uses Overpass API (OpenStreetMap) for accurate nearby search
    Otherwise: Uses Serper Places API for text-based search

    Args:
        query: Search query (e.g., "restaurants" or "restaurants near Delhi")
        max_results: Maximum number of results (default 5)
        country: Country code (default "in" for India)
        latitude: Optional latitude for location-based search
        longitude: Optional longitude for location-based search

    Returns:
        ToolResult with place results or error
    """
    # If coordinates provided, use Overpass API for accurate nearby search
    if latitude is not None and longitude is not None:
        return await _search_places_by_coordinates(query, latitude, longitude, max_results)

    # Otherwise use Serper for text-based search
    return await _serper_places_search(query, country, max_results)


async def search_news(
    query: str,
    max_results: int = 5,
    country: str = "in",
) -> ToolResult:
    """
    Search for news using Serper News API.

    Args:
        query: Search query
        max_results: Maximum number of results (default 5)
        country: Country code (default "in" for India)

    Returns:
        ToolResult with news results or error
    """
    if not settings.SERPER_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Serper API key not configured",
            tool_name="serper_news",
        )

    try:
        headers = {
            "X-API-KEY": settings.SERPER_API_KEY,
            "Content-Type": "application/json",
        }

        payload = {
            "q": query,
            "gl": country,
            "num": max_results,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://google.serper.dev/news",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logger.error(f"Serper News API error: {response.text}")
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Serper News API error: {response.status_code}",
                    tool_name="serper_news",
                )

            data = response.json()
            news = data.get("news", [])[:max_results]

            # Format results
            results = []
            for item in news:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source"),
                    "date": item.get("date"),
                    "image": item.get("imageUrl"),
                })

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "news": results,
                },
                error=None,
                tool_name="serper_news",
            )

    except Exception as e:
        logger.error(f"Serper news search failed: {e}")
        return ToolResult(
            success=False,
            data=None,
            error=f"Serper news search failed for query '{query}': {e}",
            tool_name="serper_news",
        )


# Sync wrappers for compatibility
def search_google_sync(
    query: str,
    max_results: int = 5,
    country: str = "in",
) -> ToolResult:
    """Sync version of search_google."""
    import asyncio
    return asyncio.run(search_google(query, max_results, country=country))
