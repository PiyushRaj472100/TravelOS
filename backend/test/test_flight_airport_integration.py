from app.services.flight_service import FlightService


flight_service = FlightService()


print("=" * 60)
print("FLIGHT + AIRPORT SERVICE INTEGRATION TEST")
print("=" * 60)


try:

    results = flight_service.search_flights(
        origin="London",
        destination="Dubai",
        departure_date="2026-09-15",
        passengers=1,
        cabin_class="economy",
        max_connections=1
    )

    print()
    print(
        f"Flights returned: {len(results)}"
    )

    for flight in results[:5]:

        print()
        print(
            "Provider:",
            flight.provider
        )

        print(
            "Route:",
            flight.origin,
            "->",
            flight.destination
        )

        print(
            "Departure:",
            flight.departure
        )

        print(
            "Arrival:",
            flight.arrival
        )

        print(
            "Duration:",
            flight.duration_minutes,
            "minutes"
        )

        print(
            "Stops:",
            flight.stops
        )

        print(
            "Price:",
            flight.price,
            flight.currency
        )

        print(
            "ID:",
            flight.option_id
        )


    print()
    print("=" * 60)
    print("TEST PASSED")
    print("=" * 60)


except Exception as e:

    print()
    print("=" * 60)
    print("TEST FAILED")
    print("=" * 60)

    print(
        type(e).__name__,
        ":",
        e
    )