from __future__ import annotations

from typing import Optional, Dict, Any, List

import httpx

from app.logger import logger


class ZomatoService:
    """
    Zomato API service for restaurant search, reviews, and food ordering.

    Note: Zomato has deprecated their public API. This implementation uses
    available endpoints or can be adapted for RapidAPI alternatives.
    """

    def __init__(
        self,
        *,
        api_key: str = None,
        base_url: str = "https://developers.zomato.com/api/v2.1",
    ):
        self.api_key = api_key or ""
        self.base_url = base_url
        self.available = bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "user-key": self.api_key,
            "Accept": "application/json",
        }

    async def search_restaurants(
        self,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        city_id: Optional[int] = None,
        cuisines: Optional[str] = None,
        sort: str = "rating",
        order: str = "desc",
        count: int = 10,
    ) -> str:
        """
        Search for restaurants.

        Args:
            query: Search query (restaurant name, cuisine, etc.)
            latitude: Optional latitude for location-based search
            longitude: Optional longitude for location-based search
            city_id: Optional Zomato city ID
            cuisines: Comma-separated cuisine IDs
            sort: Sort by - cost, rating, real_distance
            order: asc or desc
            count: Number of results (max 20)
        """
        if not self.available:
            return "Zomato service is not configured. Please add your API key in Settings."

        try:
            params: Dict[str, Any] = {
                "q": query,
                "count": min(count, 20),
                "sort": sort,
                "order": order,
            }
            if latitude and longitude:
                params["lat"] = latitude
                params["lon"] = longitude
            if city_id:
                params["entity_id"] = city_id
                params["entity_type"] = "city"
            if cuisines:
                params["cuisines"] = cuisines

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/search",
                    headers=self._get_headers(),
                    params=params,
                )

                if resp.status_code != 200:
                    return f"Failed to search restaurants: {resp.status_code}"

                data = resp.json()
                restaurants = data.get("restaurants", [])

                if not restaurants:
                    return f"No restaurants found for '{query}'"

                results = []
                for r in restaurants:
                    rest = r.get("restaurant", {})
                    name = rest.get("name", "Unknown")
                    cuisines_list = rest.get("cuisines", "Unknown")
                    location = rest.get("location", {})
                    address = location.get("address", "Unknown")
                    locality = location.get("locality", "")
                    rating = rest.get("user_rating", {})
                    aggregate_rating = rating.get("aggregate_rating", "N/A")
                    votes = rating.get("votes", 0)
                    cost_for_two = rest.get("average_cost_for_two", "N/A")
                    currency = rest.get("currency", "INR")
                    is_delivering = rest.get("is_delivering_now", 0)
                    has_online_delivery = rest.get("has_online_delivery", 0)

                    delivery_text = "Delivers Now" if is_delivering else "Not Delivering"
                    online_text = "Online Order Available" if has_online_delivery else ""

                    results.append(
                        f"- {name} ({aggregate_rating}/5, {votes} votes)\n"
                        f"  Cuisines: {cuisines_list}\n"
                        f"  Location: {locality}, {address}\n"
                        f"  Cost for Two: {currency} {cost_for_two}\n"
                        f"  {delivery_text} | {online_text}"
                    )

                return f"Found {len(restaurants)} restaurants:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("zomato_search_error", error=str(exc))
            return f"Zomato error: {exc}"

    async def get_restaurant_details(self, restaurant_id: str) -> str:
        """Get detailed information about a restaurant."""
        if not self.available:
            return "Zomato service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/restaurant",
                    headers=self._get_headers(),
                    params={"res_id": restaurant_id},
                )

                if resp.status_code != 200:
                    return f"Failed to get restaurant details: {resp.status_code}"

                rest = resp.json()
                name = rest.get("name", "Unknown")
                cuisines = rest.get("cuisines", "Unknown")
                location = rest.get("location", {})
                address = location.get("address", "Unknown")
                city = location.get("city", "Unknown")
                timings = rest.get("timings", "Unknown")
                highlights = rest.get("highlights", [])
                phone = rest.get("phone_numbers", "Unknown")
                rating = rest.get("user_rating", {})
                aggregate_rating = rating.get("aggregate_rating", "N/A")
                rating_text = rating.get("rating_text", "")
                votes = rating.get("votes", 0)
                cost_for_two = rest.get("average_cost_for_two", "N/A")
                currency = rest.get("currency", "INR")
                menu_url = rest.get("menu_url", "")
                photos_url = rest.get("photos_url", "")

                highlights_text = ", ".join(highlights[:5]) if highlights else "None"

                return (
                    f"{name}\n"
                    f"{'=' * len(name)}\n\n"
                    f"Rating: {aggregate_rating}/5 ({rating_text}) - {votes} votes\n"
                    f"Cuisines: {cuisines}\n"
                    f"Cost for Two: {currency} {cost_for_two}\n\n"
                    f"Address: {address}, {city}\n"
                    f"Phone: {phone}\n"
                    f"Timings: {timings}\n\n"
                    f"Highlights: {highlights_text}\n\n"
                    f"Menu: {menu_url}\n"
                    f"Photos: {photos_url}"
                )

        except Exception as exc:
            logger.error("zomato_details_error", error=str(exc))
            return f"Zomato error: {exc}"

    async def get_restaurant_reviews(
        self,
        restaurant_id: str,
        count: int = 5,
    ) -> str:
        """Get reviews for a restaurant."""
        if not self.available:
            return "Zomato service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/reviews",
                    headers=self._get_headers(),
                    params={
                        "res_id": restaurant_id,
                        "count": min(count, 10),
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to get reviews: {resp.status_code}"

                data = resp.json()
                reviews = data.get("user_reviews", [])

                if not reviews:
                    return "No reviews found for this restaurant."

                results = []
                for r in reviews:
                    review = r.get("review", {})
                    rating = review.get("rating", "N/A")
                    text = review.get("review_text", "No review text")
                    user = review.get("user", {})
                    user_name = user.get("name", "Anonymous")
                    review_time = review.get("review_time_friendly", "Unknown")
                    likes = review.get("likes", 0)

                    # Truncate long reviews
                    if len(text) > 200:
                        text = text[:200] + "..."

                    results.append(
                        f"- {user_name} ({rating}/5) - {review_time}\n"
                        f"  \"{text}\"\n"
                        f"  {likes} likes"
                    )

                return f"Reviews:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("zomato_reviews_error", error=str(exc))
            return f"Zomato error: {exc}"

    async def get_cuisines(self, city_id: int) -> str:
        """Get list of cuisines available in a city."""
        if not self.available:
            return "Zomato service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/cuisines",
                    headers=self._get_headers(),
                    params={"city_id": city_id},
                )

                if resp.status_code != 200:
                    return f"Failed to get cuisines: {resp.status_code}"

                data = resp.json()
                cuisines = data.get("cuisines", [])

                if not cuisines:
                    return "No cuisines found for this city."

                results = []
                for c in cuisines:
                    cuisine = c.get("cuisine", {})
                    cuisine_id = cuisine.get("cuisine_id", "")
                    cuisine_name = cuisine.get("cuisine_name", "Unknown")
                    results.append(f"- {cuisine_name} (ID: {cuisine_id})")

                return "Available Cuisines:\n\n" + "\n".join(results)

        except Exception as exc:
            logger.error("zomato_cuisines_error", error=str(exc))
            return f"Zomato error: {exc}"

    async def get_collections(
        self,
        city_id: int,
        count: int = 10,
    ) -> str:
        """Get curated restaurant collections in a city."""
        if not self.available:
            return "Zomato service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/collections",
                    headers=self._get_headers(),
                    params={
                        "city_id": city_id,
                        "count": min(count, 20),
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to get collections: {resp.status_code}"

                data = resp.json()
                collections = data.get("collections", [])

                if not collections:
                    return "No collections found for this city."

                results = []
                for c in collections:
                    coll = c.get("collection", {})
                    title = coll.get("title", "Unknown")
                    description = coll.get("description", "")
                    res_count = coll.get("res_count", 0)

                    results.append(
                        f"- {title} ({res_count} restaurants)\n"
                        f"  {description}"
                    )

                return "Restaurant Collections:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("zomato_collections_error", error=str(exc))
            return f"Zomato error: {exc}"

    async def search_location(self, query: str) -> str:
        """Search for a location to get city/locality IDs."""
        if not self.available:
            return "Zomato service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/locations",
                    headers=self._get_headers(),
                    params={"query": query},
                )

                if resp.status_code != 200:
                    return f"Failed to search location: {resp.status_code}"

                data = resp.json()
                locations = data.get("location_suggestions", [])

                if not locations:
                    return f"No locations found for '{query}'"

                results = []
                for loc in locations:
                    title = loc.get("title", "Unknown")
                    entity_type = loc.get("entity_type", "Unknown")
                    entity_id = loc.get("entity_id", "Unknown")
                    city_name = loc.get("city_name", "")
                    country_name = loc.get("country_name", "")

                    location_str = ", ".join(filter(None, [city_name, country_name]))

                    results.append(
                        f"- {title} ({entity_type})\n"
                        f"  ID: {entity_id} | {location_str}"
                    )

                return "Locations Found:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("zomato_location_error", error=str(exc))
            return f"Zomato error: {exc}"
