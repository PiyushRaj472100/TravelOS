import re
from app.services.flight_ranker import FlightRanker

from app.services.currency_services import (
    CurrencyService
)

from app.services.weather_service import (
    WeatherService
)

from app.services.flight_service import (
    FlightService
)


class LiveQueryService:

    def __init__(
        self,
        currency_service: CurrencyService | None = None,
        weather_service: WeatherService | None = None,
        flight_service: FlightService | None = None
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


        # ---------------------------------------------
        # Flights
        # ---------------------------------------------

        self.flight_service = (
            flight_service
            if flight_service
            else FlightService()
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
    # Flights
    # =================================================

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        passengers: int = 1,
        cabin_class: str = "economy",
        max_connections: int = 1
    ):

        return self.flight_service.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            passengers=passengers,
            cabin_class=cabin_class,
            max_connections=max_connections
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
        # FLIGHTS
        # ---------------------------------------------

        if query.category == "flight":

            if not query.origin:

                raise ValueError(
                    "An origin is required for flight search."
                )

            if not query.destination:

                raise ValueError(
                    "A destination is required for flight search."
                )

            if not query.departure_date:

                raise ValueError(
                    "A departure date is required "
                    "for flight search."
                )

            flights =  self.search_flights(
                origin=query.origin,
                destination=query.destination,
                departure_date=query.departure_date,
                passengers=(
                    query.passengers
                    if query.passengers
                    else 1
                ),
                cabin_class=(
                    query.cabin_class
                    if query.cabin_class
                    else "economy"
                ),
                max_connections=(
                    query.max_connections
                    if query.max_connections is not None
                    else 1
                )
            )
            
            # rank flights
            
            return {
                "all" : flights,
                "cheapest" : FlightRanker.cheapest(flights , limit=5),
                "fastest" : FlightRanker.fastest(flights , limit=5) , 
                "fewest_stops" : FlightRanker.fewest_stops(flights , limit=5),
                "recommended" : FlightRanker.balanced(flights , limit=5)
                
            }


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


        found = re.findall(
            r"\b[A-Z]{3}\b",
            question.upper()
        )


        found = [
            currency
            for currency in found
            if currency in currency_codes
        ]


        if len(found) >= 2:

            return (
                found[0],
                found[1]
            )


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

        self.flight_service.close()