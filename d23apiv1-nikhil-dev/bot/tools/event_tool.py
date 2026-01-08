"""
Event Service
=============

Service for managing events, venues, and ticket categories.
Uses real seed data gathered from TicketGenie, IPL, and entertainment sources.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import logging

from bot.data.seed_data import (
    VENUES,
    IPL_TEAMS,
    TEAM_TICKET_CATEGORIES,
    CONCERTS,
    COMEDY_SHOWS,
    generate_ipl_matches,
    get_venue_by_id,
    get_team_info,
    get_all_events,
    get_events_by_category,
    get_events_by_city,
    get_featured_events,
    search_events as seed_search_events,
    get_city_from_coordinates,
)

logger = logging.getLogger(__name__)


class EventService:
    """
    Service for event operations.

    Uses real seed data from TicketGenie, IPL, and entertainment events.
    Will be replaced with real TicketGenie API integration later.
    """

    def __init__(self):
        # Load all events from seed data
        self._all_events = get_all_events()
        self._events_by_id = {e["id"]: e for e in self._all_events}
        self._venues = {v["id"]: v for v in VENUES}
        self._ipl_teams = IPL_TEAMS

        logger.info(
            "event_service_initialized",
            total_events=len(self._all_events),
            total_venues=len(self._venues),
            total_teams=len(self._ipl_teams),
        )

    async def get_upcoming_events(
        self,
        city: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get upcoming events with optional filters."""
        logger.debug(
            "get_upcoming_events_called",
            city=city,
            category=category,
            limit=limit,
        )

        events = self._all_events.copy()
        original_count = len(events)

        # Filter by city
        if city:
            city_lower = city.lower()
            events = [e for e in events if city_lower in e.get("city", "").lower()]
            logger.debug("filtered_by_city", city=city, remaining=len(events))

        # Filter by category
        if category:
            cat_lower = category.lower()
            events = [e for e in events if cat_lower in e.get("category", "").lower()
                     or cat_lower in e.get("sub_category", "").lower()]
            logger.debug("filtered_by_category", category=category, remaining=len(events))

        # Sort by date
        events.sort(key=lambda x: x.get("date", ""))

        # Format for response
        formatted = self._format_events(events[:limit])

        logger.info(
            "get_upcoming_events_result",
            original_count=original_count,
            filtered_count=len(events),
            returned_count=len(formatted),
        )
        return formatted

    async def search_events(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
        team: Optional[str] = None,
        artist: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search events with multiple criteria."""
        events = self._all_events.copy()

        # Text search
        if query:
            query_lower = query.lower()
            events = [
                e for e in events
                if query_lower in str(e.get("name", "")).lower()
                or query_lower in str(e.get("artist", "")).lower()
                or query_lower in str(e.get("city", "")).lower()
                or query_lower in str(e.get("venue_name", "")).lower()
                or query_lower in str(e.get("home_team_name", "")).lower()
                or query_lower in str(e.get("away_team_name", "")).lower()
            ]

        # City filter
        if city:
            city_lower = city.lower()
            events = [e for e in events if city_lower in e.get("city", "").lower()]

        # Date filters
        if date_from:
            events = [e for e in events if e.get("date", "") >= date_from]
        if date_to:
            events = [e for e in events if e.get("date", "") <= date_to]

        # Category filter
        if category:
            cat_lower = category.lower()
            events = [e for e in events if cat_lower in e.get("category", "").lower()]

        # Team filter (for IPL)
        if team:
            team_lower = team.lower()
            team_code = self._get_team_code(team_lower)
            events = [
                e for e in events
                if team_code in [e.get("home_team", ""), e.get("away_team", "")]
                or team_lower in (e.get("home_team_name", "") + e.get("away_team_name", "")).lower()
            ]

        # Artist filter
        if artist:
            artist_lower = artist.lower()
            events = [e for e in events if artist_lower in e.get("artist", "").lower()]

        events.sort(key=lambda x: x.get("date", ""))
        return self._format_events(events[:limit])

    async def get_event_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed event information."""
        logger.debug("get_event_details_called", event_id=event_id)

        event = self._events_by_id.get(event_id)
        if not event:
            logger.warning("event_not_found", event_id=event_id)
            return None

        # Enrich with venue details
        venue_id = event.get("venue_id")
        venue = self._venues.get(venue_id) if venue_id else None

        logger.info(
            "event_details_retrieved",
            event_id=event_id,
            event_name=event.get("name"),
            category=event.get("category"),
            has_venue=bool(venue),
        )

        return {
            **event,
            "venue_details": venue,
            "venue_city": event.get("city", ""),  # Alias for compatibility
            "formatted_date": self._format_date(event.get("date", "")),
            "formatted_time": event.get("time", ""),
            "booking_url": self._generate_booking_url(event),
        }

    async def get_ipl_matches(
        self,
        team: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get IPL matches with optional team filter."""
        logger.debug("get_ipl_matches_called", team=team, city=city, limit=limit)

        # Get only IPL matches
        events = [e for e in self._all_events if e.get("category") == "cricket" and "IPL" in e.get("tournament", "")]
        total_ipl = len(events)

        if team:
            team_code = self._get_team_code(team.lower())
            events = [
                e for e in events
                if team_code in [e.get("home_team", ""), e.get("away_team", "")]
            ]
            logger.debug("filtered_by_team", team=team, team_code=team_code, remaining=len(events))

        if city:
            city_lower = city.lower()
            events = [e for e in events if city_lower in e.get("city", "").lower()]
            logger.debug("filtered_by_city", city=city, remaining=len(events))

        events.sort(key=lambda x: x.get("date", ""))
        formatted = self._format_ipl_matches(events[:limit])

        logger.info(
            "get_ipl_matches_result",
            total_ipl_matches=total_ipl,
            filtered_count=len(events),
            returned_count=len(formatted),
        )
        return formatted

    async def get_concerts(
        self,
        artist: Optional[str] = None,
        city: Optional[str] = None,
        genre: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get concerts with optional filters."""
        events = [e for e in self._all_events if e.get("category") == "concert"]

        if artist:
            artist_lower = artist.lower()
            events = [e for e in events if artist_lower in e.get("artist", "").lower()]

        if city:
            city_lower = city.lower()
            events = [e for e in events if city_lower in e.get("city", "").lower()]

        if genre:
            genre_lower = genre.lower()
            events = [e for e in events if genre_lower in e.get("genre", "").lower()]

        events.sort(key=lambda x: x.get("date", ""))
        return self._format_events(events[:limit])

    async def get_comedy_shows(
        self,
        comedian: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get comedy shows with optional filters."""
        events = [e for e in self._all_events if e.get("category") == "comedy"]

        if comedian:
            comedian_lower = comedian.lower()
            events = [e for e in events if comedian_lower in e.get("artist", "").lower()]

        if city:
            city_lower = city.lower()
            events = [e for e in events if city_lower in e.get("city", "").lower()]

        events.sort(key=lambda x: x.get("date", ""))
        return self._format_events(events[:limit])

    async def get_nearby_events(
        self,
        latitude: float,
        longitude: float,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get events near a GPS location.

        Returns events in the nearest city based on coordinates.
        """
        logger.debug(
            "get_nearby_events_called",
            latitude=latitude,
            longitude=longitude,
            category=category,
            limit=limit,
        )

        # Find nearest city from coordinates
        nearest_city = get_city_from_coordinates(latitude, longitude)

        logger.info(
            "nearest_city_detected",
            latitude=latitude,
            longitude=longitude,
            detected_city=nearest_city,
        )

        # Get events for that city
        events = self._all_events.copy()
        city_lower = nearest_city.lower()
        events = [e for e in events if city_lower in e.get("city", "").lower()]

        # Filter by category if specified
        if category:
            cat_lower = category.lower()
            events = [e for e in events if cat_lower in e.get("category", "").lower()
                     or cat_lower in e.get("sub_category", "").lower()]

        events.sort(key=lambda x: x.get("date", ""))
        formatted = self._format_events(events[:limit])

        logger.info(
            "get_nearby_events_result",
            detected_city=nearest_city,
            event_count=len(formatted),
        )

        return {
            "city": nearest_city,
            "events": formatted,
        }

    async def get_events_by_type(
        self,
        event_type: str,
        city: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get events by specific type (theatre, movies, workshops, etc.)."""
        logger.debug(
            "get_events_by_type_called",
            event_type=event_type,
            city=city,
            limit=limit,
        )

        type_lower = event_type.lower()
        events = [e for e in self._all_events
                  if type_lower in e.get("category", "").lower()
                  or type_lower in e.get("sub_category", "").lower()]

        if city:
            city_lower = city.lower()
            events = [e for e in events if city_lower in e.get("city", "").lower()]

        events.sort(key=lambda x: x.get("date", ""))
        formatted = self._format_events(events[:limit])

        logger.info(
            "get_events_by_type_result",
            event_type=event_type,
            city=city,
            event_count=len(formatted),
        )
        return formatted

    async def get_football_matches(
        self,
        team: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get ISL football matches with optional filters."""
        logger.debug("get_football_matches_called", team=team, city=city, limit=limit)

        # Get only football matches
        events = [e for e in self._all_events if e.get("category") == "football"]
        total_football = len(events)

        if team:
            team_lower = team.lower()
            team_code = self._get_football_team_code(team_lower)
            events = [
                e for e in events
                if team_code in [e.get("home_team", ""), e.get("away_team", "")]
                or team_lower in (e.get("home_team_name", "") + e.get("away_team_name", "")).lower()
            ]
            logger.debug("filtered_by_team", team=team, team_code=team_code, remaining=len(events))

        if city:
            city_lower = city.lower()
            events = [e for e in events if city_lower in e.get("city", "").lower()]
            logger.debug("filtered_by_city", city=city, remaining=len(events))

        events.sort(key=lambda x: x.get("date", ""))
        formatted = self._format_football_matches(events[:limit])

        logger.info(
            "get_football_matches_result",
            total_football_matches=total_football,
            filtered_count=len(events),
            returned_count=len(formatted),
        )
        return formatted

    def _get_football_team_code(self, team_name: str) -> str:
        """Map football team name to standard code."""
        team_map = {
            "mumbai city": "MCFC",
            "mumbai city fc": "MCFC",
            "mcfc": "MCFC",
            "bengaluru fc": "BFC",
            "bengaluru": "BFC",
            "bfc": "BFC",
            "kerala blasters": "KBFC",
            "kerala": "KBFC",
            "kbfc": "KBFC",
            "atk mohun bagan": "ATKMB",
            "mohun bagan": "ATKMB",
            "atkmb": "ATKMB",
            "east bengal": "EBFC",
            "ebfc": "EBFC",
            "chennaiyin": "CFC",
            "chennaiyin fc": "CFC",
            "cfc": "CFC",
            "fc goa": "FCG",
            "goa": "FCG",
            "fcg": "FCG",
            "jamshedpur": "JFC",
            "jamshedpur fc": "JFC",
            "jfc": "JFC",
        }
        return team_map.get(team_name.lower(), team_name.upper())

    def _format_football_matches(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Format football matches for API response."""
        formatted = []
        for event in events:
            categories = event.get("ticket_categories", [])
            min_price = min((c.get("price", 0) for c in categories), default=0)
            max_price = max((c.get("max_price", c.get("price", 0)) for c in categories), default=0)

            formatted.append({
                "id": event.get("id"),
                "name": event.get("name"),
                "full_name": event.get("full_name", ""),
                "match_number": event.get("match_number"),
                "tournament": event.get("tournament", "ISL 2024-25"),
                "home_team": {
                    "code": event.get("home_team"),
                    "name": event.get("home_team_name", ""),
                    "logo": event.get("home_team_logo", ""),
                },
                "away_team": {
                    "code": event.get("away_team"),
                    "name": event.get("away_team_name", ""),
                    "logo": event.get("away_team_logo", ""),
                },
                "venue_name": event.get("venue_name", ""),
                "city": event.get("city", ""),
                "venue_city": event.get("city", ""),
                "date": event.get("date", ""),
                "time": event.get("time", ""),
                "formatted_date": self._format_date(event.get("date", "")),
                "status": event.get("status", "upcoming"),
                "image_url": event.get("image_url", ""),
                "min_price": min_price,
                "max_price": max_price,
                "formatted_price": f"₹{min_price:,}" + (f" - ₹{max_price:,}" if max_price > min_price else ""),
                "ticketing_partner": event.get("ticketing_partner", "BookMyShow"),
                "booking_url": self._generate_booking_url(event),
            })

        return formatted

    async def get_ticket_categories(self, event_id: str) -> List[Dict[str, Any]]:
        """Get ticket categories for an event."""
        logger.debug("get_ticket_categories_called", event_id=event_id)

        event = self._events_by_id.get(event_id)
        if not event:
            logger.warning("event_not_found_for_categories", event_id=event_id)
            return []

        categories = event.get("ticket_categories", [])

        # Format categories with availability
        formatted = []
        for cat in categories:
            formatted.append({
                "id": cat.get("id"),
                "name": cat.get("name"),
                "description": cat.get("description", ""),
                "price": cat.get("price"),
                "max_price": cat.get("max_price", cat.get("price")),
                "formatted_price": f"₹{cat.get('price'):,}",
                "available_seats": cat.get("available_seats", 0),
                "is_available": cat.get("available_seats", 0) > 0,
                "benefits": cat.get("benefits", []),
                "max_per_booking": cat.get("max_per_booking", 10),
            })

        logger.info(
            "ticket_categories_retrieved",
            event_id=event_id,
            category_count=len(formatted),
            price_range=f"₹{min(c['price'] for c in formatted):,} - ₹{max(c['price'] for c in formatted):,}" if formatted else "N/A",
        )
        return formatted

    async def get_category_details(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category details by ID."""
        for event in self._all_events:
            for cat in event.get("ticket_categories", []):
                if cat.get("id") == category_id:
                    return {
                        **cat,
                        "event_id": event.get("id"),
                        "event_name": event.get("name"),
                    }
        return None

    async def check_availability(
        self,
        category_id: str,
        quantity: int,
    ) -> bool:
        """Check if requested quantity is available."""
        category = await self.get_category_details(category_id)
        if not category:
            return False
        return category.get("available_seats", 0) >= quantity

    async def get_venues(self, city: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all venues with optional city filter."""
        venues = list(self._venues.values())

        if city:
            city_lower = city.lower()
            venues = [v for v in venues if city_lower in v.get("city", "").lower()]

        return venues

    async def get_venue_details(self, venue_id: str) -> Optional[Dict[str, Any]]:
        """Get venue details by ID."""
        return self._venues.get(venue_id)

    async def get_ipl_teams(self) -> List[Dict[str, Any]]:
        """Get all IPL teams."""
        return [
            {
                "code": code,
                **info
            }
            for code, info in self._ipl_teams.items()
        ]

    async def get_team_details(self, team_code: str) -> Optional[Dict[str, Any]]:
        """Get IPL team details."""
        team_code = team_code.upper()
        team = self._ipl_teams.get(team_code)
        if not team:
            return None

        # Get home venue
        venue = self._venues.get(team.get("home_venue_id"))

        return {
            "code": team_code,
            **team,
            "home_venue": venue,
        }

    async def get_featured_events(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Get featured/highlighted events."""
        events = [e for e in self._all_events if e.get("is_featured")]
        events.sort(key=lambda x: x.get("date", ""))
        return self._format_events(events[:limit])

    # === Helper Methods ===

    def _generate_booking_url(self, event: Dict) -> str:
        """Generate booking URL based on ticketing partner."""
        partner = event.get("ticketing_partner", "TicketGenie").lower()
        event_id = event.get("id", "")
        event_name = event.get("name", "").lower().replace(" ", "-").replace("'", "")[:50]

        # Partner-specific URLs
        partner_urls = {
            "bookmyshow": f"https://in.bookmyshow.com/events/{event_name}",
            "paytm insider": f"https://insider.in/event/{event_name}",
            "insider": f"https://insider.in/event/{event_name}",
            "ticketgenie": f"https://ticketgenie.in/events/{event_id}",
        }

        return partner_urls.get(partner, f"https://ticketgenie.in/events/{event_id}")

    def _get_team_code(self, team_name: str) -> str:
        """Map team name/abbreviation to standard code."""
        team_map = {
            "rcb": "RCB",
            "royal challengers": "RCB",
            "royal challengers bengaluru": "RCB",
            "bangalore": "RCB",
            "bengaluru": "RCB",
            "csk": "CSK",
            "chennai": "CSK",
            "chennai super kings": "CSK",
            "super kings": "CSK",
            "mi": "MI",
            "mumbai": "MI",
            "mumbai indians": "MI",
            "kkr": "KKR",
            "kolkata": "KKR",
            "kolkata knight riders": "KKR",
            "knight riders": "KKR",
            "dc": "DC",
            "delhi": "DC",
            "delhi capitals": "DC",
            "capitals": "DC",
            "pbks": "PBKS",
            "punjab": "PBKS",
            "punjab kings": "PBKS",
            "kings": "PBKS",
            "rr": "RR",
            "rajasthan": "RR",
            "rajasthan royals": "RR",
            "royals": "RR",
            "srh": "SRH",
            "hyderabad": "SRH",
            "sunrisers": "SRH",
            "sunrisers hyderabad": "SRH",
            "gt": "GT",
            "gujarat": "GT",
            "gujarat titans": "GT",
            "titans": "GT",
            "lsg": "LSG",
            "lucknow": "LSG",
            "lucknow super giants": "LSG",
            "super giants": "LSG",
        }
        return team_map.get(team_name.lower(), team_name.upper())

    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
        except:
            return date_str

    def _format_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Format events for API response."""
        formatted = []
        for event in events:
            categories = event.get("ticket_categories", [])
            min_price = min((c.get("price", 0) for c in categories), default=0)
            max_price = max((c.get("max_price", c.get("price", 0)) for c in categories), default=0)

            formatted.append({
                "id": event.get("id"),
                "name": event.get("name"),
                "category": event.get("category"),
                "sub_category": event.get("sub_category", ""),
                "artist": event.get("artist", ""),
                "venue_name": event.get("venue_name", ""),
                "city": event.get("city", ""),
                "venue_city": event.get("city", ""),  # Alias for compatibility
                "date": event.get("date", ""),
                "time": event.get("time", ""),
                "formatted_date": self._format_date(event.get("date", "")),
                "status": event.get("status", "available"),
                "image_url": event.get("image_url", ""),
                "min_price": min_price,
                "max_price": max_price,
                "formatted_price": f"₹{min_price:,}" + (f" - ₹{max_price:,}" if max_price > min_price else ""),
                "is_featured": event.get("is_featured", False),
                "ticketing_partner": event.get("ticketing_partner", "TicketGenie"),
                "booking_url": self._generate_booking_url(event),
            })

        return formatted

    def _format_ipl_matches(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Format IPL matches for API response."""
        formatted = []
        for event in events:
            categories = event.get("ticket_categories", [])
            min_price = min((c.get("price", 0) for c in categories), default=0)
            max_price = max((c.get("max_price", c.get("price", 0)) for c in categories), default=0)

            home_team = self._ipl_teams.get(event.get("home_team", ""))
            away_team = self._ipl_teams.get(event.get("away_team", ""))

            formatted.append({
                "id": event.get("id"),
                "name": event.get("name"),
                "full_name": event.get("full_name", ""),
                "match_number": event.get("match_number"),
                "tournament": event.get("tournament", "TATA IPL 2025"),
                "home_team": {
                    "code": event.get("home_team"),
                    "name": event.get("home_team_name", ""),
                    "logo": event.get("home_team_logo", ""),
                    "color": home_team.get("primary_color", "") if home_team else "",
                },
                "away_team": {
                    "code": event.get("away_team"),
                    "name": event.get("away_team_name", ""),
                    "logo": event.get("away_team_logo", ""),
                    "color": away_team.get("primary_color", "") if away_team else "",
                },
                "venue_name": event.get("venue_name", ""),
                "city": event.get("city", ""),
                "venue_city": event.get("city", ""),  # Alias for compatibility
                "date": event.get("date", ""),
                "time": event.get("time", ""),
                "formatted_date": self._format_date(event.get("date", "")),
                "status": event.get("status", "upcoming"),
                "image_url": event.get("image_url", ""),
                "min_price": min_price,
                "max_price": max_price,
                "formatted_price": f"₹{min_price:,}" + (f" - ₹{max_price:,}" if max_price > min_price else ""),
                "ticketing_partner": event.get("ticketing_partner", "TicketGenie"),
                "booking_url": self._generate_booking_url(event),
            })

        return formatted
