from app.services.llm_service import LLMService
from app.rag.query_analyzer import QueryAnalyzer


llm_service = LLMService()

analyzer = QueryAnalyzer(
    llm_service
)


questions = [

    "Find flights from Delhi to Dubai on September 15",

    "Are there flights from Mumbai to London tomorrow?",

    "Find a direct flight from Paris to Tokyo",

    "I need a business class flight from Delhi to Singapore",

]


for question in questions:

    print("=" * 60)

    print(
        "QUESTION:",
        question
    )

    result = analyzer.analyze(
        question
    )

    print()

    print(
        "CATEGORY:",
        result.category
    )

    print(
        "ORIGIN:",
        result.origin
    )

    print(
        "DESTINATION:",
        result.destination
    )

    print(
        "DATE:",
        result.departure_date
    )

    print(
        "PASSENGERS:",
        result.passengers
    )

    print(
        "CABIN:",
        result.cabin_class
    )

    print(
        "MAX CONNECTIONS:",
        result.max_connections
    )

    print(
        "LIVE:",
        result.needs_live_data
    )

    print()