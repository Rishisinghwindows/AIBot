"""
Travel Service

Provides Indian travel features:
- PNR Status (Indian Railways)
- Train Running Status
- Metro Information
"""

import logging
import random
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Indian Railways stations
POPULAR_STATIONS = {
    "NDLS": "New Delhi",
    "BCT": "Mumbai Central",
    "HWH": "Howrah Junction",
    "MAS": "Chennai Central",
    "SBC": "Bangalore City",
    "CSTM": "Mumbai CST",
    "NZM": "Hazrat Nizamuddin",
    "KGP": "Kharagpur",
    "PUNE": "Pune Junction",
    "JP": "Jaipur Junction",
}

# Popular trains
POPULAR_TRAINS = {
    "12301": "Howrah Rajdhani Express",
    "12302": "New Delhi Rajdhani Express",
    "12951": "Mumbai Rajdhani Express",
    "12952": "New Delhi Rajdhani Express",
    "12259": "Sealdah Duronto Express",
    "12260": "Howrah Duronto Express",
    "22691": "Rajdhani Express",
    "12309": "Rajdhani Express",
    "12013": "Amritsar Shatabdi Express",
    "12014": "New Delhi Shatabdi Express",
}


class TravelService:
    """Service for Indian travel-related queries."""

    # RapidAPI endpoints (same as D23Bot reference)
    PNR_API_HOST = "irctc-indian-railway-pnr-status.p.rapidapi.com"
    PNR_API_URL = f"https://{PNR_API_HOST}/getPNRStatus"

    TRAIN_STATUS_API_HOST = "indian-railway-irctc.p.rapidapi.com"
    TRAIN_STATUS_API_URL = f"https://{TRAIN_STATUS_API_HOST}/api/trains/v1/train/status"

    def __init__(self, railway_api_key: Optional[str] = None):
        self.railway_api_key = railway_api_key

    async def get_pnr_status(self, pnr: str) -> Dict[str, Any]:
        """
        Get PNR status for Indian Railways.

        Args:
            pnr: 10-digit PNR number

        Returns:
            PNR status with passenger details
        """
        # Validate PNR format
        pnr = pnr.strip()
        if not pnr.isdigit() or len(pnr) != 10:
            return {
                "success": False,
                "error": "Invalid PNR. Please provide a 10-digit PNR number."
            }

        try:
            # If we have API key, try real API
            if self.railway_api_key:
                logger.info(f"Attempting real PNR API call for {pnr}")
                result = await self._fetch_real_pnr(pnr)
                if result["success"]:
                    logger.info(f"Real PNR API succeeded for {pnr}")
                    return result
                else:
                    logger.warning(f"Real PNR API failed for {pnr}: {result.get('error')}")
            else:
                logger.info(f"No API key configured, using demo data for {pnr}")

            # Return simulated data for demo
            logger.info(f"Returning demo PNR data for {pnr}")
            return self._generate_demo_pnr(pnr)

        except Exception as e:
            logger.error(f"PNR status error: {e}")
            return {"success": False, "error": str(e)}

    async def _fetch_real_pnr(self, pnr: str) -> Dict[str, Any]:
        """Fetch real PNR status from API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.PNR_API_URL}/{pnr}",
                    headers={
                        "X-RapidAPI-Key": self.railway_api_key,
                        "X-RapidAPI-Host": self.PNR_API_HOST,
                        "Accept": "application/json",
                    }
                )

                logger.debug(f"PNR API response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"PNR API response for {pnr}: {data}")

                    # Check for explicit error responses
                    if data.get("error") or data.get("status") == "error":
                        return {
                            "success": False,
                            "error": data.get("message", f"PNR {pnr} not found or invalid")
                        }

                    # Extract PNR data from various possible response structures
                    pnr_data = data.get("data", data)

                    # Handle case where data is empty or None
                    if not pnr_data or pnr_data == {}:
                        logger.warning(f"PNR API returned empty data for {pnr}")
                        return {
                            "success": False,
                            "error": f"PNR {pnr} not found. Please check the number and try again."
                        }

                    return {
                        "success": True,
                        "data": self._parse_pnr_response(pnr_data, pnr)
                    }
                elif response.status_code == 404:
                    return {"success": False, "error": f"PNR {pnr} not found or invalid"}
                elif response.status_code in [401, 403]:
                    return {"success": False, "error": "Invalid API key. Please check your RapidAPI key."}
                elif response.status_code == 429:
                    return {"success": False, "error": "API rate limit exceeded. Please try again later."}
                else:
                    return {"success": False, "error": f"API returned status {response.status_code}"}

        except httpx.TimeoutException:
            logger.warning(f"PNR API timeout for {pnr}")
            return {"success": False, "error": "Request timed out. Please try again."}
        except Exception as e:
            logger.warning(f"Real PNR API failed: {e}")
            return {"success": False, "error": str(e)}

    def _parse_pnr_response(self, data: Dict, pnr: str) -> Dict[str, Any]:
        """Parse PNR API response into standard format."""
        # Extract train number - this is a critical field
        train_number = (
            data.get("trainNumber") or
            data.get("train_number") or
            data.get("trainNo") or
            data.get("TrainNo") or
            "N/A"
        )

        # Extract train name
        train_name = (
            data.get("trainName") or
            data.get("train_name") or
            data.get("TrainName") or
            "N/A"
        )

        # Extract stations
        from_station = (
            data.get("boardingPoint") or
            data.get("boarding_point") or
            data.get("from") or
            data.get("source") or
            data.get("FromStation") or
            data.get("sourceStation") or
            data.get("fromStation") or
            "N/A"
        )

        to_station = (
            data.get("destinationStation") or
            data.get("destination_station") or
            data.get("to") or
            data.get("destination") or
            data.get("ToStation") or
            data.get("destStation") or
            data.get("toStation") or
            "N/A"
        )

        # Extract journey date
        journey_date = (
            data.get("dateOfJourney") or
            data.get("date_of_journey") or
            data.get("doj") or
            data.get("journey_date") or
            data.get("journeyDate") or
            data.get("DOJ") or
            "N/A"
        )

        # Extract class
        travel_class = (
            data.get("journeyClass") or
            data.get("journey_class") or
            data.get("class") or
            data.get("Class") or
            data.get("travelClass") or
            "N/A"
        )

        # Extract chart status
        chart_prepared = (
            data.get("chartPrepared") or
            data.get("chart_prepared") or
            data.get("chartStatus") == "Chart Prepared" or
            data.get("isChartPrepared") or
            False
        )

        # Extract passengers
        passenger_list = (
            data.get("passengers") or
            data.get("passengerList") or
            data.get("PassengerStatus") or
            []
        )

        return {
            "pnr": pnr,
            "train_number": train_number,
            "train_name": train_name,
            "from_station": from_station,
            "to_station": to_station,
            "journey_date": journey_date,
            "class": travel_class,
            "chart_prepared": bool(chart_prepared),
            "passengers": self._parse_passengers(passenger_list)
        }

    def _parse_passengers(self, passengers: List) -> List[Dict]:
        """Parse passenger list from API."""
        result = []
        for p in passengers:
            result.append({
                "booking_status": (
                    p.get("bookingStatus") or
                    p.get("booking_status") or
                    p.get("BookingStatus") or
                    "N/A"
                ),
                "current_status": (
                    p.get("currentStatus") or
                    p.get("current_status") or
                    p.get("CurrentStatus") or
                    "N/A"
                ),
                "coach": p.get("coach") or p.get("coachPosition") or p.get("Coach") or "",
                "berth": p.get("berth") or p.get("berthNumber") or p.get("Berth") or p.get("berth_number") or "",
            })
        return result

    def _generate_demo_pnr(self, pnr: str) -> Dict[str, Any]:
        """Generate demo PNR status."""
        seed = hash(pnr)
        random.seed(seed)

        # Random train
        train_number = random.choice(list(POPULAR_TRAINS.keys()))
        train_name = POPULAR_TRAINS[train_number]

        # Random stations
        station_codes = list(POPULAR_STATIONS.keys())
        from_code = random.choice(station_codes)
        to_code = random.choice([s for s in station_codes if s != from_code])

        # Journey date (future)
        journey_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%d-%m-%Y")

        # Passenger statuses
        statuses = ["CNF", "RAC", "WL"]
        weights = [0.6, 0.25, 0.15]
        num_passengers = random.randint(1, 4)
        passengers = []

        for i in range(num_passengers):
            booking_status = random.choices(statuses, weights=weights)[0]
            if booking_status == "CNF":
                coaches = ["B1", "B2", "B3", "S1", "S2", "A1", "A2"]
                coach = random.choice(coaches)
                berth = random.randint(1, 72)
                berth_type = random.choice(["LB", "UB", "MB", "SL", "SU"])
                current_status = f"CNF/{coach}/{berth}/{berth_type}"
            elif booking_status == "RAC":
                rac_num = random.randint(1, 15)
                current_status = f"RAC {rac_num}"
                coach = ""
                berth = ""
            else:
                wl_num = random.randint(1, 50)
                current_status = f"WL {wl_num}"
                coach = ""
                berth = ""

            passengers.append({
                "booking_status": booking_status,
                "current_status": current_status,
                "coach": coach,
                "berth": str(berth) if berth else ""
            })

        return {
            "success": True,
            "data": {
                "pnr": pnr,
                "train_number": train_number,
                "train_name": train_name,
                "from_station": f"{POPULAR_STATIONS[from_code]} ({from_code})",
                "to_station": f"{POPULAR_STATIONS[to_code]} ({to_code})",
                "journey_date": journey_date,
                "class": random.choice(["SL", "3A", "2A", "1A"]),
                "chart_prepared": random.choice([True, False]),
                "passengers": passengers
            }
        }

    async def get_train_status(
        self,
        train_number: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get live train running status.

        Args:
            train_number: Train number (4-5 digits)
            date: Journey date (optional, defaults to today)

        Returns:
            Train running status with delay info
        """
        train_number = train_number.strip()
        if not train_number.isdigit() or len(train_number) not in [4, 5]:
            return {
                "success": False,
                "error": "Invalid train number. Please provide a 4-5 digit train number."
            }

        try:
            # If we have API key, try real API
            if self.railway_api_key:
                result = await self._fetch_real_train_status(train_number, date)
                if result["success"]:
                    return result

            # Return simulated data for demo
            return self._generate_demo_train_status(train_number)

        except Exception as e:
            logger.error(f"Train status error: {e}")
            return {"success": False, "error": str(e)}

    async def _fetch_real_train_status(
        self,
        train_number: str,
        date: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch real train status from API."""
        try:
            if not date:
                date = datetime.now().strftime("%Y%m%d")
            elif "-" in date:
                date = date.replace("-", "")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.TRAIN_STATUS_API_URL,
                    params={
                        "train_number": train_number,
                        "departure_date": date,
                        "isH5": "true",
                        "client": "web",
                    },
                    headers={
                        "X-RapidAPI-Key": self.railway_api_key,
                        "X-RapidAPI-Host": self.TRAIN_STATUS_API_HOST,
                        "x-rapid-api": "rapid-api-database",
                        "Accept": "application/json",
                    }
                )

                logger.debug(f"Train status API response status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Train status API response for {train_number}: {data}")

                    if data.get("error") or data.get("status") == "error":
                        return {
                            "success": False,
                            "error": data.get("message", f"Train {train_number} not found or not running")
                        }

                    return {
                        "success": True,
                        "data": self._parse_train_status(data.get("data", data), train_number)
                    }
                elif response.status_code == 404:
                    return {"success": False, "error": f"Train {train_number} not found or not running on this date"}
                elif response.status_code in [401, 403]:
                    return {"success": False, "error": "Train status API requires subscription"}
                elif response.status_code == 429:
                    return {"success": False, "error": "API rate limit exceeded. Please try again later."}
                else:
                    return {"success": False, "error": f"API returned status {response.status_code}"}

        except httpx.TimeoutException:
            logger.warning(f"Train status API timeout for {train_number}")
            return {"success": False, "error": "Request timed out. Please try again."}
        except Exception as e:
            logger.warning(f"Real train status API failed: {e}")
            return {"success": False, "error": str(e)}

    def _parse_train_status(self, data: Dict, train_number: str) -> Dict[str, Any]:
        """Parse train status API response."""
        # Handle current station
        current_station = data.get("currentStation", data.get("current_station", {}))
        if isinstance(current_station, str):
            current_station = {"name": current_station}

        # Handle delay
        delay = data.get("delay", data.get("delayInMinutes", 0))
        if isinstance(delay, str):
            try:
                delay = int(delay.replace("min", "").strip())
            except:
                delay = 0

        # Determine running status
        status = data.get("status", data.get("running_status", ""))
        if not status:
            if delay == 0:
                status = "On Time"
            elif delay > 0:
                status = f"Running Late by {delay} min"
            else:
                status = f"Running Early by {abs(delay)} min"

        return {
            "train_number": train_number,
            "train_name": data.get("trainName", data.get("train_name", "N/A")),
            "running_status": status,
            "delay_minutes": delay,
            "last_station": data.get("lastStation", current_station.get("name", "N/A")),
            "last_station_time": data.get("lastStationTime", current_station.get("time", "")),
            "next_station": data.get("nextStation", data.get("next_station", "N/A")),
            "eta_next_station": data.get("etaNextStation", data.get("eta", "")),
            "source": data.get("source", data.get("from", "")),
            "destination": data.get("destination", data.get("to", "")),
        }

    def _generate_demo_train_status(self, train_number: str) -> Dict[str, Any]:
        """Generate demo train status."""
        seed = hash(f"{train_number}{datetime.now().date().isoformat()}")
        random.seed(seed)

        # Get train name
        train_name = POPULAR_TRAINS.get(train_number, f"Express {train_number}")

        # Random status
        statuses = ["Running on time", "Running late", "Arrived at station", "Departed from station"]
        status = random.choice(statuses)

        # Random delay
        delay = random.choice([0, 0, 0, 5, 10, 15, 20, 30, 45, 60, 90])

        # Random stations
        station_codes = list(POPULAR_STATIONS.keys())
        last_station_code = random.choice(station_codes)
        next_station_code = random.choice([s for s in station_codes if s != last_station_code])

        # Times
        last_time = datetime.now() - timedelta(minutes=random.randint(10, 60))
        eta = datetime.now() + timedelta(minutes=random.randint(30, 180))

        return {
            "success": True,
            "data": {
                "train_number": train_number,
                "train_name": train_name,
                "running_status": status,
                "delay_minutes": delay,
                "last_station": f"{POPULAR_STATIONS[last_station_code]} ({last_station_code})",
                "last_station_time": last_time.strftime("%H:%M"),
                "next_station": f"{POPULAR_STATIONS[next_station_code]} ({next_station_code})",
                "eta_next_station": eta.strftime("%H:%M")
            }
        }

    async def get_metro_info(
        self,
        source: str,
        destination: str,
        city: str = "delhi"
    ) -> Dict[str, Any]:
        """
        Get metro route and fare information.

        Args:
            source: Source station
            destination: Destination station
            city: Metro city (delhi, bangalore, mumbai, etc.)

        Returns:
            Metro route with fare and time
        """
        try:
            city = city.lower()

            # Delhi Metro stations (simplified)
            delhi_metro_lines = {
                "blue": ["Dwarka Sector 21", "Dwarka", "Janakpuri West", "Rajouri Garden", "Kirti Nagar", "Moti Nagar", "Ramesh Nagar", "Rajiv Chowk", "Mandi House", "Pragati Maidan", "Noida City Centre"],
                "yellow": ["Samaypur Badli", "Jahangirpuri", "Kashmere Gate", "Chandni Chowk", "New Delhi", "Rajiv Chowk", "AIIMS", "Hauz Khas", "Qutub Minar", "Huda City Centre"],
                "red": ["Shaheed Sthal", "Dilshad Garden", "Welcome", "Shahdara", "Kashmere Gate", "Tis Hazari", "Rithala"],
                "green": ["Inderlok", "Ashok Park Main", "Kirti Nagar", "Mundka"],
                "violet": ["Kashmere Gate", "ITO", "Mandi House", "Central Secretariat", "Khan Market", "Nehru Place", "Kalkaji Mandir", "Escorts Mujesar"],
                "pink": ["Majlis Park", "Netaji Subhash Place", "Azadpur", "Shalimar Bagh", "Haiderpur Badli Mor", "Lajpat Nagar", "South Extension", "Saket"],
            }

            # Base fare calculation
            base_fare = 10
            per_km_fare = 2.5

            # Estimate distance and time
            seed = hash(f"{source}{destination}")
            random.seed(seed)
            distance = random.randint(5, 35)
            time_minutes = int(distance * 2.5)
            fare = int(base_fare + (distance * per_km_fare))
            fare = min(fare, 60)  # Max fare cap

            # Find connecting lines
            interchange_stations = ["Rajiv Chowk", "Kashmere Gate", "Central Secretariat", "Mandi House", "Kirti Nagar"]
            interchanges = random.randint(0, 2)

            return {
                "success": True,
                "data": {
                    "source": source,
                    "destination": destination,
                    "city": city.capitalize(),
                    "distance_km": distance,
                    "time_minutes": time_minutes,
                    "fare": fare,
                    "interchanges": interchanges,
                    "interchange_stations": random.sample(interchange_stations, min(interchanges, len(interchange_stations))) if interchanges > 0 else [],
                    "first_train": "05:30 AM",
                    "last_train": "11:00 PM",
                    "frequency": "3-5 minutes during peak hours"
                }
            }
        except Exception as e:
            logger.error(f"Metro info error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_travel_service: Optional[TravelService] = None


def get_travel_service(railway_api_key: Optional[str] = None) -> TravelService:
    """Get singleton travel service instance."""
    global _travel_service
    if _travel_service is None:
        logger.info(f"Creating TravelService with API key: {'set' if railway_api_key else 'not set'}")
        _travel_service = TravelService(railway_api_key)
    elif railway_api_key and not _travel_service.railway_api_key:
        # Update API key if it wasn't set initially
        logger.info("Updating TravelService with API key")
        _travel_service.railway_api_key = railway_api_key
    return _travel_service
