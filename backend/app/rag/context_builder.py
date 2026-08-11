from app.models.travel_state import TravelState


class RAGContextBuilder:

    def build(
        self,
        state: TravelState,
        question: str
    ) -> dict:

        return {
            "question": question,

            "origin": state.origin,

            "destinations": state.destinations,
            "countries": state.countries,
            "regions": state.regions,
            "cities": state.cities,

            "interests": state.interests,
            "travel_style": state.travel_style,
            "pace": state.pace,

            "accommodation_preference":
                state.accommodation_preference,

            "transportation_preference":
                state.transportation_preference,

            "food_preferences":
                state.food_preferences,

            "duration_days":
                state.duration_days,

            "travelers":
                state.travelers,

            "traveler_type":
                state.traveler_type,

            "budget":
                state.budget,

            "currency":
                state.currency,
        }