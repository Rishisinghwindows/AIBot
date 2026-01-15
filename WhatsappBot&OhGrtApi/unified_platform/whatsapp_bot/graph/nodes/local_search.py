"""
Local Search Node

Uses Serper Places API for searching local places and businesses.
Supports WhatsApp location sharing for "near me" searches.
Supports multilingual responses (11+ Indian languages).
"""

import logging
import re
from whatsapp_bot.state import BotState
from common.tools.serper_search import search_places
from common.utils.response_formatter import sanitize_error, create_service_error_response
from whatsapp_bot.stores.pending_location_store import get_pending_location_store
from common.whatsapp.client import get_whatsapp_client
from common.i18n.responses import get_local_search_label

logger = logging.getLogger(__name__)

# Intent constant
INTENT = "local_search"

# Response type for location request
RESPONSE_TYPE_LOCATION_REQUEST = "location_request"

def _build_maps_search_link(title: str, address: str = "") -> str:
    """Create a Google Maps search link from place text."""
    import urllib.parse

    query = " ".join(part for part in [title.strip(), address.strip()] if part)
    if not query:
        return ""
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"


def _extract_location_from_query(query: str) -> tuple[str, str]:
    """
    Extract search term and location from query.

    Returns:
        Tuple of (search_term, location)
    """
    query_lower = query.lower()

    # Invalid locations (not actual places)
    invalid_locations = ["me", "here", "my location", "my area", "this area"]

    # Patterns to extract location
    patterns = [
        r"(.+?)\s+(?:in|at|near|around)\s+(.+?)$",
        r"(.+?)\s+(?:in|at|near|around)\s+(.+?)(?:\s+area|\s+city)?$",
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            search_term = match.group(1).strip()
            location = match.group(2).strip()
            # Check if extracted location is valid
            if location not in invalid_locations:
                return search_term, location

    return query, ""


def _has_location_indicator(query: str) -> bool:
    """Check if query has 'near me', 'nearby' etc without actual location."""
    query_lower = query.lower()
    indicators = ["near me", "nearby", "around me", "close to me", "nearest", "near here"]
    return any(ind in query_lower for ind in indicators)


def _extract_search_term(query: str) -> str:
    """Extract the search term from a 'near me' query."""
    query_lower = query.lower()

    # Remove location indicators
    indicators = ["near me", "nearby", "around me", "close to me", "nearest", "near here"]
    result = query_lower
    for ind in indicators:
        result = result.replace(ind, "").strip()

    # Remove common prefixes
    prefixes = ["find", "search", "show", "get", "where is", "where are", "looking for", "i need", "i want"]
    for prefix in prefixes:
        if result.startswith(prefix):
            result = result[len(prefix):].strip()

    return result.strip() or query


async def handle_local_search(state: BotState) -> dict:
    """
    Node function: Handle local search queries.
    Returns response in user's detected language.

    Supports two flows:
    1. Direct search with location (e.g., "restaurants in Delhi")
    2. "Near me" search - asks for WhatsApp location, then searches

    Args:
        state: Current bot state with intent and entities

    Returns:
        Updated state with search results or location request
    """
    entities = state.get("extracted_entities", {})
    whatsapp_message = state.get("whatsapp_message", {})
    phone = whatsapp_message.get("from_number", "")
    location_data = whatsapp_message.get("location")
    message_type = whatsapp_message.get("message_type", "text")
    detected_lang = state.get("detected_language", "en")

    logger.info(f"handle_local_search called: phone={phone}, message_type={message_type}, location_data={location_data}")

    pending_store = get_pending_location_store()

    # Check if user sent a location (responding to our location request)
    if location_data and message_type == "location":
        logger.info(f"Location message received from {phone}, checking for pending search")
        pending = await pending_store.get_pending_search(phone)
        logger.info(f"Pending search result: {pending}")
        if pending:
            # User sent location for a pending "near me" search
            search_query = pending["search_query"]
            lat = location_data.get("latitude")
            lon = location_data.get("longitude")
            address = location_data.get("address") or location_data.get("name") or ""

            logger.info(f"Processing pending search with location: {search_query} at {lat},{lon} (address: {address})")

            # Send acknowledgment message before processing
            try:
                whatsapp_client = get_whatsapp_client()
                message_id = whatsapp_message.get("message_id", "")

                # Send a quick acknowledgment reaction
                if message_id:
                    await whatsapp_client.send_reaction(phone, message_id, "👍")

                # Send processing message
                searching = get_local_search_label("searching", detected_lang, query=search_query)
                await whatsapp_client.send_text_message(
                    to=phone,
                    text=f"🔍 {searching}"
                )
            except Exception as e:
                logger.warning(f"Failed to send acknowledgment: {e}")

            # Use coordinates directly for accurate local search
            return await _execute_search_with_coordinates(
                search_query=search_query,
                latitude=lat,
                longitude=lon,
                address=address,
                lang=detected_lang,
            )

    # Build search query from entities or use original query
    search_query = entities.get("search_query", "")
    location = entities.get("location", "")
    original_query = state.get("current_query", "")

    # Get the full text from whatsapp message as backup
    whatsapp_text = whatsapp_message.get("text", "")

    logger.info(f"local_search: original_query='{original_query}', search_query='{search_query}', location='{location}', whatsapp_text='{whatsapp_text}'")

    # Try to extract location from query if not in entities
    query_to_check = original_query or whatsapp_text
    if not location and query_to_check:
        extracted_query, extracted_location = _extract_location_from_query(query_to_check)
        logger.info(f"local_search: extracted_query='{extracted_query}', extracted_location='{extracted_location}'")
        if extracted_location:
            if extracted_query and (not search_query or search_query == query_to_check):
                search_query = extracted_query
            location = extracted_location

    # Check for "near me" indicators in original query OR whatsapp text
    has_indicator = _has_location_indicator(original_query) or _has_location_indicator(whatsapp_text)
    logger.info(f"local_search: has_location_indicator={has_indicator}, location after extraction='{location}'")

    # Check if user said "near me" but didn't provide location
    if has_indicator and not location:
        # Extract what they're searching for (use search_query from entities if available)
        search_term = search_query or _extract_search_term(query_to_check)

        # Save pending search
        await pending_store.save_pending_search(
            phone=phone,
            search_query=search_term,
            original_message=original_query,
        )

        # Request location from user (localized)
        ask_location = get_local_search_label("ask_location", detected_lang)
        return {
            "response_text": f"📍 *{search_term}*\n\n{ask_location}",
            "response_type": RESPONSE_TYPE_LOCATION_REQUEST,
            "should_fallback": False,
            "intent": INTENT,
        }

    # If we have a search term but no location, ask for location
    if search_query and not location:
        await pending_store.save_pending_search(
            phone=phone,
            search_query=search_query,
            original_message=original_query,
        )

        ask_location = get_local_search_label("ask_location", detected_lang)
        return {
            "response_text": f"📍 *{search_query}*\n\n{ask_location}",
            "response_type": RESPONSE_TYPE_LOCATION_REQUEST,
            "should_fallback": False,
            "intent": INTENT,
        }

    if search_query and location:
        query = f"{search_query} near {location} India"
    elif location:
        query = f"{original_query} {location} India"
    elif search_query:
        query = f"{search_query} India"
    else:
        query = original_query

    if not query:
        local_search_label = get_local_search_label("local_search", detected_lang)
        what_search = get_local_search_label("what_search", detected_lang)
        example = get_local_search_label("example", detected_lang)
        return {
            "response_text": (
                f"*{local_search_label}*\n\n"
                f"{what_search}\n\n"
                f"*{example}:* Hospitals in Dwarka New Delhi"
            ),
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    return await _execute_search(query, search_query or original_query, detected_lang)


async def _execute_search_with_coordinates(
    search_query: str,
    latitude: float,
    longitude: float,
    address: str = "",
    lang: str = "en",
) -> dict:
    """
    Execute search using coordinates for accurate location-based results.

    Args:
        search_query: What to search for (e.g., "hotel", "restaurant")
        latitude: User's latitude
        longitude: User's longitude
        address: Optional address name for display
        lang: Language code for response

    Returns:
        Response dict with search results
    """
    try:
        # Search using coordinates
        result = await search_places(
            query=search_query,
            latitude=latitude,
            longitude=longitude,
        )

        # Get location name from result or use address
        location_name = result.get("data", {}).get("location_name") or address or "your location"

        if result["success"]:
            places = result["data"].get("places", [])

            if places:
                found_places = get_local_search_label("found_places", lang)
                away = get_local_search_label("away", lang)
                reviews_label = get_local_search_label("reviews", lang)
                response_lines = [f"*{search_query.title()}* near {location_name}\n"]
                response_lines.append(f"*{found_places}:*\n")

                for i, place in enumerate(places[:5], 1):
                    title = place.get("title", "Unknown")
                    place_address = place.get("address", "")
                    rating = place.get("rating")
                    reviews = place.get("reviews")
                    phone = place.get("phone")
                    category = place.get("category", "")
                    distance_text = place.get("distance_text", "")
                    maps_link = place.get("maps_link", "")
                    if not maps_link:
                        maps_link = _build_maps_search_link(title, place_address)

                    response_lines.append(f"{i}. *{title}*")
                    if category:
                        response_lines.append(f"   _{category}_")
                    if distance_text:
                        response_lines.append(f"   📏 {distance_text} {away}")
                    if place_address:
                        response_lines.append(f"   📍 {place_address}")
                    if rating:
                        stars = "⭐" * int(rating)
                        review_text = f" ({reviews} {reviews_label})" if reviews else ""
                        response_lines.append(f"   {stars} {rating}{review_text}")
                    if phone:
                        response_lines.append(f"   📞 {phone}")
                    if maps_link:
                        response_lines.append(f"   🗺️ {maps_link}")
                    response_lines.append("")  # Empty line between places

                response_text = "\n".join(response_lines)
            else:
                # Check if radius info is available
                radius_km = result.get("data", {}).get("radius_km", 10)
                no_within = get_local_search_label("no_within_radius", lang, query=search_query, radius=radius_km, location=location_name)
                response_text = f"❌ *{no_within}*"

            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "search")
            local_search = get_local_search_label("local_search", lang)
            try_again = get_local_search_label("try_again", lang)
            return {
                "tool_result": result,
                "response_text": (
                    f"*{local_search}*\n\n"
                    f"{user_message}\n\n"
                    f"{try_again}"
                ),
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Local search with coordinates error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="Local Search",
            raw_error=str(e)
        )


async def _execute_search(query: str, display_query: str, lang: str = "en") -> dict:
    """
    Execute the actual search using Serper Places API.

    Args:
        query: Full search query with location
        display_query: User-friendly query for display
        lang: Language code for response

    Returns:
        Response dict with search results
    """
    try:
        result = await search_places(query)

        if result["success"]:
            places = result["data"].get("places", [])

            if places:
                found_places = get_local_search_label("found_places", lang)
                away = get_local_search_label("away", lang)
                reviews_label = get_local_search_label("reviews", lang)
                response_lines = [f"*{display_query}*\n"]
                response_lines.append(f"*{found_places}:*\n")

                for i, place in enumerate(places[:5], 1):
                    title = place.get("title", "Unknown")
                    address = place.get("address", "")
                    rating = place.get("rating")
                    reviews = place.get("reviews")
                    phone = place.get("phone")
                    category = place.get("category", "")
                    distance_text = place.get("distance_text", "")
                    maps_link = place.get("maps_link", "")
                    if not maps_link:
                        maps_link = _build_maps_search_link(title, address)

                    response_lines.append(f"{i}. *{title}*")
                    if category:
                        response_lines.append(f"   _{category}_")
                    if distance_text:
                        response_lines.append(f"   📏 {distance_text} {away}")
                    if address:
                        response_lines.append(f"   📍 {address}")
                    if rating:
                        stars = "⭐" * int(rating)
                        review_text = f" ({reviews} {reviews_label})" if reviews else ""
                        response_lines.append(f"   {stars} {rating}{review_text}")
                    if phone:
                        response_lines.append(f"   📞 {phone}")
                    if maps_link:
                        response_lines.append(f"   🗺️ {maps_link}")
                    response_lines.append("")  # Empty line between places

                response_text = "\n".join(response_lines)
            else:
                no_places = get_local_search_label("no_places_for", lang, query=display_query)
                response_text = no_places

            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }
        else:
            raw_error = result.get("error", "")
            user_message = sanitize_error(raw_error, "search")
            local_search = get_local_search_label("local_search", lang)
            try_again = get_local_search_label("try_again", lang)
            response_text = (
                f"*{local_search}*\n\n"
                f"{user_message}\n\n"
                f"{try_again}"
            )
            return {
                "tool_result": result,
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

    except Exception as e:
        logger.error(f"Local search handler error: {e}")
        return create_service_error_response(
            intent=INTENT,
            feature_name="Local Search",
            raw_error=str(e)
        )
