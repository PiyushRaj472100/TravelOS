from app.services.flight_ranker import FlightRanker
from app.services.flight_service import FlightService


print("=" * 60)
print("FLIGHT RANKER TEST")
print("=" * 60)


flight_service = FlightService()


flights = flight_service.search_flights(
    origin="DEL",
    destination="DXB",
    departure_date="2026-09-15",
    passengers=1,
    cabin_class="economy",
    max_connections=1
)


print()
print(
    f"Total flights received: {len(flights)}"
)


# -------------------------------------------------
# Cheapest
# -------------------------------------------------

cheapest = FlightRanker.cheapest(
    flights,
    limit=5
)

print()
print("CHEAPEST")
print("-" * 40)

for flight in cheapest:

    print(
        flight.provider,
        "|",
        flight.price,
        flight.currency,
        "|",
        flight.duration_minutes,
        "min |",
        flight.stops,
        "stops"
    )


# -------------------------------------------------
# Fastest
# -------------------------------------------------

fastest = FlightRanker.fastest(
    flights,
    limit=5
)

print()
print("FASTEST")
print("-" * 40)

for flight in fastest:

    print(
        flight.provider,
        "|",
        flight.price,
        flight.currency,
        "|",
        flight.duration_minutes,
        "min |",
        flight.stops,
        "stops"
    )


# -------------------------------------------------
# Fewest stops
# -------------------------------------------------

fewest = FlightRanker.fewest_stops(
    flights,
    limit=5
)

print()
print("FEWEST STOPS")
print("-" * 40)

for flight in fewest:

    print(
        flight.provider,
        "|",
        flight.price,
        flight.currency,
        "|",
        flight.duration_minutes,
        "min |",
        flight.stops,
        "stops"
    )


# -------------------------------------------------
# Balanced
# -------------------------------------------------

balanced = FlightRanker.balanced(
    flights,
    limit=5
)

print()
print("BALANCED")
print("-" * 40)

for flight in balanced:

    print(
        flight.provider,
        "|",
        flight.price,
        flight.currency,
        "|",
        flight.duration_minutes,
        "min |",
        flight.stops,
        "stops"
    )


print()
print("=" * 60)
print("FLIGHT RANKER TEST COMPLETED")
print("=" * 60)