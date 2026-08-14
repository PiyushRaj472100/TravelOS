from app.services.llm_service import LLMService
from app.rag.query_analyzer import QueryAnalyzer


llm = LLMService()

analyzer = QueryAnalyzer(
    llm
)


questions = [
    "What should I pack for Paris in December?",
    "What are the entry requirements for my trip?",
    "How can I travel around Italy cheaply?",
    "What is the current exchange rate from INR to EUR?",
    "What is the weather in Tokyo tomorrow?",
]


for question in questions:

    print("\n==============================")
    print("QUESTION:")
    print(question)

    result = analyzer.analyze(
        question
    )

    print("\nANALYZED:")
    print(result.model_dump())