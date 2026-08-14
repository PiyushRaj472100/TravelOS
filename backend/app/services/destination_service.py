import os
import time
import hmac
import hashlib
import base64
import secrets

import requests
from dotenv import load_dotenv

from app.models.destination import DestinationPlace


load_dotenv()


class DestinationService:

    BASE_URL = os.getenv(
        "ROUTESTACK_BASE_URL",
        "https://evolvemcp.routestack.ai"
    )


    # =================================================
    # Initialization
    # =================================================

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None
    ):

        self.api_key = (
            api_key
            or os.getenv(
                "ROUTESTACK_API_KEY"
            )
        )

        self.api_secret = (
            api_secret
            or os.getenv(
                "ROUTESTACK_API_SECRET"
            )
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
    # Authentication
    # =================================================

    def _get_partner_token(self) -> str:

        timestamp = int(
            time.time()
        )

        nonce = secrets.token_urlsafe(
            24
        )

        message = (
            f"{self.api_key}:"
            f"{timestamp}:"
            f"{nonce}"
        )

        signature = hmac.new(
            self.api_secret.encode(
                "utf-8"
            ),
            message.encode(
                "utf-8"
            ),
            hashlib.sha256
        ).digest()

        hmac_signature = (
            base64.urlsafe_b64encode(
                signature
            )
            .decode("utf-8")
            .rstrip("=")
        )

        response = requests.post(
            f"{self.BASE_URL}"
            "/mcp/auth/partner-token",

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
    # Search Destinations
    # =================================================

    def search_destinations(
        self,
        query: str
    ) -> list[DestinationPlace]:

        token = self._get_partner_token()


        headers = {
            "Authorization": (
                f"Bearer {token}"
            ),

            "Content-Type": (
                "application/json"
            )
        }


        # ---------------------------------------------
        # RouteStack destination search payload
        # ---------------------------------------------

        payload = {
            "query": query,
            "type": "DESTINATION"
        }


        # ---------------------------------------------
        # Correct RouteStack endpoint
        # ---------------------------------------------

        response = requests.post(

            f"{self.BASE_URL}"
            "/mcp/hotel/search-destinations",

            headers=headers,

            json=payload,

            timeout=60
        )


        response.raise_for_status()


        data = response.json()


        return self._parse_results(
            data
        )


    # =================================================
    # Parse Destination Results
    # =================================================

    def _parse_results(
        self,
        data: dict
    ) -> list[DestinationPlace]:

        # ---------------------------------------------
        # First result level
        # ---------------------------------------------

        results = data.get(
            "result",
            []
        )


        # ---------------------------------------------
        # Handle nested result
        # ---------------------------------------------

        if isinstance(
            results,
            dict
        ):

            results = results.get(
                "result",
                []
            )


        if not isinstance(
            results,
            list
        ):

            return []


        places = []


        # =================================================
        # Process each destination
        # =================================================

        for item in results:

            if not isinstance(
                item,
                dict
            ):

                continue


            # ---------------------------------------------
            # Name
            # ---------------------------------------------

            name = (
                item.get(
                    "fullName"
                )
                or item.get(
                    "name"
                )
            )


            if not name:

                continue


            # ---------------------------------------------
            # Type
            # ---------------------------------------------

            place_type = (
                item.get(
                    "type"
                )
                or "place"
            )


            # ---------------------------------------------
            # Country
            # ---------------------------------------------

            country = item.get(
                "country"
            )


            # ---------------------------------------------
            # Coordinates
            # ---------------------------------------------

            coordinates = item.get(
                "coordinates",
                {}
            )


            if not isinstance(
                coordinates,
                dict
            ):

                coordinates = {}


            latitude = coordinates.get(
                "lat"
            )


            longitude = coordinates.get(
                "long"
            )


            # ---------------------------------------------
            # Source ID
            # ---------------------------------------------

            source_id = item.get(
                "id"
            )


            # ---------------------------------------------
            # Build map URL
            # ---------------------------------------------

            map_url = (
                self._build_map_url(
                    latitude,
                    longitude
                )
            )


            # ---------------------------------------------
            # Create model
            # ---------------------------------------------

            place = DestinationPlace(

                name=name,

                place_type=place_type,

                country=country,

                latitude=latitude,

                longitude=longitude,

                source="routestack",

                source_id=(
                    str(source_id)
                    if source_id is not None
                    else None
                ),

                map_url=map_url
            )


            places.append(
                place
            )


        return places


    # =================================================
    # Google Maps URL
    # =================================================

    @staticmethod
    def _build_map_url(
        latitude: float | None,
        longitude: float | None
    ) -> str | None:

        if (
            latitude is None
            or longitude is None
        ):

            return None


        return (
            "https://www.google.com/maps/search/"
            f"?api=1&query="
            f"{latitude},{longitude}"
        )