from app.models.travel_state import TravelState

from app.services.currency_services import CurrencyService
from app.services.country_currency_services import (
    CountryCurrencyService
)


class TravelCurrencyService:

    def __init__(
        self,
        currency_service: CurrencyService | None = None,
        country_currency_service: (
            CountryCurrencyService | None
        ) = None
    ):

        self.currency_service = (
            currency_service
            if currency_service
            else CurrencyService()
        )

        self.country_currency_service = (
            country_currency_service
            if country_currency_service
            else CountryCurrencyService()
        )

    def convert_budget_for_trip(
        self,
        state: TravelState
    ):

        if state.budget is None:

            raise ValueError(
                "Travel budget is not available."
            )

        if not state.currency:

            raise ValueError(
                "Travel budget currency is not available."
            )

        countries = state.countries

        if not countries:

            raise ValueError(
                "No destination countries are available."
            )

        currencies = (
            self.country_currency_service
            .get_currencies(countries)
        )

        results = (
            self.currency_service
            .convert_trip_budget(
                budget=state.budget,
                budget_currency=state.currency,
                target_currencies=currencies
            )
        )

        return results

    def close(self):

        self.currency_service.close()