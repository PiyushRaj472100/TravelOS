from dotenv import load_dotenv

load_dotenv()

from app.services.flight_service import FlightService




print()
print("=" * 50)
print("Testing TravelOS Flight Service")
print("=" * 50)


flight_service = FlightService()


print()
print("Searching:")
print("Origin: LHR")
print("Destination: DXB")
print("Passengers: 1")
print("Cabin: Economy")
print()


try:

    flights = flight_service.search_flights(
        origin="LHR",
        destination="DXB",
        departure_date="2027-02-15",
        passengers=1,
        cabin_class="economy",
        max_connections=1
    )

    print()
    print("=" * 50)
    print(f"FLIGHTS FOUND: {len(flights)}")
    print("=" * 50)


    for index, flight in enumerate(
        flights,
        start=1
    ):

        print()
        print(f"FLIGHT {index}")
        print("-" * 40)

        print(
            "Provider:",
            flight.provider
        )

        print(
            "Route:",
            f"{flight.origin} → {flight.destination}"
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
            "Option ID:",
            flight.option_id
        )


except Exception as e:

    print()
    print("=" * 50)
    print("FLIGHT SEARCH FAILED")
    print("=" * 50)

    print(type(e).__name__)
    print(e)