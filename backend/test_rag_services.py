from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.metadata_store import MetadataStore
from app.rag.ingestion import RAGIngestionService
from app.rag.retriever import RAGRetriever
from app.rag.rag_services import RAGService
from app.rag.document import RAGDocument

from app.services.llm_service import LLMService

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


document = RAGDocument(
    text="""
    Travelers should verify current entry,
    passport and visa requirements before
    traveling to the destination.
    """,
    country="Country-A",
    category="entry_requirements",
    source="development",
    title="Entry Requirements"
)

ingestion.ingest(document)


retriever = RAGRetriever(
    vector_store=vector_store,
    embedding_service=embedding_service
)


llm = LLMService()


rag = RAGService(
    retriever=retriever,
    llm_service=llm
)


result = rag.answer(
    question="What should I check before entering?",
    country="Country-A",
    category="entry_requirements"
)


print("\n===== ANSWER =====")

print(result["answer"])


print("\n===== SOURCES =====")

for source in result["sources"]:

    print(source)