from app.rag.query import RAGQuery
from app.rag.query_router import QueryRouter

from app.services.live_query_service import (
    LiveQueryService
)


# -------------------------------------------------
# 1. Create the query
# -------------------------------------------------

query = RAGQuery(
    question=(
        "What is the current exchange rate "
        "from INR to EUR?"
    ),
    category="currency",
    needs_live_data=True
)


# -------------------------------------------------
# 2. Create router
# -------------------------------------------------

router = QueryRouter()


# -------------------------------------------------
# 3. Determine route
# -------------------------------------------------

route = router.route(
    query
)

print("\n==============================")
print("QUERY ROUTER")
print("==============================")

print(
    f"Category: {query.category}"
)

print(
    f"Needs live data: "
    f"{query.needs_live_data}"
)

print(
    f"Route: {route}"
)


# -------------------------------------------------
# 4. Execute live route
# -------------------------------------------------

if route == "live":

    live_service = LiveQueryService()

    try:

        result = live_service.handle(
            query
        )

        print("\n==============================")
        print("LIVE RESULT")
        print("==============================")

        print(
            f"Base currency: "
            f"{result['base_currency']}"
        )

        print(
            f"Target currency: "
            f"{result['target_currency']}"
        )

        print(
            f"Live rate: "
            f"{result['rate']}"
        )

    finally:

        live_service.close()