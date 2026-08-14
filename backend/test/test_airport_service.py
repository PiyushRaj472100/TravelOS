from app.services.airport_service import AirportService


locations = [
    "Delhi",
    "Mumbai",
    "London",
    "Heathrow",
    "Dubai",
    "Tokyo",
    "Paris",
    "Sydney",
    "Singapore",
    "Johannesburg",
    "New York",
    "LHR",
    "DXB"
]


for location in locations:

    try:

        result = AirportService.resolve(
            location
        )

        print(
            f"{location} -> "
            f"{result.code} | "
            f"{result.location_type}"
        )

    except ValueError as e:

        print(
            f"{location} -> ERROR: {e}"
        )