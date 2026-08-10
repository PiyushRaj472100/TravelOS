from app.models.travel_state import TravelState


class MissingInformationDetector:

    REQUIRED_FIELDS = {
        "destination": 1,
        "duration": 2,
        "budget": 3,
        "travelers": 4,
        "interests": 5
    }

    @staticmethod
    def detect(state: TravelState) -> list[str]:

        missing = []

        if not state.destinations:
            missing.append("destination")

        if state.duration_days is None:
            missing.append("duration")

        if state.budget is None:
            missing.append("budget")

        if state.travelers is None:
            missing.append("travelers")

        if not state.interests:
            missing.append("interests")

        missing.sort(
            key=lambda field:
            MissingInformationDetector.REQUIRED_FIELDS[field]
        )

        return missing

    @staticmethod
    def next_question(state: TravelState) -> str | None:

        missing = MissingInformationDetector.detect(state)

        if not missing:
            return None

        questions = {
            "destination":
                "Where would you like to travel?",

            "duration":
                "How many days would you like to travel?",

            "budget":
                "What is your approximate budget for the trip?",

            "travelers":
                "How many people will be traveling?",

            "interests":
                "What are the main things you'd like to experience on this trip?"
        }

        return questions[missing[0]]