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
    _poi_cache: dict[str, tuple[float, float]] = {
        # Common iconic landmarks for instant pinpoint lookup
        "eiffel tower": (48.8584, 2.2945),
        "louvre": (48.8606, 2.3376),
        "louvre museum": (48.8606, 2.3376),
        "notre-dame": (48.8530, 2.3499),
        "notre dame": (48.8530, 2.3499),
        "musee d'orsay": (48.8599, 2.3265),
        "orsay museum": (48.8599, 2.3265),
        "arc de triomphe": (48.8738, 2.2950),
        "sacre-coeur": (48.8867, 2.3431),
        "champs-elysees": (48.8698, 2.3075),
        "senso-ji": (35.7148, 139.7967),
        "shibuya crossing": (35.6595, 139.7005),
        "tokyo skytree": (35.7101, 139.8107),
        "tokyo tower": (35.6586, 139.7454),
        "fushimi inari": (34.9671, 135.7727),
        "kinkaku-ji": (35.0394, 135.7292),
        "colosseum": (41.8902, 12.4922),
        "vatican": (41.9029, 12.4534),
        "trevi fountain": (41.9009, 12.4833),
        "big ben": (51.5007, -0.1246),
        "london eye": (51.5033, -0.1195),
        "tower of london": (51.5081, -0.0759),
        "burj khalifa": (25.1972, 55.2744),
        "dubai mall": (25.1985, 55.2796),
        "statue of liberty": (40.6892, -74.0445),
        "central park": (40.7851, -73.9683),
        "empire state building": (40.7484, -73.9857),
    }

    @classmethod
    def geocode_poi(cls, name: str, city: str = "") -> tuple[float, float] | None:
        """Geocode landmark, attraction, or point of interest using cache and Geoapify."""
        if not name:
            return None

        clean_name = name.lower().strip()
        # Clean noise words from tour titles
        for noise in ["timed-entry tour", "walking tour", "masterpieces exploration", "guided tour", "skip-the-line", "experience", "admission ticket", "day trip"]:
            clean_name = clean_name.replace(noise, "").strip()

        # Check static POI cache
        for k, coords in cls._poi_cache.items():
            if k in clean_name or clean_name in k:
                return coords

        cache_key = f"{clean_name}|{city.lower()}"
        if cache_key in cls._poi_cache:
            return cls._poi_cache[cache_key]

        # Use Geoapify API if configured
        import os
        geoapify_key = os.getenv("GEOAPIFY_API_KEY")
        if geoapify_key:
            try:
                search_query = f"{clean_name} {city}".strip()
                resp = requests.get(
                    "https://api.geoapify.com/v1/geocode/search",
                    params={
                        "text": search_query,
                        "apiKey": geoapify_key,
                        "limit": 1
                    },
                    timeout=4
                )
                if resp.ok:
                    features = resp.json().get("features", [])
                    if features:
                        coords = features[0].get("geometry", {}).get("coordinates", [])
                        if len(coords) >= 2:
                            lng, lat = float(coords[0]), float(coords[1])
                            cls._poi_cache[cache_key] = (lat, lng)
                            return (lat, lng)
            except Exception as e:
                print(f"[GeoService] Geoapify POI error: {e}")

        return None

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