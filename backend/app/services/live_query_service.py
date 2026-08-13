import re

from app.services.currency_services import (
    CurrencyService
)

from app.services.weather_service import (
    WeatherService
)


class LiveQueryService:

    def __init__(
        self,
        currency_service: CurrencyService | None = None,
        weather_service: WeatherService | None = None
    ):

        # ---------------------------------------------
        # Currency
        # ---------------------------------------------

        self.currency_service = (
            currency_service
            if currency_service
            else CurrencyService()
        )


        # ---------------------------------------------
        # Weather
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

            "base_currency": (
                base_currency.upper()
            ),

            "target_currency": (
                target_currency.upper()
            ),

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
    # Main live query handler
    # =================================================

    def handle(
        self,
        query
    ) -> dict:

        # ---------------------------------------------
        # WEATHER
        # ---------------------------------------------

        if query.category == "weather":

            if not query.cities:

                raise ValueError(
                    "A city is required for weather information."
                )

            city = query.cities[0]

            return self.get_weather(
                city
            )


        # ---------------------------------------------
        # CURRENCY
        # ---------------------------------------------

        if query.category == "currency":

            base_currency, target_currency = (
                self._extract_currencies(
                    query.question
                )
            )

            return self.get_currency_rate(
                base_currency=base_currency,
                target_currency=target_currency
            )


        # ---------------------------------------------
        # Unsupported live category
        # ---------------------------------------------

        raise ValueError(
            f"Unsupported live category: "
            f"{query.category}"
        )


    # =================================================
    # Extract currencies from question
    # =================================================

    def _extract_currencies(
        self,
        question: str
    ) -> tuple[str, str]:

        # ---------------------------------------------
        # Common currency codes
        # ---------------------------------------------

        currency_codes = {
            "USD",
            "EUR",
            "GBP",
            "INR",
            "JPY",
            "AUD",
            "CAD",
            "CHF",
            "CNY",
            "SGD",
            "AED",
            "NZD",
            "HKD",
            "KRW",
            "THB",
            "MYR",
            "IDR",
            "ZAR",
            "TRY",
            "SAR"
        }


        # ---------------------------------------------
        # Find currency codes
        # ---------------------------------------------

        found = re.findall(
            r"\b[A-Z]{3}\b",
            question.upper()
        )


        found = [
            currency
            for currency in found
            if currency in currency_codes
        ]


        # ---------------------------------------------
        # Require two currencies
        # ---------------------------------------------

        if len(found) >= 2:

            return (
                found[0],
                found[1]
            )


        # ---------------------------------------------
        # Currency symbols / names
        # ---------------------------------------------

        question_lower = question.lower()

        currency_names = {
            "rupees": "INR",
            "rupee": "INR",
            "dollars": "USD",
            "dollar": "USD",
            "euros": "EUR",
            "euro": "EUR",
            "pounds": "GBP",
            "pound": "GBP",
            "yen": "JPY"
        }


        detected = []

        for name, code in currency_names.items():

            if name in question_lower:

                detected.append(code)


        if len(detected) >= 2:

            return (
                detected[0],
                detected[1]
            )


        # ---------------------------------------------
        # Cannot determine currencies
        # ---------------------------------------------

        raise ValueError(
            "Could not determine the base and "
            "target currencies from the question. "
            "Please specify two currencies, such as "
            "'INR to EUR'."
        )


    # =================================================
    # Close services
    # =================================================

    def close(self):

        self.currency_service.close()

        self.weather_service.close()