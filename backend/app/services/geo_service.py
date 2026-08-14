import requests
from app.models.geo import GeoLocation


class GeoService:

    LOCATIONS = {
        "japan": GeoLocation(
            name="Japan",
            country="Japan",
            latitude=36.2048,
            longitude=138.2529,
            location_type="country"
        ),

        "tokyo": GeoLocation(
            name="Tokyo",
            country="Japan",
            region="Kanto",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
            location_type="city"
        ),

        "kyoto": GeoLocation(
            name="Kyoto",
            country="Japan",
            region="Kansai",
            city="Kyoto",
            latitude=35.0116,
            longitude=135.7681,
            location_type="city"
        ),

        "osaka": GeoLocation(
            name="Osaka",
            country="Japan",
            region="Kansai",
            city="Osaka",
            latitude=34.6937,
            longitude=135.5023,
            location_type="city"
        ),

        "seoul": GeoLocation(
            name="Seoul",
            country="South Korea",
            region="Seoul",
            city="Seoul",
            latitude=37.5665,
            longitude=126.9780,
            location_type="city"
        ),

        "singapore": GeoLocation(
            name="Singapore",
            country="Singapore",
            latitude=1.3521,
            longitude=103.8198,
            location_type="country"
        ),

        "paris": GeoLocation(
            name="Paris",
            country="France",
            region="Île-de-France",
            city="Paris",
            latitude=48.8566,
            longitude=2.3522,
            location_type="city"
        ),

        "london": GeoLocation(
            name="London",
            country="United Kingdom",
            region="England",
            city="London",
            latitude=51.5074,
            longitude=-0.1278,
            location_type="city"
        ),

        "new york": GeoLocation(
            name="New York",
            country="United States",
            region="New York",
            city="New York",
            latitude=40.7128,
            longitude=-74.0060,
            location_type="city"
        ),

        "dubai": GeoLocation(
            name="Dubai",
            country="United Arab Emirates",
            region="Dubai",
            city="Dubai",
            latitude=25.2048,
            longitude=55.2708,
            location_type="city"
        ),

        "bali": GeoLocation(
            name="Bali",
            country="Indonesia",
            region="Bali",
            city="Denpasar",
            latitude=-8.4095,
            longitude=115.1889,
            location_type="region"
        ),

        "rome": GeoLocation(
            name="Rome",
            country="Italy",
            region="Lazio",
            city="Rome",
            latitude=41.9028,
            longitude=12.4964,
            location_type="city"
        ),

        "cairo": GeoLocation(
            name="Cairo",
            country="Egypt",
            region="Cairo",
            city="Cairo",
            latitude=30.0444,
            longitude=31.2357,
            location_type="city"
        ),

        "sydney": GeoLocation(
            name="Sydney",
            country="Australia",
            region="New South Wales",
            city="Sydney",
            latitude=-33.8688,
            longitude=151.2093,
            location_type="city"
        )
    }

    _cache: dict[str, GeoLocation] = {}

    @classmethod
    def find_location(
        cls,
        name: str
    ) -> GeoLocation | None:

        if not name:
            return None

        key = name.strip().lower()

        # 1. Check hardcoded dictionary
        if key in cls.LOCATIONS:
            return cls.LOCATIONS[key]

        # 2. Check dynamic cache
        if key in cls._cache:
            return cls._cache[key]

        # 3. Dynamic lookup via Open-Meteo Geocoding
        try:
            resp = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": name,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                },
                timeout=5
            )
            if resp.ok:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    loc_data = results[0]
                    geo = GeoLocation(
                        name=loc_data.get("name", name),
                        country=loc_data.get("country", ""),
                        region=loc_data.get("admin1", ""),
                        city=loc_data.get("name", name),
                        latitude=loc_data.get("latitude"),
                        longitude=loc_data.get("longitude"),
                        location_type="city"
                    )
                    cls._cache[key] = geo
                    return geo
        except Exception:
            pass

        return None