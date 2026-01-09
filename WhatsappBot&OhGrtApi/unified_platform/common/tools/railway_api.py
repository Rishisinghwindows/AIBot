"""
Railway API Tool

Wrapper for RapidAPI Indian Railways APIs by shivesh96.
- PNR Status: real-time-pnr-status-api-for-indian-railways
- Train Running Status: train-running-status-indian-railways
"""

import httpx
from typing import Optional, Union
from datetime import datetime
from common.config.settings import settings
from common.graph.state import ToolResult


# RapidAPI endpoints
PNR_API_HOST = "irctc-indian-railway-pnr-status.p.rapidapi.com"
PNR_API_URL = f"https://{PNR_API_HOST}/getPNRStatus"

# Train status API options (will try in order)
# Option 1: shivesh96 API (free, more reliable)
TRAIN_STATUS_API_HOST_V1 = "train-running-status-indian-railways.p.rapidapi.com"
TRAIN_STATUS_API_URL_V1 = f"https://{TRAIN_STATUS_API_HOST_V1}/getTrainRunningStatus"

# Option 2: rahilkhan224 API (backup)
TRAIN_STATUS_API_HOST_V2 = "indian-railway-irctc.p.rapidapi.com"
TRAIN_STATUS_API_URL_V2 = f"https://{TRAIN_STATUS_API_HOST_V2}/api/trains/v1/train/status"


def _get_rapidapi_headers(host: str, extra_headers: dict = None) -> dict:
    """Get headers for RapidAPI requests."""
    headers = {
        "X-RapidAPI-Key": settings.RAILWAY_API_KEY,
        "X-RapidAPI-Host": host,
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


def _make_pnr_request(pnr: str, client: Union[httpx.Client, httpx.AsyncClient]) -> ToolResult:
    """Make the API call to the PNR API."""
    response = client.get(
        f"{PNR_API_URL}/{pnr}",
        headers=_get_rapidapi_headers(PNR_API_HOST),
    )
    return _process_pnr_response(response, pnr)


async def _make_pnr_request_async(pnr: str, client: httpx.AsyncClient) -> ToolResult:
    """Make the API call to the PNR API asynchronously."""
    response = await client.get(
        f"{PNR_API_URL}/{pnr}",
        headers=_get_rapidapi_headers(PNR_API_HOST),
    )
    return _process_pnr_response(response, pnr)


def _process_pnr_response(response: httpx.Response, pnr: str) -> ToolResult:
    """Process the response from the PNR API."""
    import logging
    logger = logging.getLogger(__name__)

    if response.status_code == 200:
        data = response.json()
        logger.debug(f"PNR API response for {pnr}: {data}")

        # Check for explicit error responses
        if data.get("error") or data.get("status") == "error":
            return ToolResult(
                success=False,
                data=None,
                error=data.get("message", f"PNR {pnr} not found or invalid"),
                tool_name="railway_pnr",
            )

        # Extract PNR data from various possible response structures
        pnr_data = data.get("data", data)

        # Handle case where data is empty or None
        if not pnr_data or pnr_data == {}:
            logger.warning(f"PNR API returned empty data for {pnr}")
            return ToolResult(
                success=False,
                data=None,
                error=f"PNR {pnr} not found. Please check the number and try again.",
                tool_name="railway_pnr",
            )

        # Extract train number - this is a critical field
        train_number = (
            pnr_data.get("trainNumber") or
            pnr_data.get("train_number") or
            pnr_data.get("trainNo") or
            pnr_data.get("TrainNo")
        )

        # Extract train name
        train_name = (
            pnr_data.get("trainName") or
            pnr_data.get("train_name") or
            pnr_data.get("TrainName")
        )

        # If no train info found, the PNR is likely invalid
        if not train_number and not train_name:
            logger.warning(f"PNR API returned no train info for {pnr}: {pnr_data}")
            return ToolResult(
                success=False,
                data=None,
                error=f"PNR {pnr} not found or expired. Please verify the PNR number.",
                tool_name="railway_pnr",
            )

        # Extract stations
        from_station = (
            pnr_data.get("boardingPoint") or
            pnr_data.get("boarding_point") or
            pnr_data.get("from") or
            pnr_data.get("source") or
            pnr_data.get("FromStation") or
            pnr_data.get("sourceStation")
        )

        to_station = (
            pnr_data.get("destinationStation") or
            pnr_data.get("destination_station") or
            pnr_data.get("to") or
            pnr_data.get("destination") or
            pnr_data.get("ToStation") or
            pnr_data.get("destStation")
        )

        # Extract journey date
        journey_date = (
            pnr_data.get("dateOfJourney") or
            pnr_data.get("date_of_journey") or
            pnr_data.get("doj") or
            pnr_data.get("journey_date") or
            pnr_data.get("journeyDate") or
            pnr_data.get("DOJ")
        )

        # Extract class
        travel_class = (
            pnr_data.get("journeyClass") or
            pnr_data.get("journey_class") or
            pnr_data.get("class") or
            pnr_data.get("Class") or
            pnr_data.get("travelClass")
        )

        # Extract chart status
        chart_prepared = (
            pnr_data.get("chartPrepared") or
            pnr_data.get("chart_prepared") or
            pnr_data.get("chartStatus") == "Chart Prepared" or
            pnr_data.get("isChartPrepared") or
            False
        )

        # Extract passengers
        passengers = []
        passenger_list = (
            pnr_data.get("passengers") or
            pnr_data.get("passengerList") or
            pnr_data.get("PassengerStatus") or
            []
        )

        for p in passenger_list:
            passengers.append({
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
                "berth": p.get("berth") or p.get("berthNumber") or p.get("Berth") or "",
            })

        return ToolResult(
            success=True,
            data={
                "pnr": pnr,
                "train_number": train_number or "N/A",
                "train_name": train_name or "N/A",
                "from_station": from_station or "N/A",
                "to_station": to_station or "N/A",
                "journey_date": journey_date or "N/A",
                "class": travel_class or "N/A",
                "chart_prepared": bool(chart_prepared),
                "passengers": passengers,
            },
            error=None,
            tool_name="railway_pnr",
        )
    elif response.status_code == 404:
        return ToolResult(
            success=False,
            data=None,
            error=f"PNR {pnr} not found or invalid",
            tool_name="railway_pnr",
        )
    elif response.status_code in [401, 403]:
        return ToolResult(
            success=False,
            data=None,
            error="Invalid API key. Please check your RapidAPI key.",
            tool_name="railway_pnr",
        )
    elif response.status_code == 429:
        return ToolResult(
            success=False,
            data=None,
            error="API rate limit exceeded. Please try again later.",
            tool_name="railway_pnr",
        )
    else:
        return ToolResult(
            success=False,
            data=None,
            error=f"API returned status {response.status_code}",
            tool_name="railway_pnr",
        )


def get_pnr_status(pnr: str) -> ToolResult:
    """
    Get PNR status from RapidAPI.

    Args:
        pnr: 10-digit PNR number

    Returns:
        ToolResult with PNR status or error
    """
    if not pnr or len(pnr) != 10 or not pnr.isdigit():
        return ToolResult(
            success=False,
            data=None,
            error="Invalid PNR format. Must be 10 digits.",
            tool_name="railway_pnr",
        )

    if not settings.RAILWAY_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Railway API key not configured. Get one from RapidAPI.",
            tool_name="railway_pnr",
        )

    try:
        with httpx.Client(timeout=30.0) as client:
            return _make_pnr_request(pnr, client)
    except httpx.TimeoutException:
        return ToolResult(
            success=False,
            data=None,
            error="Request timed out. Please try again.",
            tool_name="railway_pnr",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="railway_pnr",
        )


def _make_train_status_request(train_number: str, date: str, client: Union[httpx.Client, httpx.AsyncClient]) -> ToolResult:
    """Make the API call to the train status API (tries multiple sources)."""
    import logging
    logger = logging.getLogger(__name__)

    # Try API V1 (shivesh96) first - format: trainNo/YYYYMMDD
    try:
        logger.info(f"Trying train status API V1 for train {train_number}")
        response = client.get(
            f"{TRAIN_STATUS_API_URL_V1}/{train_number}/{date}",
            headers=_get_rapidapi_headers(TRAIN_STATUS_API_HOST_V1),
        )
        result = _process_train_status_response(response, train_number)
        if result["success"]:
            return result
        logger.warning(f"API V1 failed: {result.get('error')}")
    except Exception as e:
        logger.warning(f"API V1 exception: {e}")

    # Try API V2 (rahilkhan224) as fallback
    try:
        logger.info(f"Trying train status API V2 for train {train_number}")
        extra_headers = {"x-rapid-api": "rapid-api-database"}
        response = client.get(
            TRAIN_STATUS_API_URL_V2,
            params={
                "train_number": train_number,
                "departure_date": date,
                "isH5": "true",
                "client": "web",
            },
            headers=_get_rapidapi_headers(TRAIN_STATUS_API_HOST_V2, extra_headers),
        )
        return _process_train_status_response(response, train_number)
    except Exception as e:
        logger.error(f"API V2 exception: {e}")
        return ToolResult(
            success=False,
            data=None,
            error=f"Unable to fetch train status: {e}",
            tool_name="railway_train_status",
        )


async def _make_train_status_request_async(train_number: str, date: str, client: httpx.AsyncClient) -> ToolResult:
    """Make the API call to the train status API asynchronously (tries multiple sources)."""
    import logging
    logger = logging.getLogger(__name__)

    # Try API V1 (shivesh96) first - format: trainNo/YYYYMMDD
    try:
        logger.info(f"Trying train status API V1 for train {train_number}")
        response = await client.get(
            f"{TRAIN_STATUS_API_URL_V1}/{train_number}/{date}",
            headers=_get_rapidapi_headers(TRAIN_STATUS_API_HOST_V1),
        )
        result = _process_train_status_response(response, train_number)
        if result["success"]:
            return result
        logger.warning(f"API V1 failed: {result.get('error')}")
    except Exception as e:
        logger.warning(f"API V1 exception: {e}")

    # Try API V2 (rahilkhan224) as fallback
    try:
        logger.info(f"Trying train status API V2 for train {train_number}")
        extra_headers = {"x-rapid-api": "rapid-api-database"}
        response = await client.get(
            TRAIN_STATUS_API_URL_V2,
            params={
                "train_number": train_number,
                "departure_date": date,
                "isH5": "true",
                "client": "web",
            },
            headers=_get_rapidapi_headers(TRAIN_STATUS_API_HOST_V2, extra_headers),
        )
        return _process_train_status_response(response, train_number)
    except Exception as e:
        logger.error(f"API V2 exception: {e}")
        return ToolResult(
            success=False,
            data=None,
            error=f"Unable to fetch train status: {e}",
            tool_name="railway_train_status",
        )


def _process_train_status_response(response: httpx.Response, train_number: str) -> ToolResult:
    """Process the response from the train status API."""
    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"Train status API response code: {response.status_code}")
    logger.debug(f"Train status API response: {response.text[:1000] if response.text else 'empty'}")

    if response.status_code == 200:
        data = response.json()

        # Check for error responses
        if data.get("error") or data.get("status") == "error":
            return ToolResult(
                success=False,
                data=None,
                error=data.get("message", f"Train {train_number} not found or not running"),
                tool_name="railway_train_status",
            )

        # Handle different response structures
        train_data = data.get("data", data)

        # API V1 (shivesh96) returns nested structure
        if "train_name" in data or "trainName" in data:
            train_data = data
        elif isinstance(train_data, dict) and "body" in train_data:
            # Some APIs wrap in body
            train_data = train_data.get("body", train_data)

        # Extract train name (try multiple keys)
        train_name = (
            train_data.get("train_name") or
            train_data.get("trainName") or
            train_data.get("TrainName") or
            train_data.get("name") or
            "N/A"
        )

        # Extract current/last station
        current_station = (
            train_data.get("current_station_name") or
            train_data.get("currentStation") or
            train_data.get("current_station") or
            train_data.get("last_station") or
            train_data.get("lastStation") or
            {}
        )
        if isinstance(current_station, str):
            current_station = {"name": current_station}

        last_station_name = (
            current_station.get("name") if isinstance(current_station, dict) else current_station
        ) or train_data.get("current_station_name", "N/A")

        # Extract delay
        delay = (
            train_data.get("delay") or
            train_data.get("delayInMinutes") or
            train_data.get("delay_in_minutes") or
            train_data.get("late_by") or
            0
        )
        if isinstance(delay, str):
            try:
                delay = int(delay.replace("min", "").replace("mins", "").strip())
            except:
                delay = 0

        # Extract status
        status = (
            train_data.get("status") or
            train_data.get("running_status") or
            train_data.get("message") or
            ""
        )
        if not status:
            if delay == 0:
                status = "On Time"
            elif delay > 0:
                status = f"Running Late by {delay} min"
            else:
                status = f"Running Early by {abs(delay)} min"

        # Extract next station
        next_station = (
            train_data.get("next_station_name") or
            train_data.get("nextStation") or
            train_data.get("next_station") or
            "N/A"
        )

        # Extract times
        last_time = (
            train_data.get("current_station_time") or
            train_data.get("lastStationTime") or
            train_data.get("last_station_time") or
            current_station.get("time", "") if isinstance(current_station, dict) else ""
        )

        eta = (
            train_data.get("eta") or
            train_data.get("etaNextStation") or
            train_data.get("next_station_eta") or
            ""
        )

        # Extract source/destination
        source = (
            train_data.get("source") or
            train_data.get("from") or
            train_data.get("source_station") or
            ""
        )
        destination = (
            train_data.get("destination") or
            train_data.get("to") or
            train_data.get("dest_station") or
            ""
        )

        return ToolResult(
            success=True,
            data={
                "train_number": train_number,
                "train_name": train_name,
                "running_status": status,
                "delay_minutes": delay,
                "last_station": last_station_name,
                "last_station_time": last_time,
                "next_station": next_station,
                "eta_next_station": eta,
                "source": source,
                "destination": destination,
            },
            error=None,
            tool_name="railway_train_status",
        )
    elif response.status_code == 404:
        return ToolResult(
            success=False,
            data=None,
            error=f"Train {train_number} not found or not running on this date",
            tool_name="railway_train_status",
        )
    elif response.status_code in [401, 403]:
        return ToolResult(
            success=False,
            data=None,
            error="Train status API subscription required or invalid API key",
            tool_name="railway_train_status",
        )
    elif response.status_code == 429:
        return ToolResult(
            success=False,
            data=None,
            error="API rate limit exceeded. Please try again later.",
            tool_name="railway_train_status",
        )
    else:
        return ToolResult(
            success=False,
            data=None,
            error=f"API returned status {response.status_code}",
            tool_name="railway_train_status",
        )


def get_train_status(train_number: str, date: Optional[str] = None) -> ToolResult:
    """
    Get live train running status from RapidAPI.

    Args:
        train_number: Train number (usually 5 digits)
        date: Journey date in YYYYMMDD format (optional, defaults to today)

    Returns:
        ToolResult with train status or error
    """
    if not train_number:
        return ToolResult(
            success=False,
            data=None,
            error="Train number is required",
            tool_name="railway_train_status",
        )

    if not settings.RAILWAY_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Railway API key not configured. Get one from RapidAPI.",
            tool_name="railway_train_status",
        )

    if not date:
        date = datetime.now().strftime("%Y%m%d")
    elif "-" in date:
        date = date.replace("-", "")

    try:
        with httpx.Client(timeout=30.0) as client:
            return _make_train_status_request(train_number, date, client)
    except httpx.TimeoutException:
        return ToolResult(
            success=False,
            data=None,
            error="Request timed out. Please try again.",
            tool_name="railway_train_status",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="railway_train_status",
        )


async def get_pnr_status_async(pnr: str) -> ToolResult:
    """Async version of get_pnr_status."""
    if not pnr or len(pnr) != 10 or not pnr.isdigit():
        return ToolResult(
            success=False,
            data=None,
            error="Invalid PNR format. Must be 10 digits.",
            tool_name="railway_pnr",
        )

    if not settings.RAILWAY_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Railway API key not configured. Get one from RapidAPI.",
            tool_name="railway_pnr",
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await _make_pnr_request_async(pnr, client)
    except httpx.TimeoutException:
        return ToolResult(
            success=False,
            data=None,
            error="Request timed out. Please try again.",
            tool_name="railway_pnr",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="railway_pnr",
        )


async def get_train_status_async(
    train_number: str, date: Optional[str] = None
) -> ToolResult:
    """Async version of get_train_status."""
    if not train_number:
        return ToolResult(
            success=False,
            data=None,
            error="Train number is required",
            tool_name="railway_train_status",
        )

    if not settings.RAILWAY_API_KEY:
        return ToolResult(
            success=False,
            data=None,
            error="Railway API key not configured. Get one from RapidAPI.",
            tool_name="railway_train_status",
        )

    if not date:
        date = datetime.now().strftime("%Y%m%d")
    elif "-" in date:
        date = date.replace("-", "")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await _make_train_status_request_async(train_number, date, client)
    except httpx.TimeoutException:
        return ToolResult(
            success=False,
            data=None,
            error="Request timed out. Please try again.",
            tool_name="railway_train_status",
        )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            error=str(e),
            tool_name="railway_train_status",
        )
