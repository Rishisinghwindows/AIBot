"""
Event Node Handler

Handles event-related queries: IPL matches, concerts, comedy shows, and general events.
Supports location-based event search using GPS coordinates.
Supports multilingual responses (11+ Indian languages).
"""

import logging
import re
import httpx
from typing import Optional
from whatsapp_bot.state import BotState
from common.tools.event_tool import EventService
from whatsapp_bot.stores.pending_location_store import get_pending_location_store
from common.i18n.responses import get_event_label, get_phrase

logger = logging.getLogger(__name__)

INTENT = "events"
RESPONSE_TYPE_LOCATION_REQUEST = "location_request"


def _has_location_indicator(query: str) -> bool:
    """Check if query has 'near me', 'nearby' etc without actual location."""
    query_lower = query.lower()
    indicators = ["near me", "nearby", "around me", "close to me", "nearest", "near here"]
    return any(ind in query_lower for ind in indicators)


def _extract_year(query: str) -> Optional[int]:
    """Extract a 4-digit year from the query."""
    match = re.search(r"\b(20\d{2})\b", query)
    return int(match.group(1)) if match else None


# Singleton event service instance
_event_service: Optional[EventService] = None


def get_event_service() -> EventService:
    """Get or create singleton EventService instance."""
    global _event_service
    if _event_service is None:
        _event_service = EventService()
    return _event_service


def _extract_city(query: str) -> Optional[str]:
    """Extract city name from query."""
    # Map common variations to official names used in seed data
    city_aliases = {
        "bangalore": "Bengaluru",
        "bombay": "Mumbai",
        "madras": "Chennai",
        "calcutta": "Kolkata",
        "trivandrum": "Thiruvananthapuram",
        "cochin": "Kochi",
    }

    cities = [
        "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "kolkata",
        "hyderabad", "pune", "ahmedabad", "jaipur", "lucknow", "kanpur",
        "nagpur", "indore", "bhopal", "visakhapatnam", "patna", "vadodara",
        "ghaziabad", "ludhiana", "agra", "nashik", "faridabad", "meerut",
        "rajkot", "varanasi", "srinagar", "aurangabad", "dhanbad", "amritsar",
        "navi mumbai", "allahabad", "ranchi", "howrah", "coimbatore", "jabalpur",
        "gwalior", "vijayawada", "jodhpur", "madurai", "raipur", "kota",
        "guwahati", "chandigarh", "solapur", "hubli", "mysore", "tiruchirappalli",
        "bareilly", "aligarh", "tiruppur", "moradabad", "jalandhar", "bhubaneswar",
        "salem", "warangal", "guntur", "bhiwandi", "saharanpur", "gorakhpur",
        "bikaner", "amravati", "noida", "jamshedpur", "bhilai", "cuttack",
        "firozabad", "kochi", "cochin", "thiruvananthapuram", "trivandrum",
        "mohali", "dharamsala", "goa",
    ]
    query_lower = query.lower()
    for city in cities:
        if city in query_lower:
            # Return mapped alias if exists, otherwise title case
            return city_aliases.get(city, city.title())
    return None


def _extract_team(query: str) -> Optional[str]:
    """Extract IPL team from query."""
    team_patterns = {
        "rcb": ["rcb", "royal challengers", "bangalore", "bengaluru"],
        "csk": ["csk", "chennai super kings", "chennai", "dhoni"],
        "mi": ["mi", "mumbai indians", "mumbai"],
        "kkr": ["kkr", "kolkata knight riders", "kolkata", "knight riders"],
        "dc": ["dc", "delhi capitals", "delhi"],
        "pbks": ["pbks", "punjab kings", "punjab"],
        "rr": ["rr", "rajasthan royals", "rajasthan"],
        "srh": ["srh", "sunrisers", "hyderabad"],
        "gt": ["gt", "gujarat titans", "gujarat"],
        "lsg": ["lsg", "lucknow super giants", "lucknow"],
    }
    query_lower = query.lower()
    for team_code, patterns in team_patterns.items():
        for pattern in patterns:
            if pattern in query_lower:
                return team_code.upper()
    return None


def _extract_artist(query: str) -> Optional[str]:
    """Extract artist name from query."""
    artists = [
        "arijit singh", "arijit", "ar rahman", "a r rahman", "rahman",
        "coldplay", "diljit", "diljit dosanjh", "badshah", "honey singh",
        "neha kakkar", "shreya ghoshal", "sonu nigam", "sunidhi chauhan",
        "atif aslam", "kk", "mohit chauhan", "pritam", "vishal shekhar",
    ]
    query_lower = query.lower()
    for artist in artists:
        if artist in query_lower:
            return artist.title()
    return None


def _extract_comedian(query: str) -> Optional[str]:
    """Extract comedian name from query."""
    comedians = [
        "zakir khan", "zakir", "biswa", "biswa kalyan rath", "kenny sebastian",
        "kenny", "kanan gill", "kanan", "abhishek upmanyu", "upmanyu",
        "comicstaan", "anubhav bassi", "bassi", "rahul subramanian",
        "aakash gupta", "samay raina", "tanmay bhat", "tanmay",
    ]
    query_lower = query.lower()
    for comedian in comedians:
        if comedian in query_lower:
            return comedian.title()
    return None


def _format_events_response(events: list, event_type: str = "events", lang: str = "en") -> str:
    """Format events list for WhatsApp response."""
    if not events:
        return get_event_label("not_found", lang)

    found_label = get_event_label("found", lang, count=len(events))
    at_label = get_event_label("at", lang)
    response = f"🎫 *{found_label}:*\n\n"

    for i, event in enumerate(events[:5], 1):
        name = event.get("name", "Unknown Event")
        venue = event.get("venue_name", "")
        city = event.get("city", "")
        date = event.get("formatted_date", event.get("date", ""))
        time = event.get("time", "")
        price = event.get("formatted_price", "")

        response += f"*{i}. {name}*\n"
        if venue:
            response += f"📍 {venue}"
            if city:
                response += f", {city}"
            response += "\n"
        if date:
            response += f"📅 {date}"
            if time:
                response += f" {at_label} {time}"
            response += "\n"
        if price:
            response += f"💰 {price}\n"
        response += "\n"

    if len(events) > 5:
        and_more = get_event_label("and_more", lang, count=len(events) - 5)
        response += f"_{and_more}_\n"

    more_details = get_event_label("more_details", lang)
    response += f"\n📱 {more_details}"
    return response


def _format_ipl_response(matches: list, lang: str = "en") -> str:
    """Format IPL matches for WhatsApp response."""
    if not matches:
        return get_event_label("no_ipl", lang)

    ipl_title = get_event_label("ipl_title", lang)
    at_label = get_event_label("at", lang)
    response = f"🏏 *{ipl_title}:*\n\n"

    for i, match in enumerate(matches[:5], 1):
        home = match.get("home_team", {})
        away = match.get("away_team", {})
        venue = match.get("venue_name", "")
        city = match.get("city", "")
        date = match.get("formatted_date", "")
        time = match.get("time", "")
        price = match.get("formatted_price", "")

        home_name = home.get("name", home.get("code", "TBD"))
        away_name = away.get("name", away.get("code", "TBD"))

        response += f"*{i}. {home_name} vs {away_name}*\n"
        if venue:
            response += f"📍 {venue}"
            if city:
                response += f", {city}"
            response += "\n"
        if date:
            response += f"📅 {date}"
            if time:
                response += f" {at_label} {time}"
            response += "\n"
        if price:
            response += f"💰 {price}\n"
        response += "\n"

    if len(matches) > 5:
        and_more = get_event_label("and_more", lang, count=len(matches) - 5)
        response += f"_{and_more}_\n"

    ticket_details = get_event_label("ticket_details", lang)
    response += f"\n🎟️ {ticket_details}"
    return response


def _format_concert_response(concerts: list, lang: str = "en") -> str:
    """Format concerts for WhatsApp response."""
    if not concerts:
        return get_event_label("no_concerts", lang)

    concerts_title = get_event_label("concerts_title", lang)
    response = f"🎵 *{concerts_title}:*\n\n"

    for i, concert in enumerate(concerts[:5], 1):
        name = concert.get("name", "")
        artist = concert.get("artist", "")
        venue = concert.get("venue_name", "")
        city = concert.get("city", "")
        date = concert.get("formatted_date", "")
        price = concert.get("formatted_price", "")

        response += f"*{i}. {name}*\n"
        if artist:
            response += f"🎤 {artist}\n"
        if venue:
            response += f"📍 {venue}"
            if city:
                response += f", {city}"
            response += "\n"
        if date:
            response += f"📅 {date}\n"
        if price:
            response += f"💰 {price}\n"
        response += "\n"

    if len(concerts) > 5:
        and_more = get_event_label("and_more", lang, count=len(concerts) - 5)
        response += f"_{and_more}_\n"

    return response


def _format_comedy_response(shows: list, lang: str = "en") -> str:
    """Format comedy shows for WhatsApp response."""
    if not shows:
        return get_event_label("no_comedy", lang)

    comedy_title = get_event_label("comedy_title", lang)
    response = f"😂 *{comedy_title}:*\n\n"

    for i, show in enumerate(shows[:5], 1):
        name = show.get("name", "")
        artist = show.get("artist", "")
        venue = show.get("venue_name", "")
        city = show.get("city", "")
        date = show.get("formatted_date", "")
        price = show.get("formatted_price", "")

        response += f"*{i}. {name}*\n"
        if artist:
            response += f"🎭 {artist}\n"
        if venue:
            response += f"📍 {venue}"
            if city:
                response += f", {city}"
            response += "\n"
        if date:
            response += f"📅 {date}\n"
        if price:
            response += f"💰 {price}\n"
        response += "\n"

    if len(shows) > 5:
        and_more = get_event_label("and_more", lang, count=len(shows) - 5)
        response += f"_{and_more}_\n"

    return response


async def handle_events(state: BotState) -> dict:
    """
    Handle event-related queries.
    Returns response in user's detected language.

    Supports:
    - IPL matches (cricket)
    - Concerts
    - Comedy shows
    - Football/ISL matches
    - General event search
    - Location-based event search (nearby events)

    Args:
        state: Current bot state

    Returns:
        Updated state with event information
    """
    query = state.get("current_query", "").lower()
    whatsapp_message = state.get("whatsapp_message", {})
    phone = whatsapp_message.get("from_number", "")
    location_data = whatsapp_message.get("location")
    message_type = whatsapp_message.get("message_type", "text")
    detected_lang = state.get("detected_language", "en")

    try:
        # Avoid returning stale IPL data when user requests a different year.
        requested_year = _extract_year(query)
        if requested_year and "ipl" in query and requested_year != 2025:
            response_text = get_event_label("ipl_future_unavailable", detected_lang, year=requested_year)
            return {
                "response_text": response_text,
                "response_type": "text",
                "should_fallback": False,
                "intent": INTENT,
            }

        service = get_event_service()
        pending_store = get_pending_location_store()

        # Check if this is a location message for pending event search
        if location_data and message_type == "location":
            pending = await pending_store.get_pending_search(phone)
            if pending and pending.get("search_query", "").startswith("__events"):
                # User sent location for event search
                lat = location_data.get("latitude")
                lon = location_data.get("longitude")

                logger.info(f"Processing event search with location: {lat},{lon}")

                # Get nearby events
                result = await service.get_nearby_events(
                    latitude=lat,
                    longitude=lon,
                    limit=10
                )

                city = result.get("city", "your location")
                events = result.get("events", [])

                if events:
                    events_near = get_event_label("events_near", detected_lang, city=city)
                    response_text = f"🎫 *{events_near}:*\n\n"
                    response_text += _format_events_response(events, f"events in {city}", detected_lang).split("\n\n", 1)[-1]
                else:
                    response_text = get_event_label("no_events_near", detected_lang, city=city)

                # Clear pending search
                await pending_store.clear_pending_search(phone)

                return {
                    "response_text": response_text,
                    "response_type": "text",
                    "should_fallback": False,
                    "intent": INTENT,
                }

        # Extract filters from query
        city = _extract_city(query)
        team = _extract_team(query)
        artist = _extract_artist(query)
        comedian = _extract_comedian(query)

        # Check if user wants events "near me" without specifying city
        if _has_location_indicator(query) and not city:
            # Determine event type for better message
            event_type = "events"
            if any(kw in query for kw in ["ipl", "cricket", "match"]):
                event_type = "IPL matches"
            elif any(kw in query for kw in ["concert", "music", "live"]):
                event_type = "concerts"
            elif any(kw in query for kw in ["comedy", "standup"]):
                event_type = "comedy shows"
            elif any(kw in query for kw in ["football", "isl"]):
                event_type = "football matches"

            # Save pending search
            await pending_store.save_pending_search(
                phone=phone,
                search_query=f"__events_{event_type}",
                original_message=query,
            )

            logger.info(f"Requesting location for events search: {event_type}")

            # Localized location request
            ask_location = get_event_label("ask_location", detected_lang)
            return {
                "response_text": f"🎫 *{event_type}*\n\n{ask_location}",
                "response_type": RESPONSE_TYPE_LOCATION_REQUEST,
                "should_fallback": False,
                "intent": INTENT,
            }

        # Determine query type and fetch events
        if any(kw in query for kw in ["ipl", "cricket", "match", "rcb", "csk", "mi", "kkr", "dc", "srh", "rr", "pbks", "gt", "lsg"]):
            # IPL/Cricket matches
            matches = await service.get_ipl_matches(team=team, city=city, limit=10)
            response_text = _format_ipl_response(matches, detected_lang)

        elif any(kw in query for kw in ["concert", "music", "live", "singer"]) or artist:
            # Concerts
            concerts = await service.get_concerts(artist=artist, city=city, limit=10)
            response_text = _format_concert_response(concerts, detected_lang)

        elif any(kw in query for kw in ["comedy", "standup", "stand-up", "comedian", "funny"]) or comedian:
            # Comedy shows
            shows = await service.get_comedy_shows(comedian=comedian, city=city, limit=10)
            response_text = _format_comedy_response(shows, detected_lang)

        elif any(kw in query for kw in ["football", "isl", "soccer"]):
            # Football matches
            football_label = get_event_label("football_matches", detected_lang)
            matches = await service.get_football_matches(city=city, limit=10)
            response_text = _format_events_response(matches, football_label, detected_lang)

        else:
            # General event search
            events = await service.get_upcoming_events(city=city, limit=10)
            response_text = _format_events_response(events, "events", detected_lang)

            # If no city specified and no events found, suggest popular cities
            if not city and not events:
                looking_for = get_event_label("looking_for_events", detected_lang)
                tell_me = get_event_label("tell_me", detected_lang)
                ipl_title = get_event_label("ipl_title", detected_lang)
                concerts_title = get_event_label("concerts_title", detected_lang)
                comedy_title = get_event_label("comedy_title", detected_lang)
                football_label = get_event_label("football_matches", detected_lang)
                search_by_city = get_event_label("search_by_city", detected_lang)
                response_text = (
                    f"🎫 *{looking_for}*\n\n"
                    f"{tell_me}\n\n"
                    f"🏏 *{ipl_title}:* _\"Show RCB matches\"_\n"
                    f"🎵 *{concerts_title}:* _\"Coldplay concert in Mumbai\"_\n"
                    f"😂 *{comedy_title}:* _\"Zakir Khan shows\"_\n"
                    f"⚽ *{football_label}:* _\"ISL matches in Bengaluru\"_\n\n"
                    f"{search_by_city}\n"
                    "• _Events in Mumbai_\n"
                    "• _Events in Delhi_\n"
                    "• _Events in Bengaluru_"
                )

        return {
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Error in handle_events: {e}", exc_info=True)
        error_msg = get_phrase("error_occurred", detected_lang)
        return {
            "response_text": error_msg,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
