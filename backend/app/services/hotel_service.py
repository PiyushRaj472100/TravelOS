"""
HotelService — searches hotels via RouteStack API.

Uses the same HMAC-SHA256 authentication pattern as DestinationService.
The full RouteStack hotel search was proven in test_routestack_hotels.py.
"""

import os
import time
import hmac
import hashlib
import base64
import secrets
from datetime import date, timedelta

import requests
from dotenv import load_dotenv


load_dotenv()


class HotelService:

    BASE_URL = os.getenv(
        "ROUTESTACK_BASE_URL",
        "https://evolvemcp.routestack.ai"
    )

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None
    ):

        self.api_key = (
            api_key
            or os.getenv("ROUTESTACK_API_KEY")
        )

        self.api_secret = (
            api_secret
            or os.getenv("ROUTESTACK_API_SECRET")
        )

        if not self.api_key:
            raise ValueError(
                "ROUTESTACK_API_KEY is not configured."
            )

        if not self.api_secret:
            raise ValueError(
                "ROUTESTACK_API_SECRET is not configured."
            )


    # =================================================
    # HMAC Authentication (same as DestinationService)
    # =================================================

    def _get_partner_token(self) -> str:

        timestamp = int(time.time())

        nonce = secrets.token_urlsafe(24)

        message = (
            f"{self.api_key}:"
            f"{timestamp}:"
            f"{nonce}"
        )

        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).digest()

        hmac_signature = (
            base64.urlsafe_b64encode(signature)
            .decode("utf-8")
            .rstrip("=")
        )

        response = requests.post(
            f"{self.BASE_URL}/mcp/auth/partner-token",
            json={
                "apiKey": self.api_key,
                "timestamp": timestamp,
                "nonce": nonce,
                "hmac": hmac_signature
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["token"]


    # =================================================
    # Search Hotels
    # =================================================

    def search_hotels(
        self,
        destination_id: str,
        lat: float,
        lng: float,
        check_in: str,
        check_out: str,
        adults: int = 2,
        currency: str = "USD",
        room_count: int = 1
    ) -> list[dict]:
        """
        Search hotels via RouteStack.

        Args:
            destination_id: RouteStack destination ID
            lat: Destination latitude
            lng: Destination longitude
            check_in: ISO date string YYYY-MM-DD
            check_out: ISO date string YYYY-MM-DD
            adults: Number of adult travelers
            currency: Currency code (USD, EUR, GBP, etc.)
            room_count: Number of rooms

        Returns:
            List of hotel dicts
        """

        token = self._get_partner_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "checkIn": check_in,
            "checkOut": check_out,
            "destinationId": str(destination_id),
            "destinationType": str(destination_id),
            "lat": lat,
            "long": lng,
            "roomCount": room_count,
            "currency": currency,
            "rooms": [
                {
                    "adults": adults,
                    "children": 0,
                    "childAges": []
                }
            ]
        }

        response = requests.post(
            f"{self.BASE_URL}/mcp/hotel/search-hotels",
            headers=headers,
            json=payload,
            timeout=60
        )

        if not response.ok:
            print(f"RouteStack hotel error: {response.status_code} {response.text}")
            response.raise_for_status()

        data = response.json()

        return self._parse_hotels(data)


    # =================================================
    # Parse Hotel Results
    # =================================================

    def _parse_hotels(self, data: dict) -> list[dict]:

        result = data.get("result", {})

        if isinstance(result, dict):
            hotels_raw = result.get("result") or result.get("hotels") or []
        elif isinstance(result, list):
            hotels_raw = result
        else:
            return []

        hotels = []

        for item in hotels_raw:

            if not isinstance(item, dict):
                continue

            # Price info
            price_info = item.get("price", {}) or {}

            price = None
            currency = "USD"
            if price_info:
                try:
                    price = float(
                        price_info.get("publishedRate")
                        or price_info.get("amount")
                        or 0
                    )
                    currency = price_info.get("currency", "USD")
                except (TypeError, ValueError):
                    pass

            # Facilities
            facilities = item.get("facilities", []) or []
            if isinstance(facilities, list):
                facility_names = [
                    f.get("name", "") if isinstance(f, dict) else str(f)
                    for f in facilities[:5]
                ]
            else:
                facility_names = []

            hotel = {
                "id": item.get("id") or item.get("hotelId"),
                "name": item.get("name") or item.get("hotelName", ""),
                "provider": item.get("provider"),
                "stars": item.get("starRating") or item.get("stars"),
                "price": price,
                "currency": currency,
                "published_rate": price_info.get("publishedRate"),
                "savings": price_info.get("savings"),
                "distance": item.get("distance"),
                "image": item.get("image") or item.get("thumbnail"),
                "chain": item.get("chain"),
                "refundable": item.get("refundable"),
                "breakfast_included": item.get("breakfastIncluded"),
                "facilities": facility_names,
                "address": item.get("address"),
                "latitude": (
                    item.get("coordinates", {}) or {}
                ).get("lat"),
                "longitude": (
                    item.get("coordinates", {}) or {}
                ).get("long"),
            }

            hotels.append(hotel)

        # Sort by price
        hotels.sort(
            key=lambda h: h.get("price") or 999999
        )

        return hotels[:20]  # Return top 20
