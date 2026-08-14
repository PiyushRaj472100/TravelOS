"""Hotel search agent — resolves destination then searches RouteStack hotels."""

from datetime import date, timedelta

from app.models.travel_state import TravelState
from app.services.hotel_service import HotelService
from app.services.destination_service import DestinationService


class HotelAgent:

    def __init__(self):
        self.hotel_service = HotelService()
        self.destination_service = DestinationService()


    # =================================================
    # Search Hotels for Trip
    # =================================================

    def search(
        self,
        state: TravelState,
        destination_name: str | None = None
    ) -> dict:
        """
        Search hotels for the current trip state.

        Resolves destination coords via DestinationService,
        then searches RouteStack for hotels.
        """

        # Determine target destination
        target = (
            destination_name
            or (state.destinations[0] if state.destinations else None)
        )

        if not target:
            return {
                "agent": "hotel",
                "status": "error",
                "message": "No destination specified for hotel search.",
                "hotels": []
            }


        # -------------------------------------------------
        # Resolve destination coordinates & RouteStack ID
        # -------------------------------------------------

        destination_id = None
        lat = None
        lng = None

        # First try from state.locations for coordinates
        for loc in state.locations:
            if loc.name.lower() == target.lower():
                lat = loc.latitude
                lng = loc.longitude
                break

        # Query DestinationService for RouteStack destination_id & coordinates
        try:
            places = self.destination_service.search_destinations(target)
            if places:
                best = places[0]
                destination_id = best.source_id
                if lat is None or lng is None:
                    lat = best.latitude
                    lng = best.longitude
        except Exception as e:
            print(f"[HotelAgent] DestinationService error: {e}")


        if lat is None or lng is None:
            return {
                "agent": "hotel",
                "status": "error",
                "message": (
                    f"Could not resolve coordinates for '{target}'. "
                    "Please try a more specific city name."
                ),
                "hotels": []
            }


        # -------------------------------------------------
        # Determine check-in / check-out dates
        # -------------------------------------------------

        from app.services.date_service import DateService
        from datetime import datetime

        if state.start_date:
            check_in = DateService.normalize(state.start_date)
        else:
            check_in = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

        if state.end_date:
            check_out = DateService.normalize(state.end_date)
        else:
            duration = state.duration_days or 7
            try:
                ci_date = datetime.strptime(check_in, "%Y-%m-%d").date()
                check_out = (ci_date + timedelta(days=duration)).strftime("%Y-%m-%d")
            except Exception:
                check_out = (date.today() + timedelta(days=37)).strftime("%Y-%m-%d")


        # -------------------------------------------------
        # Currency
        # -------------------------------------------------

        currency = state.currency or "USD"


        # -------------------------------------------------
        # Adults
        # -------------------------------------------------

        adults = state.travelers or 2


        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        try:
            hotels = self.hotel_service.search_hotels(
                destination_id=destination_id or "",
                lat=lat,
                lng=lng,
                check_in=check_in,
                check_out=check_out,
                adults=adults,
                currency=currency,
                room_count=1
            )

            return {
                "agent": "hotel",
                "status": "done",
                "destination": target,
                "check_in": check_in,
                "check_out": check_out,
                "adults": adults,
                "hotels": hotels
            }

        except Exception as e:
            print(f"[HotelAgent] Hotel search error: {e}")
            return {
                "agent": "hotel",
                "status": "error",
                "message": f"Hotel search failed: {str(e)}",
                "hotels": []
            }
