from app.models.travel_state import TravelState


class TravelStateService:

    # =================================================
    # Update Travel State
    # =================================================

    @staticmethod
    def update(
        state: TravelState,
        extraction: dict
    ) -> TravelState:

        # ---------------------------------------------
        # Destination
        # ---------------------------------------------

        if extraction.get("origin"):
            state.origin = extraction["origin"]

        if extraction.get("destination"):
            state.destination = extraction["destination"]

        if extraction.get("destinations"):
            state.destinations = (
                extraction["destinations"]
            )

        if extraction.get("countries"):
            state.countries = (
                extraction["countries"]
            )

        if extraction.get("regions"):
            state.regions = (
                extraction["regions"]
            )

        if extraction.get("cities"):
            state.cities = (
                extraction["cities"]
            )


        # ---------------------------------------------
        # Dates
        # ---------------------------------------------

        if extraction.get("start_date"):
            state.start_date = (
                extraction["start_date"]
            )

        if extraction.get("end_date"):
            state.end_date = (
                extraction["end_date"]
            )

        if extraction.get("duration_days") is not None:
            state.duration_days = (
                extraction["duration_days"]
            )


        # ---------------------------------------------
        # Travelers
        # ---------------------------------------------

        if extraction.get("travelers") is not None:
            state.travelers = (
                extraction["travelers"]
            )


        # ---------------------------------------------
        # Budget
        # ---------------------------------------------

        if extraction.get("budget") is not None:
            state.budget = (
                extraction["budget"]
            )

        if extraction.get("budget_currency"):
            state.budget_currency = (
                extraction["budget_currency"]
            )


        # ---------------------------------------------
        # Preferences
        # ---------------------------------------------

        if extraction.get("travel_style"):
            state.travel_style = (
                extraction["travel_style"]
            )

        if extraction.get(
            "accommodation_preference"
        ):
            state.accommodation_preference = (
                extraction[
                    "accommodation_preference"
                ]
            )

        if extraction.get("interests"):
            state.interests = list(
                dict.fromkeys(
                    state.interests
                    + extraction["interests"]
                )
            )

        if extraction.get(
            "dietary_preferences"
        ):
            state.dietary_preferences = list(
                dict.fromkeys(
                    state.dietary_preferences
                    + extraction[
                        "dietary_preferences"
                    ]
                )
            )


        # ---------------------------------------------
        # Transportation
        # ---------------------------------------------

        if extraction.get(
            "preferred_transportation"
        ):
            state.preferred_transportation = (
                extraction[
                    "preferred_transportation"
                ]
            )

        if extraction.get("cabin_class"):
            state.cabin_class = (
                extraction["cabin_class"]
            )


        return state


    # =================================================
    # Calculate Missing Information
    # =================================================

    @staticmethod
    def get_missing_information(
        state: TravelState
    ) -> list[str]:

        missing = []


        if not state.destination:
            missing.append(
                "destination"
            )


        if not state.duration_days:
            missing.append(
                "duration"
            )


        if not state.travelers:
            missing.append(
                "number of travelers"
            )


        if state.budget is None:
            missing.append(
                "budget"
            )


        if not state.start_date:
            missing.append(
                "start date"
            )


        return missing


    # =================================================
    # Check Planning Completion
    # =================================================

    @staticmethod
    def update_completion(
        state: TravelState
    ) -> TravelState:

        missing = (
            TravelStateService
            .get_missing_information(
                state
            )
        )

        state.missing_information = missing

        state.planning_complete = (
            len(missing) == 0
        )

        return state