from app.rag.rag_manager import RAGManager
from app.services.llm_service import LLMService


# ============================================
# Load RAG
# ============================================

llm_service = LLMService()

rag_manager = RAGManager(
    llm_service=llm_service
)


rag_service = (
    rag_manager.get_rag_service()
)


retriever = (
    rag_service.retriever
)


# ============================================
# Test cases
# ============================================

tests = [

    {
        "question": "What are the safety considerations?",
        "country": "Australia",
        "category": "safety"
    },

    {
        "question": "What are the visa requirements?",
        "country": "Japan",
        "category": "visa"
    },

    {
        "question": "What safety information is available?",
        "country": "United Arab Emirates",
        "category": "safety"
    },

    {
        "question": "How is transportation handled?",
        "country": "India",
        "category": "transportation"
    },

    {
        "question": "What should I pack?",
        "country": "France",
        "category": "packing"
    }
]


# ============================================
# Run tests
# ============================================

for number, test in enumerate(
    tests,
    start=1
):

    print(
        "\n========================================"
    )

    print(
        f"TEST {number}"
    )

    print(
        "========================================"
    )

    print(
        "Question:",
        test["question"]
    )

    print(
        "Country:",
        test["country"]
    )

    print(
        "Category:",
        test["category"]
    )


    results = retriever.search(
        query=test["question"],
        country=test["country"],
        category=test["category"],
        top_k=3
    )


    print(
        "\nRESULTS:"
    )


    if not results:

        print(
            "No results found."
        )

        continue


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
            "Score:",
            result["score"]
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
        