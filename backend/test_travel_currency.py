from app.models.travel_state import TravelState

from app.services.travel_currency_service import (
    TravelCurrencyService
)


state = TravelState(
    countries=[
        "France",
        "Switzerland",
        "Italy"
    ],
    budget=200000,
    currency="INR"
)


service = TravelCurrencyService()


try:

    results = service.convert_budget_for_trip(
        state
    )

    print("\n==============================")
    print("TRAVEL BUDGET CONVERSION")
    print("==============================")

    print(
        f"Original budget: "
        f"{state.budget} {state.currency}"
    )

    print(
        f"Countries: "
        f"{state.countries}"
    )

    print("\nConversions:")

    for result in results:

        print(
            f"{result.from_currency} "
            f"→ "
            f"{result.to_currency}: "
            f"{result.converted_amount:.2f}"
        )

finally:

    service.close()