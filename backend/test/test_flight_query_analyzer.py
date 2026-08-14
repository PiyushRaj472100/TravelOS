from app.services.llm_service import LLMService
from app.rag.query_analyzer import QueryAnalyzer


llm_service = LLMService()

analyzer = QueryAnalyzer(
    llm_service
)


questions = [

    "Find flights from London to Dubai on February 15.",

    "Are there flights from Delhi to Tokyo tomorrow?",

    "Find cheap flights from Paris to Rome.",

    "Show me business class flights from London to Dubai.",

    "I want to visit Japan for 10 days.",

    "What is the weather in Tokyo?",

    "What is the current exchange rate from INR to EUR?"

]


for question in questions:

    print()
    print("=" * 60)
    print("QUESTION:")
    print(question)
    print("=" * 60)

    result = analyzer.analyze(
        question
    )

    print(
        result.model_dump()
    )