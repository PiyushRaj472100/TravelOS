from app.services.llm_service import LLMService
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.query_router import QueryRouter
from app.services.live_query_service import LiveQueryService


llm_service = LLMService()

analyzer = QueryAnalyzer(
    llm_service
)

router = QueryRouter()

live_service = LiveQueryService()


question = (
    "Find flights from Delhi to Dubai "
    "on September 15"
)


print("=" * 60)
print("TRAVELOS FLIGHT PIPELINE TEST")
print("=" * 60)

print()
print("QUESTION:")
print(question)


# -------------------------------------------------
# 1. Analyze
# -------------------------------------------------

query = analyzer.analyze(
    question
)

print()
print("QUERY ANALYSIS")
print("-" * 40)

print(
    "Category:",
    query.category
)

print(
    "Origin:",
    query.origin
)

print(
    "Destination:",
    query.destination
)

print(
    "Departure date:",
    query.departure_date
)

print(
    "Passengers:",
    query.passengers
)

print(
    "Cabin:",
    query.cabin_class
)

print(
    "Max connections:",
    query.max_connections
)

print(
    "Needs live:",
    query.needs_live_data
)


# -------------------------------------------------
# 2. Route
# -------------------------------------------------

route = router.route(
    query
)

print()
print("ROUTE")
print("-" * 40)

print(route)


# -------------------------------------------------
# 3. Live service
# -------------------------------------------------

if route != "live":

    raise ValueError(
        f"Expected live route, got: {route}"
    )


result = live_service.handle(
    query
)


# -------------------------------------------------
# 4. Results
# -------------------------------------------------

print()
print("FLIGHT RESULTS")
print("-" * 40)

print(
    f"Found {len(result)} flights."
)


for index, flight in enumerate(
    result[:5],
    start=1
):

    print()
    print(
        f"Flight {index}"
    )

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


print()
print("=" * 60)
print("FLIGHT PIPELINE TEST PASSED")
print("=" * 60)