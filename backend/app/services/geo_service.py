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
        )
    }

    @classmethod
    def find_location(
        cls,
        name: str
    ) -> GeoLocation | None:

        key = name.strip().lower()

        return cls.LOCATIONS.get(key)