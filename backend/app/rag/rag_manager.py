from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.metadata_store import MetadataStore
from app.rag.ingestion import RAGIngestionService
from app.rag.retriever import RAGRetriever
from app.rag.rag_services import RAGService
from app.rag.document import RAGDocument

from app.services.llm_service import LLMService


class RAGManager:

    def __init__(
        self,
        llm_service: LLMService
    ):

        # ---------------------------------------------
        # 1. Embedding service
        # ---------------------------------------------

        self.embedding_service = (
            EmbeddingService()
        )

        # Gemini embedding dimension
        dimension = 3072

        # ---------------------------------------------
        # 2. Vector store
        # ---------------------------------------------

        self.vector_store = VectorStore(
            dimension=dimension
        )

        # ---------------------------------------------
        # 3. Metadata store
        # ---------------------------------------------

        self.metadata_store = MetadataStore()

        # ---------------------------------------------
        # 4. Ingestion service
        # ---------------------------------------------

        self.ingestion = RAGIngestionService(
            embedding_service=(
                self.embedding_service
            ),
            vector_store=self.vector_store,
            metadata_store=self.metadata_store
        )

        # ---------------------------------------------
        # 5. Load development knowledge
        # ---------------------------------------------

        self._load_documents()

        # ---------------------------------------------
        # 6. Retriever
        # ---------------------------------------------

        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_service=(
                self.embedding_service
            )
        )

        # ---------------------------------------------
        # 7. RAG service
        # ---------------------------------------------

        self.rag_service = RAGService(
            retriever=self.retriever,
            llm_service=llm_service
        )

    def _load_documents(self):

        documents = [

            RAGDocument(
                text="""
                Travelers should verify the current
                entry, passport and visa requirements
                before visiting a foreign destination.
                """,
                country="Country-A",
                category="entry_requirements",
                source="development",
                title="Entry Requirements"
            ),

            RAGDocument(
                text="""
                Travelers should check local
                transportation, public transit and
                regional travel options before
                beginning their journey.
                """,
                country="Country-B",
                category="transportation",
                source="development",
                title="Transportation"
            ),

            RAGDocument(
                text="""
                Travelers should check local cultural
                customs and photography restrictions
                at specific sites.
                """,
                country="Country-A",
                category="culture",
                source="development",
                title="Cultural Guidance"
            )
        ]

        for document in documents:

            self.ingestion.ingest(
                document
            )

    def get_rag_service(self) -> RAGService:

        return self.rag_service