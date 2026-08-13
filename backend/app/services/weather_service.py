import requests


class WeatherService:

    GEOCODING_URL = (
        "https://geocoding-api.open-meteo.com/v1/search"
    )

    WEATHER_URL = (
        "https://api.open-meteo.com/v1/forecast"
    )


    def __init__(self):

        self.timeout = 10


    # =================================================
    # Find city coordinates
    # =================================================

    def _get_coordinates(
        self,
        city: str
    ) -> dict:

        response = requests.get(
            self.GEOCODING_URL,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=self.timeout
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:

            raise ValueError(
                f"Could not find location: {city}"
            )

        location = results[0]

        return {
            "name": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "country": location.get("country"),
            "timezone": location.get("timezone")
        }


    # =================================================
    # Get current weather
    # =================================================

    def get_current_weather(
        self,
        city: str
    ) -> dict:

        location = self._get_coordinates(
            city
        )

        response = requests.get(
            self.WEATHER_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],

                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m,"
                    "wind_direction_10m"
                ),

                "timezone": "auto"
            },
            timeout=self.timeout
        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        return {
            "type": "weather",

            "city": location["name"],

            "country": location["country"],

            "timezone": location["timezone"],

            "time": current.get("time"),

            "temperature": current.get(
                "temperature_2m"
            ),

            "humidity": current.get(
                "relative_humidity_2m"
            ),

            "apparent_temperature": current.get(
                "apparent_temperature"
            ),

            "precipitation": current.get(
                "precipitation"
            ),

            "weather_code": current.get(
                "weather_code"
            ),

            "wind_speed": current.get(
                "wind_speed_10m"
            ),

            "wind_direction": current.get(
                "wind_direction_10m"
            )
        }


    # =================================================
    # Close
    # =================================================

    def close(self):
        pass