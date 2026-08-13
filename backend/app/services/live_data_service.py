from app.services.currency_services import CurrencyService
from app.services.weather_service import WeatherService


class LiveDataService:

    def __init__(
        self,
        currency_service: CurrencyService | None = None,
        weather_service: WeatherService | None = None
    ):

        # ---------------------------------------------
        # Currency service
        # ---------------------------------------------

        self.currency_service = (
            currency_service
            if currency_service
            else CurrencyService()
        )

        # ---------------------------------------------
        # Weather service
        # ---------------------------------------------

        self.weather_service = (
            weather_service
            if weather_service
            else WeatherService()
        )


    # =================================================
    # Currency
    # =================================================

    def get_currency_rate(
        self,
        base_currency: str,
        target_currency: str
    ) -> dict:

        rate = self.currency_service.get_rate(
            base_currency=base_currency,
            target_currency=target_currency
        )

        return {
            "type": "currency",
            "base_currency": base_currency.upper(),
            "target_currency": target_currency.upper(),
            "rate": rate
        }


    # =================================================
    # Weather
    # =================================================

    def get_weather(
        self,
        city: str
    ) -> dict:

        return self.weather_service.get_current_weather(
            city
        )


    # =================================================
    # Close
    # =================================================

    def close(self):

        self.currency_service.close()

        self.weather_service.close()