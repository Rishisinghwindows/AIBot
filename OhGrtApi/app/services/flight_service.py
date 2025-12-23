from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import date, datetime

import httpx

from app.logger import logger


class FlightService:
    """
    Flight search and booking service.

    This implementation uses Amadeus API for flight search.
    See: https://developers.amadeus.com/

    Can also be adapted for:
    - Skyscanner API
    - Kiwi.com API
    - Google Flights (via SerpAPI)
    """

    def __init__(
        self,
        *,
        api_key: str = None,
        api_secret: str = None,
        base_url: str = "https://test.api.amadeus.com",
    ):
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.available = bool(self.api_key and self.api_secret)

    async def _get_access_token(self) -> Optional[str]:
        """Get or refresh Amadeus access token."""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.api_key,
                        "client_secret": self.api_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if resp.status_code != 200:
                    logger.error("flight_auth_error", status=resp.status_code)
                    return None

                data = resp.json()
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", 1799)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
                return self.access_token

        except Exception as exc:
            logger.error("flight_auth_error", error=str(exc))
            return None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        travel_class: str = "ECONOMY",
        non_stop: bool = False,
        max_results: int = 10,
        currency: str = "INR",
    ) -> str:
        """
        Search for flights.

        Args:
            origin: Origin airport IATA code (e.g., 'DEL' for Delhi)
            destination: Destination airport IATA code (e.g., 'BOM' for Mumbai)
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date for round trips
            adults: Number of adults (12+ years)
            children: Number of children (2-11 years)
            infants: Number of infants (under 2 years)
            travel_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
            non_stop: Only show non-stop flights
            max_results: Maximum number of results
            currency: Currency code for prices
        """
        if not self.available:
            return "Flight service is not configured. Please add your API credentials in Settings."

        token = await self._get_access_token()
        if not token:
            return "Failed to authenticate with flight service."

        try:
            params: Dict[str, Any] = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": adults,
                "travelClass": travel_class.upper(),
                "currencyCode": currency.upper(),
                "max": max_results,
            }

            if return_date:
                params["returnDate"] = return_date
            if children > 0:
                params["children"] = children
            if infants > 0:
                params["infants"] = infants
            if non_stop:
                params["nonStop"] = "true"

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(
                    f"{self.base_url}/v2/shopping/flight-offers",
                    headers=self._get_headers(),
                    params=params,
                )

                if resp.status_code != 200:
                    error_data = resp.json() if resp.content else {}
                    errors = error_data.get("errors", [])
                    if errors:
                        return f"Flight search error: {errors[0].get('detail', 'Unknown error')}"
                    return f"Failed to search flights: {resp.status_code}"

                data = resp.json()
                flights = data.get("data", [])

                if not flights:
                    return f"No flights found from {origin} to {destination} on {departure_date}"

                results = []
                for i, flight in enumerate(flights[:max_results], 1):
                    price = flight.get("price", {})
                    total_price = price.get("total", "N/A")
                    currency_code = price.get("currency", currency)

                    itineraries = flight.get("itineraries", [])
                    segments_info = []

                    for itin_idx, itinerary in enumerate(itineraries):
                        duration = itinerary.get("duration", "N/A")
                        # Convert ISO 8601 duration (PT2H30M) to readable format
                        duration_readable = self._format_duration(duration)
                        direction = "Outbound" if itin_idx == 0 else "Return"

                        segments = itinerary.get("segments", [])
                        stops = len(segments) - 1
                        stops_text = "Non-stop" if stops == 0 else f"{stops} stop(s)"

                        if segments:
                            first_seg = segments[0]
                            last_seg = segments[-1]
                            departure_time = first_seg.get("departure", {}).get("at", "")[:16]
                            arrival_time = last_seg.get("arrival", {}).get("at", "")[:16]
                            carrier = first_seg.get("carrierCode", "")
                            flight_num = first_seg.get("number", "")

                            segments_info.append(
                                f"  {direction}: {carrier}{flight_num} | {departure_time} -> {arrival_time}\n"
                                f"    Duration: {duration_readable} | {stops_text}"
                            )

                    results.append(
                        f"{i}. {currency_code} {total_price}\n" +
                        "\n".join(segments_info)
                    )

                trip_type = "Round Trip" if return_date else "One Way"
                header = (
                    f"Flights from {origin} to {destination}\n"
                    f"Date: {departure_date}"
                    + (f" - {return_date}" if return_date else "")
                    + f" | {trip_type} | {adults} Adult(s)\n"
                    f"{'=' * 50}\n\n"
                )

                return header + "\n\n".join(results)

        except Exception as exc:
            logger.error("flight_search_error", error=str(exc))
            return f"Flight search error: {exc}"

    def _format_duration(self, iso_duration: str) -> str:
        """Convert ISO 8601 duration (PT2H30M) to readable format (2h 30m)."""
        if not iso_duration or not iso_duration.startswith("PT"):
            return iso_duration

        duration = iso_duration[2:]  # Remove 'PT'
        hours = 0
        minutes = 0

        if "H" in duration:
            h_idx = duration.index("H")
            hours = int(duration[:h_idx])
            duration = duration[h_idx + 1:]

        if "M" in duration:
            m_idx = duration.index("M")
            minutes = int(duration[:m_idx])

        return f"{hours}h {minutes}m"

    async def get_flight_price(
        self,
        flight_offer: Dict[str, Any],
    ) -> str:
        """Confirm real-time price for a flight offer."""
        if not self.available:
            return "Flight service is not configured."

        token = await self._get_access_token()
        if not token:
            return "Failed to authenticate with flight service."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/shopping/flight-offers/pricing",
                    headers=self._get_headers(),
                    json={
                        "data": {
                            "type": "flight-offers-pricing",
                            "flightOffers": [flight_offer],
                        }
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to get price: {resp.status_code}"

                data = resp.json()
                flight_offers = data.get("data", {}).get("flightOffers", [])

                if not flight_offers:
                    return "Price confirmation not available."

                offer = flight_offers[0]
                price = offer.get("price", {})
                total = price.get("grandTotal", "N/A")
                currency = price.get("currency", "INR")

                return f"Confirmed Price: {currency} {total}"

        except Exception as exc:
            logger.error("flight_price_error", error=str(exc))
            return f"Price confirmation error: {exc}"

    async def search_airports(self, keyword: str) -> str:
        """Search for airports by city name or IATA code."""
        if not self.available:
            return "Flight service is not configured."

        token = await self._get_access_token()
        if not token:
            return "Failed to authenticate with flight service."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/v1/reference-data/locations",
                    headers=self._get_headers(),
                    params={
                        "keyword": keyword,
                        "subType": "AIRPORT,CITY",
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to search airports: {resp.status_code}"

                data = resp.json()
                locations = data.get("data", [])

                if not locations:
                    return f"No airports found for '{keyword}'"

                results = []
                for loc in locations[:10]:
                    iata = loc.get("iataCode", "N/A")
                    name = loc.get("name", "Unknown")
                    city = loc.get("address", {}).get("cityName", "")
                    country = loc.get("address", {}).get("countryName", "")
                    loc_type = loc.get("subType", "")

                    results.append(
                        f"- {iata}: {name}\n"
                        f"  {city}, {country} ({loc_type})"
                    )

                return "Airports Found:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("flight_airport_search_error", error=str(exc))
            return f"Airport search error: {exc}"

    async def get_cheapest_dates(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
    ) -> str:
        """Find cheapest travel dates for a route."""
        if not self.available:
            return "Flight service is not configured."

        token = await self._get_access_token()
        if not token:
            return "Failed to authenticate with flight service."

        try:
            params: Dict[str, Any] = {
                "origin": origin.upper(),
                "destination": destination.upper(),
            }
            if departure_date:
                params["departureDate"] = departure_date

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/v1/shopping/flight-dates",
                    headers=self._get_headers(),
                    params=params,
                )

                if resp.status_code != 200:
                    return f"Failed to get cheapest dates: {resp.status_code}"

                data = resp.json()
                dates = data.get("data", [])

                if not dates:
                    return f"No cheap flights found from {origin} to {destination}"

                results = []
                for d in dates[:10]:
                    dep_date = d.get("departureDate", "Unknown")
                    ret_date = d.get("returnDate", "N/A")
                    price = d.get("price", {})
                    total = price.get("total", "N/A")

                    results.append(
                        f"- {dep_date} -> {ret_date}: INR {total}"
                    )

                return (
                    f"Cheapest Dates for {origin} to {destination}:\n\n"
                    + "\n".join(results)
                )

        except Exception as exc:
            logger.error("flight_cheapest_dates_error", error=str(exc))
            return f"Cheapest dates error: {exc}"

    async def get_flight_status(
        self,
        carrier_code: str,
        flight_number: str,
        scheduled_departure_date: str,
    ) -> str:
        """Get real-time flight status."""
        if not self.available:
            return "Flight service is not configured."

        token = await self._get_access_token()
        if not token:
            return "Failed to authenticate with flight service."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/v2/schedule/flights",
                    headers=self._get_headers(),
                    params={
                        "carrierCode": carrier_code.upper(),
                        "flightNumber": flight_number,
                        "scheduledDepartureDate": scheduled_departure_date,
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to get flight status: {resp.status_code}"

                data = resp.json()
                flights = data.get("data", [])

                if not flights:
                    return f"No status found for {carrier_code}{flight_number}"

                flight = flights[0]
                segments = flight.get("flightPoints", [])

                if len(segments) < 2:
                    return "Incomplete flight data."

                departure = segments[0]
                arrival = segments[-1]

                dep_airport = departure.get("iataCode", "")
                arr_airport = arrival.get("iataCode", "")

                dep_times = departure.get("departure", {})
                dep_scheduled = dep_times.get("timings", [{}])[0].get("value", "")[:16] if dep_times.get("timings") else "N/A"

                arr_times = arrival.get("arrival", {})
                arr_scheduled = arr_times.get("timings", [{}])[0].get("value", "")[:16] if arr_times.get("timings") else "N/A"

                return (
                    f"Flight Status: {carrier_code}{flight_number}\n"
                    f"Date: {scheduled_departure_date}\n\n"
                    f"Departure: {dep_airport} at {dep_scheduled}\n"
                    f"Arrival: {arr_airport} at {arr_scheduled}"
                )

        except Exception as exc:
            logger.error("flight_status_error", error=str(exc))
            return f"Flight status error: {exc}"


# Import at the top if needed
from datetime import timedelta
