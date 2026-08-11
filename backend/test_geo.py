from app.models.travel_state import TravelState
from app.models.travel_extraction import TravelExtraction
from app.services.state_manager import StateManager


state = TravelState()


extraction = TravelExtraction(
    destinations=[
        "Tokyo",
        "Kyoto",
        "Osaka"
    ]
)


state = StateManager.update_state(
    state,
    extraction
)


print("\n===== ROUTE =====")

for location in state.route:

    print(
        f"{location.name} "
        f"({location.latitude}, {location.longitude})"
    )


print("\n===== TRAVEL LEGS =====")

for leg in state.travel_legs:

    print(
        f"{leg.order}. "
        f"{leg.from_location.name} "
        f"→ "
        f"{leg.to_location.name}"
    )