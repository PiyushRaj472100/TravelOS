from app.services.llm_service import LLMService
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.query_router import QueryRouter


llm = LLMService()

analyzer = QueryAnalyzer(
    llm
)

router = QueryRouter()


questions = [
    "What should I know about local culture?",
    "What are the entry requirements?",
    "What is the current exchange rate from INR to EUR?",
    "What is the weather in Tokyo tomorrow?",
    "How can I travel around Italy?",
]


for question in questions:

    query = analyzer.analyze(
        question
    )

    destination = router.route(
        query
    )

    print("\n============================")
    print("Question:", question)
    print("Category:", query.category)
    print("Live data:", query.needs_live_data)
    print("Route:", destination)