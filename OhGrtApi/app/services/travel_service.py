"""
Travel Service

Provides Indian Railways information:
- PNR Status
- Train Running Status
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.logger import logger


class TravelService:
    """Service for Indian Railways travel information."""

    def __init__(self, api_key: str):
        """
        Initialize the travel service.

        Args:
            api_key: API key for the railway service
        """
        self.api_key = api_key
        self.base_url = "https://indianrailapi.com/api/v2"

    async def get_pnr_status(self, pnr: str) -> Dict[str, Any]:
        """
        Get PNR status from Indian Railways.

        Args:
            pnr: 10-digit PNR number

        Returns:
            Dictionary with success status and PNR details or error
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Railway API key not configured",
            }

        if not pnr or len(pnr) != 10 or not pnr.isdigit():
            return {
                "success": False,
                "error": "Invalid PNR format. Must be 10 digits.",
            }

        try:
            url = f"{self.base_url}/PNRCheck/apikey/{self.api_key}/PNRNumber/{pnr}"

            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data.get("ResponseCode") == "200":
                    pnr_data = data.get("Result", {})
                    return {
                        "success": True,
                        "data": {
                            "pnr": pnr,
                            "train_number": pnr_data.get("TrainNo", "N/A"),
                            "train_name": pnr_data.get("TrainName", "N/A"),
                            "from_station": pnr_data.get("From", "N/A"),
                            "to_station": pnr_data.get("To", "N/A"),
                            "journey_date": pnr_data.get("Doj", "N/A"),
                            "class": pnr_data.get("Class", "N/A"),
                            "chart_prepared": pnr_data.get("ChartPrepared", False),
                            "passengers": [
                                {
                                    "booking_status": p.get("BookingStatus", "N/A"),
                                    "current_status": p.get("CurrentStatus", "N/A"),
                                    "coach": p.get("Coach", ""),
                                    "berth": p.get("Berth", ""),
                                }
                                for p in pnr_data.get("PassengerStatus", [])
                            ],
                        },
                    }
                else:
                    error = data.get("Message", "Failed to fetch PNR status")
                    logger.warning(f"PNR API error for {pnr}: {error}")
                    return {
                        "success": False,
                        "error": error,
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"PNR API HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
            }
        except Exception as e:
            logger.error(f"PNR service error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_train_status(self, train_number: str) -> Dict[str, Any]:
        """
        Get train running status.

        Args:
            train_number: 4-5 digit train number

        Returns:
            Dictionary with success status and train details or error
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Railway API key not configured",
            }

        if not train_number or not (4 <= len(train_number) <= 5) or not train_number.isdigit():
            return {
                "success": False,
                "error": "Invalid train number format. Must be 4-5 digits.",
            }

        try:
            # Get today's date for running status
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")

            url = f"{self.base_url}/livetrainstatus/apikey/{self.api_key}/trainnumber/{train_number}/date/{today}"

            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if data.get("ResponseCode") == "200":
                    train_data = data.get("Result", {})
                    current_station = train_data.get("CurrentStation", {})

                    return {
                        "success": True,
                        "data": {
                            "train_number": train_number,
                            "train_name": train_data.get("TrainName", "Unknown"),
                            "current_station": {
                                "name": current_station.get("StationName", "Unknown"),
                                "delay": current_station.get("DelayInMinutes", 0),
                                "eta": current_station.get("ETA", ""),
                            },
                            "recent_stops": [
                                {
                                    "name": stop.get("StationName", ""),
                                    "scheduled_arrival": stop.get("ScheduledArrival", ""),
                                    "actual_arrival": stop.get("ActualArrival", ""),
                                }
                                for stop in train_data.get("TrainRoute", [])[:5]
                            ],
                        },
                    }
                else:
                    error = data.get("Message", "Failed to fetch train status")
                    logger.warning(f"Train API error for {train_number}: {error}")
                    return {
                        "success": False,
                        "error": error,
                    }

        except httpx.HTTPStatusError as e:
            logger.error(f"Train API HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
            }
        except Exception as e:
            logger.error(f"Train service error: {e}")
            return {
                "success": False,
                "error": str(e),
            }


# Factory function for creating the service
_travel_service_instance: Optional[TravelService] = None


def get_travel_service(api_key: str) -> TravelService:
    """
    Get or create a TravelService instance.

    Args:
        api_key: API key for the railway service

    Returns:
        TravelService instance
    """
    global _travel_service_instance
    if _travel_service_instance is None or _travel_service_instance.api_key != api_key:
        _travel_service_instance = TravelService(api_key)
    return _travel_service_instance


# Sync wrapper functions for use in LangGraph nodes
def get_pnr_status(pnr: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for PNR status.

    Args:
        pnr: 10-digit PNR number

    Returns:
        Dictionary with success status and PNR details or error
    """
    import asyncio
    from app.config import get_settings

    settings = get_settings()
    api_key = getattr(settings, 'railway_api_key', '') or getattr(settings, 'RAILWAY_API_KEY', '')

    service = get_travel_service(api_key)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're in an async context
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(service.get_pnr_status(pnr))
    else:
        return asyncio.run(service.get_pnr_status(pnr))


def get_train_status(train_number: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for train status.

    Args:
        train_number: 4-5 digit train number
        date: Optional date string (not used, kept for compatibility)

    Returns:
        Dictionary with success status and train details or error
    """
    import asyncio
    from app.config import get_settings

    settings = get_settings()
    api_key = getattr(settings, 'railway_api_key', '') or getattr(settings, 'RAILWAY_API_KEY', '')

    service = get_travel_service(api_key)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're in an async context
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(service.get_train_status(train_number))
    else:
        return asyncio.run(service.get_train_status(train_number))
