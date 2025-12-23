from __future__ import annotations

from typing import Optional, Dict, Any, List

import httpx

from app.logger import logger


class UberService:
    """
    Uber API service for ride estimates, ride requests, and trip history.

    Note: Uber API requires OAuth 2.0 authentication and approved developer access.
    See: https://developer.uber.com/docs/riders/introduction
    """

    def __init__(
        self,
        *,
        access_token: str = None,
        client_id: str = None,
        client_secret: str = None,
        sandbox: bool = True,
    ):
        self.access_token = access_token or ""
        self.client_id = client_id or ""
        self.client_secret = client_secret or ""
        self.sandbox = sandbox
        self.base_url = (
            "https://sandbox-api.uber.com/v1.2"
            if sandbox
            else "https://api.uber.com/v1.2"
        )
        self.available = bool(self.access_token)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept-Language": "en_US",
        }

    async def get_products(
        self,
        latitude: float,
        longitude: float,
    ) -> str:
        """
        Get available Uber products/ride types at a location.

        Args:
            latitude: Pickup location latitude
            longitude: Pickup location longitude
        """
        if not self.available:
            return "Uber service is not configured. Please connect Uber in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/products",
                    headers=self._get_headers(),
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to get Uber products: {resp.status_code} - {resp.text}"

                data = resp.json()
                products = data.get("products", [])

                if not products:
                    return "No Uber products available at this location."

                results = []
                for product in products:
                    name = product.get("display_name", "Unknown")
                    description = product.get("description", "")
                    capacity = product.get("capacity", "Unknown")
                    price_details = product.get("price_details", {})
                    base = price_details.get("base", 0)
                    per_minute = price_details.get("cost_per_minute", 0)
                    per_km = price_details.get("cost_per_distance", 0)
                    currency = price_details.get("currency_code", "INR")

                    results.append(
                        f"- {name}\n"
                        f"  {description}\n"
                        f"  Capacity: {capacity} | Base: {currency} {base}\n"
                        f"  Per minute: {currency} {per_minute} | Per km: {currency} {per_km}"
                    )

                return "Available Uber Products:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("uber_products_error", error=str(exc))
            return f"Uber error: {exc}"

    async def get_price_estimate(
        self,
        start_latitude: float,
        start_longitude: float,
        end_latitude: float,
        end_longitude: float,
    ) -> str:
        """
        Get price estimates for a trip.

        Args:
            start_latitude: Pickup latitude
            start_longitude: Pickup longitude
            end_latitude: Dropoff latitude
            end_longitude: Dropoff longitude
        """
        if not self.available:
            return "Uber service is not configured. Please connect Uber in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/estimates/price",
                    headers=self._get_headers(),
                    params={
                        "start_latitude": start_latitude,
                        "start_longitude": start_longitude,
                        "end_latitude": end_latitude,
                        "end_longitude": end_longitude,
                    },
                )

                if resp.status_code != 200:
                    return f"Failed to get price estimate: {resp.status_code}"

                data = resp.json()
                prices = data.get("prices", [])

                if not prices:
                    return "No price estimates available for this route."

                results = []
                for price in prices:
                    name = price.get("display_name", "Unknown")
                    estimate = price.get("estimate", "Unknown")
                    duration = price.get("duration", 0) // 60
                    distance = price.get("distance", 0)
                    surge = price.get("surge_multiplier", 1.0)

                    surge_text = f" (Surge: {surge}x)" if surge > 1.0 else ""

                    results.append(
                        f"- {name}: {estimate}{surge_text}\n"
                        f"  Distance: {distance:.1f} km | Duration: ~{duration} mins"
                    )

                return "Uber Price Estimates:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("uber_price_error", error=str(exc))
            return f"Uber error: {exc}"

    async def get_time_estimate(
        self,
        latitude: float,
        longitude: float,
        product_id: Optional[str] = None,
    ) -> str:
        """
        Get ETA for Uber drivers at a location.

        Args:
            latitude: Pickup latitude
            longitude: Pickup longitude
            product_id: Optional specific product ID
        """
        if not self.available:
            return "Uber service is not configured. Please connect Uber in Settings."

        try:
            params: Dict[str, Any] = {
                "start_latitude": latitude,
                "start_longitude": longitude,
            }
            if product_id:
                params["product_id"] = product_id

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/estimates/time",
                    headers=self._get_headers(),
                    params=params,
                )

                if resp.status_code != 200:
                    return f"Failed to get time estimate: {resp.status_code}"

                data = resp.json()
                times = data.get("times", [])

                if not times:
                    return "No Uber drivers available at this location."

                results = []
                for time_est in times:
                    name = time_est.get("display_name", "Unknown")
                    estimate = time_est.get("estimate", 0) // 60

                    results.append(f"- {name}: ~{estimate} mins away")

                return "Uber Driver ETAs:\n\n" + "\n".join(results)

        except Exception as exc:
            logger.error("uber_time_error", error=str(exc))
            return f"Uber error: {exc}"

    async def get_ride_history(self, limit: int = 10) -> str:
        """Get user's recent ride history."""
        if not self.available:
            return "Uber service is not configured. Please connect Uber in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/history",
                    headers=self._get_headers(),
                    params={"limit": limit},
                )

                if resp.status_code != 200:
                    return f"Failed to get ride history: {resp.status_code}"

                data = resp.json()
                history = data.get("history", [])

                if not history:
                    return "No ride history found."

                results = []
                for ride in history:
                    start_city = ride.get("start_city", {}).get("display_name", "Unknown")
                    distance = ride.get("distance", 0)
                    start_time = ride.get("start_time", "Unknown")
                    end_time = ride.get("end_time", "Unknown")
                    status = ride.get("status", "Unknown")

                    results.append(
                        f"- {start_city} | {distance:.1f} km\n"
                        f"  Start: {start_time} | End: {end_time}\n"
                        f"  Status: {status}"
                    )

                return "Recent Uber Rides:\n\n" + "\n\n".join(results)

        except Exception as exc:
            logger.error("uber_history_error", error=str(exc))
            return f"Uber error: {exc}"

    async def request_ride(
        self,
        product_id: str,
        start_latitude: float,
        start_longitude: float,
        end_latitude: float,
        end_longitude: float,
        start_address: Optional[str] = None,
        end_address: Optional[str] = None,
    ) -> str:
        """
        Request an Uber ride.

        Note: This only works in sandbox mode unless you have production access.
        """
        if not self.available:
            return "Uber service is not configured. Please connect Uber in Settings."

        if not self.sandbox:
            return "Ride requests are only available in sandbox mode for this integration."

        try:
            payload: Dict[str, Any] = {
                "product_id": product_id,
                "start_latitude": start_latitude,
                "start_longitude": start_longitude,
                "end_latitude": end_latitude,
                "end_longitude": end_longitude,
            }
            if start_address:
                payload["start_address"] = start_address
            if end_address:
                payload["end_address"] = end_address

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/requests",
                    headers=self._get_headers(),
                    json=payload,
                )

                if resp.status_code not in (200, 201, 202):
                    return f"Failed to request ride: {resp.status_code} - {resp.text}"

                data = resp.json()
                request_id = data.get("request_id", "Unknown")
                status = data.get("status", "Unknown")
                eta = data.get("eta", "Unknown")

                return (
                    f"Uber Ride Requested!\n"
                    f"Request ID: {request_id}\n"
                    f"Status: {status}\n"
                    f"ETA: {eta} minutes"
                )

        except Exception as exc:
            logger.error("uber_request_error", error=str(exc))
            return f"Uber error: {exc}"

    async def cancel_ride(self, request_id: str) -> str:
        """Cancel an active ride request."""
        if not self.available:
            return "Uber service is not configured. Please connect Uber in Settings."

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.delete(
                    f"{self.base_url}/requests/{request_id}",
                    headers=self._get_headers(),
                )

                if resp.status_code == 204:
                    return f"Ride {request_id} cancelled successfully."
                else:
                    return f"Failed to cancel ride: {resp.status_code}"

        except Exception as exc:
            logger.error("uber_cancel_error", error=str(exc))
            return f"Uber error: {exc}"
