from app.rag.document import RAGDocument
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.metadata_store import MetadataStore
from app.rag.ingestion import RAGIngestionService
from app.rag.retriever import RAGRetriever


embedding_service = EmbeddingService()


# Gemini embedding dimension
dimension = 3072


vector_store = VectorStore(
    dimension=dimension
)

metadata_store = MetadataStore()


ingestion = RAGIngestionService(
    embedding_service=embedding_service,
    vector_store=vector_store,
    metadata_store=metadata_store
)


documents = [

    RAGDocument(
        text="""
        Travelers should verify the current entry,
        passport and visa requirements before visiting
        a foreign destination.
        """,
        country="Country-A",
        category="entry_requirements",
        source="development",
        title="Entry Requirements"
    ),

    RAGDocument(
        text="""
        Travelers should check local transportation,
        public transit and regional travel options
        before beginning their journey.
        """,
        country="Country-B",
        category="transportation",
        source="development",
        title="Transportation"
    ),

    RAGDocument(
        text="""
        Travelers should check local cultural customs
        and photography restrictions at specific sites.
        """,
        country="Country-A",
        category="culture",
        source="development",
        title="Cultural Guidance"
    )
]


for document in documents:

    ingestion.ingest(
        document
    )


retriever = RAGRetriever(
    vector_store=vector_store,
    embedding_service=embedding_service
)


results = retriever.search(
    query="What are the entry requirements?",
    country="Country-A",
    category="entry_requirements",
    top_k=3
)


print("\n===== RESULTS =====")

for result in results:

    print("\nScore:", result["score"])

    document = result["document"]

    print("Country:", document.country)
    print("Category:", document.category)
    print("Title:", document.title)
    print("Text:", document.text)