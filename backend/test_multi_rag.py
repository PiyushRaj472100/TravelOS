from app.models.travel_state import TravelState

# Use the SAME RAG initialization/imports
# from your existing test_rag_services.py
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.metadata_store import MetadataStore
from app.rag.ingestion import RAGIngestionService
from app.rag.retriever import RAGRetriever
from app.rag.rag_services import RAGService
from app.services.llm_service import LLMService
from app.rag.document import RAGDocument


# -------------------------------------------------
# 1. Create services
# -------------------------------------------------

embedding_service = EmbeddingService()

vector_store = VectorStore(
    dimension=3072
)

metadata_store = MetadataStore()

ingestion = RAGIngestionService(
    embedding_service=embedding_service,
    vector_store=vector_store,
    metadata_store=metadata_store
)


# -------------------------------------------------
# 2. Add test knowledge for multiple countries
# -------------------------------------------------

documents = [
    # France
    {
        "text": """
        France has an extensive railway network.
        High-speed TGV trains connect major cities.
        Paris has an extensive metro system.
        """,
        "country": "France",
        "city": "Paris",
        "category": "transportation",
        "title": "France Transportation"
    },

    # Italy
    {
        "text": """
        Italy has extensive regional and high-speed
        railway services. Major cities such as Rome,
        Milan and Florence are connected by rail.
        """,
        "country": "Italy",
        "city": "Rome",
        "category": "transportation",
        "title": "Italy Transportation"
    },

    # Switzerland
    {
        "text": """
        Switzerland is known for its extensive and
        reliable railway network. Trains connect
        major cities and scenic mountain regions.
        """,
        "country": "Switzerland",
        "city": "Zurich",
        "category": "transportation",
        "title": "Switzerland Transportation"
    }
]


# -------------------------------------------------
# 3. Ingest documents
# -------------------------------------------------

for item in documents:

    document = RAGDocument(
        text=item["text"],
        country=item["country"],
        city=item["city"],
        category=item["category"],
        title=item["title"],
        source="test"
    )

    ingestion.ingest(document)


# -------------------------------------------------
# 4. Create retriever
# -------------------------------------------------

retriever = RAGRetriever(
    vector_store=vector_store,
    embedding_service=embedding_service
)


# -------------------------------------------------
# 5. Create LLM service
# -------------------------------------------------

llm = LLMService()


# -------------------------------------------------
# 6. Create RAG service
# -------------------------------------------------

rag = RAGService(
    retriever=retriever,
    llm_service=llm
)


# -------------------------------------------------
# 7. Create multi-country TravelState
# -------------------------------------------------

state = TravelState(
    destinations=[
        "Paris",
        "Rome",
        "Zurich"
    ],

    countries=[
        "France",
        "Italy",
        "Switzerland"
    ],

    cities=[
        "Paris",
        "Rome",
        "Zurich"
    ],

    duration_days=12,

    budget=200000,

    currency="INR",

    interests=[
        "photography",
        "culture"
    ]
)


# -------------------------------------------------
# 8. Ask a question
# -------------------------------------------------

question = (
    "What should I know about transportation "
    "during my trip?"
)


result = rag.answer_with_state(
    question=question,
    state=state
)


# -------------------------------------------------
# 9. Display answer
# -------------------------------------------------

print("\n==============================")
print("ANSWER")
print("==============================")

print(result["answer"])


print("\n==============================")
print("SOURCES")
print("==============================")

for source in result["sources"]:

    print(
        f"{source['country']} | "
        f"{source['city']} | "
        f"{source['title']} | "
        f"score={source['score']}"
    )