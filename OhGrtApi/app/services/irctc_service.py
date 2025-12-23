from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import date

import httpx

from app.logger import logger


class IRCTCService:
    """
    IRCTC / Indian Railways service for train search, PNR status, and seat availability.

    Note: This service requires an IRCTC API key or uses RapidAPI's IRCTC endpoints.
    """

    def __init__(
        self,
        *,
        api_key: str = None,
        base_url: str = "https://irctc1.p.rapidapi.com",
    ):
        self.api_key = api_key or ""
        self.base_url = base_url
        self.available = bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "irctc1.p.rapidapi.com",
        }

    async def check_pnr_status(self, pnr: str) -> str:
        """Check PNR status for a booked ticket."""
        if not self.available:
            return "IRCTC service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v3/getPNRStatus",
                    headers=self._get_headers(),
                    params={"pnrNumber": pnr},
                )

                if resp.status_code != 200:
                    return f"Failed to check PNR status: {resp.status_code}"

                data = resp.json()
                if not data.get("status"):
                    return f"Error: {data.get('message', 'Unknown error')}"

                pnr_data = data.get("data", {})
                train_name = pnr_data.get("trainName", "Unknown")
                train_no = pnr_data.get("trainNumber", "Unknown")
                boarding = pnr_data.get("boardingPoint", "Unknown")
                destination = pnr_data.get("destinationStation", "Unknown")
                doj = pnr_data.get("dateOfJourney", "Unknown")
                chart_status = pnr_data.get("chartStatus", "Not Prepared")

                passengers = pnr_data.get("passengerList", [])
                passenger_info = []
                for i, p in enumerate(passengers, 1):
                    booking = p.get("bookingStatus", "Unknown")
                    current = p.get("currentStatus", "Unknown")
                    passenger_info.append(f"  {i}. Booking: {booking} | Current: {current}")

                return (
                    f"PNR Status for {pnr}:\n"
                    f"Train: {train_no} - {train_name}\n"
                    f"From: {boarding} -> To: {destination}\n"
                    f"Date of Journey: {doj}\n"
                    f"Chart Status: {chart_status}\n\n"
                    f"Passengers:\n" + "\n".join(passenger_info)
                )

        except Exception as exc:
            logger.error("irctc_pnr_error", error=str(exc))
            return f"IRCTC error: {exc}"

    async def search_trains(
        self,
        from_station: str,
        to_station: str,
        journey_date: str,
    ) -> str:
        """
        Search for trains between two stations.

        Args:
            from_station: Source station code (e.g., 'NDLS' for New Delhi)
            to_station: Destination station code (e.g., 'BCT' for Mumbai Central)
            journey_date: Date in YYYY-MM-DD format
        """
        if not self.available:
            return "IRCTC service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v3/trainBetweenStations",
                    headers=self._get_headers(),
                    params={
                        "fromStationCode": from_station.upper(),
                        "toStationCode": to_station.upper(),
                        "dateOfJourney": journey_date,
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to search trains: {resp.status_code}"

                data = resp.json()
                if not data.get("status"):
                    return f"Error: {data.get('message', 'No trains found')}"

                trains = data.get("data", [])
                if not trains:
                    return f"No trains found from {from_station} to {to_station} on {journey_date}"

                results = []
                for train in trains[:10]:
                    train_no = train.get("train_number", "Unknown")
                    train_name = train.get("train_name", "Unknown")
                    departure = train.get("from_std", "Unknown")
                    arrival = train.get("to_std", "Unknown")
                    duration = train.get("duration", "Unknown")
                    classes = ", ".join(train.get("class_type", []))

                    results.append(
                        f"- {train_no} | {train_name}\n"
                        f"  Departs: {departure} | Arrives: {arrival} | Duration: {duration}\n"
                        f"  Classes: {classes}"
                    )

                return (
                    f"Trains from {from_station} to {to_station} on {journey_date}:\n\n"
                    + "\n\n".join(results)
                )

        except Exception as exc:
            logger.error("irctc_search_error", error=str(exc))
            return f"IRCTC error: {exc}"

    async def check_seat_availability(
        self,
        train_number: str,
        from_station: str,
        to_station: str,
        journey_date: str,
        class_type: str = "SL",
    ) -> str:
        """
        Check seat availability for a specific train.

        Args:
            train_number: Train number (e.g., '12301')
            from_station: Source station code
            to_station: Destination station code
            journey_date: Date in YYYY-MM-DD format
            class_type: Class type (SL, 3A, 2A, 1A, CC, EC, etc.)
        """
        if not self.available:
            return "IRCTC service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/checkSeatAvailability",
                    headers=self._get_headers(),
                    params={
                        "classType": class_type.upper(),
                        "fromStationCode": from_station.upper(),
                        "toStationCode": to_station.upper(),
                        "trainNo": train_number,
                        "date": journey_date,
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to check availability: {resp.status_code}"

                data = resp.json()
                if not data.get("status"):
                    return f"Error: {data.get('message', 'Unknown error')}"

                availability = data.get("data", [])
                if not availability:
                    return f"No availability data for train {train_number}"

                results = []
                for day in availability:
                    avl_date = day.get("date", "Unknown")
                    status = day.get("current_status", "Unknown")
                    results.append(f"  {avl_date}: {status}")

                return (
                    f"Seat Availability for Train {train_number} ({class_type}):\n"
                    f"From: {from_station} -> To: {to_station}\n\n"
                    + "\n".join(results)
                )

        except Exception as exc:
            logger.error("irctc_availability_error", error=str(exc))
            return f"IRCTC error: {exc}"

    async def get_train_schedule(self, train_number: str) -> str:
        """Get the complete schedule/route of a train."""
        if not self.available:
            return "IRCTC service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/getTrainSchedule",
                    headers=self._get_headers(),
                    params={"trainNo": train_number},
                )

                if resp.status_code != 200:
                    return f"Failed to get schedule: {resp.status_code}"

                data = resp.json()
                if not data.get("status"):
                    return f"Error: {data.get('message', 'Unknown error')}"

                schedule_data = data.get("data", {})
                train_name = schedule_data.get("train_name", "Unknown")
                route = schedule_data.get("route", [])

                if not route:
                    return f"No schedule found for train {train_number}"

                results = []
                for stop in route:
                    station = stop.get("station_name", "Unknown")
                    code = stop.get("station_code", "")
                    arrival = stop.get("arrival", "--")
                    departure = stop.get("departure", "--")
                    day = stop.get("day", "1")

                    results.append(
                        f"  Day {day}: {station} ({code}) | Arr: {arrival} | Dep: {departure}"
                    )

                return (
                    f"Schedule for {train_number} - {train_name}:\n\n"
                    + "\n".join(results)
                )

        except Exception as exc:
            logger.error("irctc_schedule_error", error=str(exc))
            return f"IRCTC error: {exc}"

    async def get_live_status(self, train_number: str, journey_date: str) -> str:
        """Get live running status of a train."""
        if not self.available:
            return "IRCTC service is not configured. Please add your API key in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/api/v1/liveTrainStatus",
                    headers=self._get_headers(),
                    params={
                        "trainNo": train_number,
                        "startDate": journey_date,
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to get live status: {resp.status_code}"

                data = resp.json()
                if not data.get("status"):
                    return f"Error: {data.get('message', 'Train not found or not running')}"

                live_data = data.get("data", {})
                train_name = live_data.get("train_name", "Unknown")
                current_station = live_data.get("current_station_name", "Unknown")
                delay = live_data.get("delay", "0")
                last_update = live_data.get("updated_time", "Unknown")

                return (
                    f"Live Status for {train_number} - {train_name}:\n"
                    f"Current Station: {current_station}\n"
                    f"Delay: {delay} minutes\n"
                    f"Last Updated: {last_update}"
                )

        except Exception as exc:
            logger.error("irctc_live_status_error", error=str(exc))
            return f"IRCTC error: {exc}"
