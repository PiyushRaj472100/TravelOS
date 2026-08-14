from app.services.destination_service import (
    DestinationService
)


print("=" * 60)
print("TRAVELOS DESTINATION SERVICE TEST")
print("=" * 60)


service = DestinationService()


print()
print("Searching destination: Tokyo")


try:

    places = service.search_destinations(
        "Tokyo"
    )

except Exception as e:

    print()
    print("DESTINATION SEARCH FAILED")
    print("Error:", e)
    raise


print()
print("=" * 60)
print("RESULTS")
print("=" * 60)


print()
print(
    f"Places returned: {len(places)}"
)


for index, place in enumerate(
    places[:10],
    start=1
):

    print()

    print(
        f"--- PLACE {index} ---"
    )

    print(
        "Name:",
        place.name
    )

    print(
        "Type:",
        place.place_type
    )

    print(
        "Country:",
        place.country
    )

    print(
        "Latitude:",
        place.latitude
    )

    print(
        "Longitude:",
        place.longitude
    )

    print(
        "Map:",
        place.map_url
    )

    print(
        "Source ID:",
        place.source_id
    )


print()
print("=" * 60)
print("DESTINATION SERVICE TEST SUCCESS")
print("=" * 60)