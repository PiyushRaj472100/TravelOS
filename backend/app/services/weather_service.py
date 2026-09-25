import time
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
        self._coords_cache: dict[str, dict] = {}
        self._weather_cache: dict[str, tuple[float, dict]] = {}


    # =================================================
    # Find city coordinates
    # =================================================

    def _get_coordinates(
        self,
        city: str
    ) -> dict:

        key = city.strip().lower()
        if key in self._coords_cache:
            return self._coords_cache[key]

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

        res = {
            "name": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "country": location.get("country"),
            "timezone": location.get("timezone")
        }
        self._coords_cache[key] = res
        return res


    # =================================================
    # Get current weather
    # =================================================

    def get_current_weather(
        self,
        city: str
    ) -> dict:

        city_key = city.strip().lower()
        now = time.time()
        if city_key in self._weather_cache:
            cache_time, cached_val = self._weather_cache[city_key]
            if now - cache_time < 900:
                return cached_val

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

        result = {
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
        self._weather_cache[city_key] = (now, result)
        return result


    # =================================================
    # Close
    # =================================================

    def close(self):
        pass