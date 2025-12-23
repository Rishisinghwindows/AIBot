"""Uber API Service.

Provides ride history, price estimates, and ride status functionality.
Requires OAuth credentials stored via /uber/oauth-url flow.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from app.logger import logger


# Uber API endpoints
UBER_API_BASE = "https://api.uber.com"
UBER_PROFILE_URL = f"{UBER_API_BASE}/v1.2/me"
UBER_HISTORY_URL = f"{UBER_API_BASE}/v1.2/history"
UBER_PRODUCTS_URL = f"{UBER_API_BASE}/v1.2/products"
UBER_ESTIMATES_PRICE_URL = f"{UBER_API_BASE}/v1.2/estimates/price"
UBER_ESTIMATES_TIME_URL = f"{UBER_API_BASE}/v1.2/estimates/time"


class UberService:
    """Service for interacting with Uber API."""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Uber service.

        Args:
            access_token: OAuth access token from Uber
        """
        self.access_token = access_token
        self.available = bool(access_token)

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept-Language": "en_US",
        }

    async def get_profile(self) -> Dict[str, Any]:
        """
        Get user profile information.

        Returns:
            Dict with user profile data
        """
        if not self.available:
            return {"success": False, "error": "Uber not connected"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    UBER_PROFILE_URL,
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "data": {
                            "first_name": data.get("first_name"),
                            "last_name": data.get("last_name"),
                            "email": data.get("email"),
                            "picture": data.get("picture"),
                            "rider_id": data.get("rider_id") or data.get("uuid"),
                        },
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Uber token expired. Please reconnect."}
                else:
                    logger.error(f"Uber profile error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Uber profile exception: {e}")
            return {"success": False, "error": str(e)}

    async def get_ride_history(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        Get user's ride history.

        Args:
            limit: Maximum number of rides to return (max 50)
            offset: Offset for pagination

        Returns:
            Dict with ride history data
        """
        if not self.available:
            return {"success": False, "error": "Uber not connected"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    UBER_HISTORY_URL,
                    headers=self._get_headers(),
                    params={"limit": min(limit, 50), "offset": offset},
                )

                if response.status_code == 200:
                    data = response.json()
                    rides = []

                    for ride in data.get("history", []):
                        rides.append({
                            "ride_id": ride.get("request_id") or ride.get("uuid"),
                            "status": ride.get("status"),
                            "start_time": ride.get("start_time"),
                            "end_time": ride.get("end_time"),
                            "distance": ride.get("distance"),
                            "start_city": ride.get("start_city", {}).get("display_name"),
                            "product_id": ride.get("product_id"),
                        })

                    return {
                        "success": True,
                        "data": {
                            "rides": rides,
                            "count": data.get("count", len(rides)),
                            "offset": data.get("offset", offset),
                            "limit": data.get("limit", limit),
                        },
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Uber token expired. Please reconnect."}
                else:
                    logger.error(f"Uber history error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Uber history exception: {e}")
            return {"success": False, "error": str(e)}

    async def get_price_estimate(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
    ) -> Dict[str, Any]:
        """
        Get price estimates for a ride.

        Args:
            start_lat: Starting latitude
            start_lng: Starting longitude
            end_lat: Ending latitude
            end_lng: Ending longitude

        Returns:
            Dict with price estimates for different products
        """
        if not self.available:
            return {"success": False, "error": "Uber not connected"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    UBER_ESTIMATES_PRICE_URL,
                    headers=self._get_headers(),
                    params={
                        "start_latitude": start_lat,
                        "start_longitude": start_lng,
                        "end_latitude": end_lat,
                        "end_longitude": end_lng,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    estimates = []

                    for price in data.get("prices", []):
                        estimates.append({
                            "product_name": price.get("display_name") or price.get("localized_display_name"),
                            "estimate": price.get("estimate"),
                            "low_estimate": price.get("low_estimate"),
                            "high_estimate": price.get("high_estimate"),
                            "currency": price.get("currency_code"),
                            "duration": price.get("duration"),  # seconds
                            "distance": price.get("distance"),  # miles
                            "surge_multiplier": price.get("surge_multiplier", 1.0),
                        })

                    return {
                        "success": True,
                        "data": {
                            "estimates": estimates,
                            "start": {"lat": start_lat, "lng": start_lng},
                            "end": {"lat": end_lat, "lng": end_lng},
                        },
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Uber token expired. Please reconnect."}
                elif response.status_code == 422:
                    return {"success": False, "error": "Invalid location coordinates"}
                else:
                    logger.error(f"Uber price estimate error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Uber price estimate exception: {e}")
            return {"success": False, "error": str(e)}

    async def get_time_estimate(
        self,
        start_lat: float,
        start_lng: float,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get ETA for Uber products at a location.

        Args:
            start_lat: Starting latitude
            start_lng: Starting longitude
            product_id: Optional specific product ID

        Returns:
            Dict with time estimates for different products
        """
        if not self.available:
            return {"success": False, "error": "Uber not connected"}

        try:
            params = {
                "start_latitude": start_lat,
                "start_longitude": start_lng,
            }
            if product_id:
                params["product_id"] = product_id

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    UBER_ESTIMATES_TIME_URL,
                    headers=self._get_headers(),
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    estimates = []

                    for time in data.get("times", []):
                        estimates.append({
                            "product_name": time.get("display_name") or time.get("localized_display_name"),
                            "product_id": time.get("product_id"),
                            "eta_seconds": time.get("estimate"),  # seconds
                            "eta_minutes": round(time.get("estimate", 0) / 60, 1),
                        })

                    return {
                        "success": True,
                        "data": {
                            "estimates": estimates,
                            "location": {"lat": start_lat, "lng": start_lng},
                        },
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Uber token expired. Please reconnect."}
                else:
                    logger.error(f"Uber time estimate error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Uber time estimate exception: {e}")
            return {"success": False, "error": str(e)}

    async def get_products(
        self,
        lat: float,
        lng: float,
    ) -> Dict[str, Any]:
        """
        Get available Uber products at a location.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Dict with available products
        """
        if not self.available:
            return {"success": False, "error": "Uber not connected"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    UBER_PRODUCTS_URL,
                    headers=self._get_headers(),
                    params={
                        "latitude": lat,
                        "longitude": lng,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    products = []

                    for product in data.get("products", []):
                        products.append({
                            "product_id": product.get("product_id"),
                            "name": product.get("display_name"),
                            "description": product.get("description"),
                            "capacity": product.get("capacity"),
                            "image": product.get("image"),
                            "shared": product.get("shared", False),
                        })

                    return {
                        "success": True,
                        "data": {
                            "products": products,
                            "location": {"lat": lat, "lng": lng},
                        },
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Uber token expired. Please reconnect."}
                else:
                    logger.error(f"Uber products error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Uber products exception: {e}")
            return {"success": False, "error": str(e)}
