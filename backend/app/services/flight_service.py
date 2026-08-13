import os
from datetime import datetime

import requests
import os
from dotenv import load_dotenv

load_dotenv()

from app.models.transportation import TransportationOption
from app.services.airport_service import AirportService
from app.services.date_service import DateService


class FlightService:

    BASE_URL = "https://api.duffel.com"

    def __init__(
        self,
        api_token: str | None = None
    ):

        self.api_token = (
            api_token
            or os.getenv("DUFFEL_API_TOKEN")
        )

        if not self.api_token:
            raise ValueError(
                "DUFFEL_API_TOKEN is not configured."
            )

        self.headers = {
            "Authorization": (
                f"Bearer {self.api_token}"
            ),
            "Duffel-Version": "v2",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.airport_service = AirportService()


    # =================================================
    # Search Flights
    # =================================================

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        passengers: int = 1,
        cabin_class: str = "economy",
        max_connections: int = 1
    ) -> list[TransportationOption]:
        
        
        
        
        origin_location = (self.airport_service.resolve(
            origin
        ))
        
        destination_location = (self.airport_service.resolve(
            destination
        ))
        
        origin_code = origin_location.code
        destination_code = destination_location.code
        
        departure_date = DateService.normalize(
            departure_date
        )

        # Build Duffel request 

        payload = {
            "data": {

                "cabin_class": cabin_class,

                "slices": [
                    {
                        "origin": origin_code,
                        "destination": destination_code,
                        "departure_date": departure_date
                    }
                ],

                "passengers": [
                    {
                        "type": "adult"
                    }
                    for _ in range(passengers)
                ],

                "max_connections": max_connections
            }
        }

        response = requests.post(
            f"{self.BASE_URL}/air/offer_requests",
            headers=self.headers,
            json=payload,
            timeout=60
        )

        # Raise an exception for HTTP errors
        if not response.ok:
            print()
          
            print("Duffel API Error:")
            
            
            print("Status:", response.status_code)
            print("Response:", response.text)
            print()
            print("Request Payload:", payload)
            print()
            response.raise_for_status()
            

        data = response.json()

        return self._parse_offers(
            data
        )


    # =================================================
    # Parse Duffel Offers
    # =================================================

    def _parse_offers(
        self,
        response_data: dict
    ) -> list[TransportationOption]:

        offers = (
            response_data
            .get("data", {})
            .get("offers", [])
        )

        results = []

        for offer in offers:

            slices = offer.get(
                "slices",
                []
            )

            if not slices:
                continue

            # -----------------------------------------
            # For now we handle the first slice
            # -----------------------------------------

            first_slice = slices[0]

            segments = first_slice.get(
                "segments",
                []
            )

            if not segments:
                continue

            first_segment = segments[0]
            last_segment = segments[-1]

            # -----------------------------------------
            # Origin / destination
            # -----------------------------------------

            origin = (
                first_segment
                .get("origin", {})
                .get("iata_code")
            )

            destination = (
                last_segment
                .get("destination", {})
                .get("iata_code")
            )

            # -----------------------------------------
            # Departure / arrival
            # -----------------------------------------

            departure = self._parse_datetime(
                first_segment.get(
                    "departing_at"
                )
            )

            arrival = self._parse_datetime(
                last_segment.get(
                    "arriving_at"
                )
            )

            # -----------------------------------------
            # Duration
            # -----------------------------------------

            duration_minutes = None

            if departure and arrival:

                duration = (
                    arrival - departure
                )

                duration_minutes = int(
                    duration.total_seconds() / 60
                )

            # -----------------------------------------
            # Number of stops
            # -----------------------------------------

            stops = max(
                len(segments) - 1,
                0
            )

            # -----------------------------------------
            # Airline
            # -----------------------------------------

            provider = (
                offer
                .get("owner", {})
                .get("name")
            )

            # -----------------------------------------
            # Price
            # -----------------------------------------

            price = None

            try:
                price = float(
                    offer.get(
                        "total_amount"
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                pass

            currency = offer.get(
                "total_currency"
            )

            # -----------------------------------------
            # Create common model
            # -----------------------------------------

            option = TransportationOption(

                type="flight",

                provider=provider,

                origin=origin or "",

                destination=destination or "",

                departure=departure,

                arrival=arrival,

                duration_minutes=(
                    duration_minutes
                ),

                stops=stops,

                price=price,

                currency=currency,

                booking_url=None,

                option_id=offer.get(
                    "id"
                )
            )

            results.append(
                option
            )

        return results


    # =================================================
    # Datetime helper
    # =================================================

    @staticmethod
    def _parse_datetime(
        value: str | None
    ) -> datetime | None:

        if not value:
            return None

        try:

            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00"
                )
            )

        except ValueError:

            return None
        
    def close(self):
        """
        Close any resources if needed.
        """
        pass