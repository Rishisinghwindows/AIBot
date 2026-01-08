"""
Event Node Handler

Handles event-related queries: IPL matches, concerts, comedy shows, and general events.
"""

import logging
import re
import httpx
from typing import Optional
from common.graph.state import BotState
from common.tools.event_tool import EventService
from whatsapp_bot.stores.pending_location_store import get_pending_location_store

logger = logging.getLogger(__name__)

INTENT = "events"

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


def _format_events_response(events: list, event_type: str = "events") -> str:
    """Format events list for WhatsApp response."""
    if not events:
        return f"No {event_type} found matching your criteria. Try a different search or check back later!"

    response = f"🎫 *Found {len(events)} {event_type}:*\n\n"

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
                response += f" at {time}"
            response += "\n"
        if price:
            response += f"💰 {price}\n"
        response += "\n"

    if len(events) > 5:
        response += f"_...and {len(events) - 5} more events_\n"

    response += "\n📱 Reply with the event number for more details!"
    return response


def _format_ipl_response(matches: list) -> str:
    """Format IPL matches for WhatsApp response."""
    if not matches:
        return "No IPL matches found. The season might not have started yet or no matches available for your criteria."

    response = "🏏 *IPL 2025 Matches:*\n\n"

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
                response += f" at {time}"
            response += "\n"
        if price:
            response += f"💰 {price}\n"
        response += "\n"

    if len(matches) > 5:
        response += f"_...and {len(matches) - 5} more matches_\n"

    response += "\n🎟️ Reply with match number for ticket details!"
    return response


def _format_concert_response(concerts: list) -> str:
    """Format concerts for WhatsApp response."""
    if not concerts:
        return "No concerts found matching your criteria. Check back later for new events!"

    response = "🎵 *Upcoming Concerts:*\n\n"

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
        response += f"_...and {len(concerts) - 5} more concerts_\n"

    return response


def _format_comedy_response(shows: list) -> str:
    """Format comedy shows for WhatsApp response."""
    if not shows:
        return "No comedy shows found matching your criteria. Check back later!"

    response = "😂 *Upcoming Comedy Shows:*\n\n"

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
        response += f"_...and {len(shows) - 5} more shows_\n"

    return response


async def handle_events(state: BotState) -> dict:
    """
    Handle event-related queries.

    Supports:
    - IPL matches (cricket)
    - Concerts
    - Comedy shows
    - General event search

    Args:
        state: Current bot state

    Returns:
        Updated state with event information
    """
    query = state.get("current_query", "").lower()

    try:
        service = get_event_service()

        # Extract filters from query
        city = _extract_city(query)
        team = _extract_team(query)
        artist = _extract_artist(query)
        comedian = _extract_comedian(query)

        # Determine query type and fetch events
        if any(kw in query for kw in ["ipl", "cricket", "match", "rcb", "csk", "mi", "kkr", "dc", "srh", "rr", "pbks", "gt", "lsg"]):
            # IPL/Cricket matches
            matches = await service.get_ipl_matches(team=team, city=city, limit=10)
            response_text = _format_ipl_response(matches)

        elif any(kw in query for kw in ["concert", "music", "live", "singer"]) or artist:
            # Concerts
            concerts = await service.get_concerts(artist=artist, city=city, limit=10)
            response_text = _format_concert_response(concerts)

        elif any(kw in query for kw in ["comedy", "standup", "stand-up", "comedian", "funny"]) or comedian:
            # Comedy shows
            shows = await service.get_comedy_shows(comedian=comedian, city=city, limit=10)
            response_text = _format_comedy_response(shows)

        elif any(kw in query for kw in ["football", "isl", "soccer"]):
            # Football matches
            matches = await service.get_football_matches(city=city, limit=10)
            response_text = _format_events_response(matches, "football matches")

        else:
            # General event search
            events = await service.get_upcoming_events(city=city, limit=10)
            response_text = _format_events_response(events)

        return {
            "response_text": response_text,
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
        }

    except Exception as e:
        logger.error(f"Error in handle_events: {e}")
        return {
            "response_text": "Sorry, I couldn't fetch event information right now. Please try again later.",
            "response_type": "text",
            "should_fallback": False,
            "intent": INTENT,
            "error": str(e),
        }
