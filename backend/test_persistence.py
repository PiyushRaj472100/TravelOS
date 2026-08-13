from app.rag.rag_manager import RAGManager
from app.services.llm_service import LLMService


# ============================================
# Load persistent RAG database
# ============================================

llm_service = LLMService()

rag_manager = RAGManager(
    llm_service=llm_service
)

rag_service = (
    rag_manager.get_rag_service()
)


# ============================================
# Direct retrieval test
# ============================================

results = rag_service.retriever.search(
    query="What are the safety considerations for Australia?",
    top_k=5,
    country="Australia",
    category="safety"
)


print("\n========================================")
print("RETRIEVED SOURCES")
print("========================================")


for result in results:

    document = result["document"]

    print(
        "\nTitle:",
        document.title
    )

    print(
        "Country:",
        document.country
    )

    print(
        "Category:",
        document.category
    )

    print(
        "Source:",
        document.source
    )

    print(
        "URL:",
        document.source_url
    )

    print(
        "Fallback:",
        document.fallback_search_url
    )

    print(
        "Score:",
        result["score"]
    )