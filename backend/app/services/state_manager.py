from app.models.travel_state import TravelState
from app.models.travel_extraction import TravelExtraction


class StateManager:

    @staticmethod
    def update_state(
        state: TravelState,
        extraction: TravelExtraction
    ) -> TravelState:

        # Simple fields
        if extraction.origin is not None:
            state.origin = extraction.origin

        if extraction.duration_days is not None:
            state.duration_days = extraction.duration_days

        if extraction.start_date is not None:
            state.start_date = extraction.start_date

        if extraction.end_date is not None:
            state.end_date = extraction.end_date

        if extraction.travelers is not None:
            state.travelers = extraction.travelers

        if extraction.traveler_type is not None:
            state.traveler_type = extraction.traveler_type

        if extraction.budget is not None:
            state.budget = extraction.budget

        if extraction.currency is not None:
            state.currency = extraction.currency

        if extraction.pace is not None:
            state.pace = extraction.pace

        if extraction.accommodation_preference is not None:
            state.accommodation_preference = (
                extraction.accommodation_preference
            )

        if extraction.transportation_preference is not None:
            state.transportation_preference = (
                extraction.transportation_preference
            )

        # List fields
        if extraction.destinations:
            state.destinations = list(
                dict.fromkeys(
                    state.destinations + extraction.destinations
                )
            )

        if extraction.interests:
            state.interests = list(
                dict.fromkeys(
                    state.interests + extraction.interests
                )
            )

        if extraction.food_preferences:
            state.food_preferences = list(
                dict.fromkeys(
                    state.food_preferences + extraction.food_preferences
                )
            )

        return state