from pathlib import Path

from app.rag.embeddings import (
    EmbeddingService
)

from app.rag.vector_store import (
    VectorStore
)

from app.rag.metadata_store import (
    MetadataStore
)

from app.rag.retriever import (
    RAGRetriever
)

from app.rag.rag_services import (
    RAGService
)


class RAGManager:

    def __init__(
        self,
        llm_service
    ):

        self.llm_service = (
            llm_service
        )


        # =============================================
        # Persistent storage paths
        # =============================================

        backend_dir = Path(__file__).resolve().parents[2]
        default_storage = backend_dir / "data" / "vector_store"
        if default_storage.exists():
            self.storage_dir = default_storage
        else:
            self.storage_dir = Path("data/vector_store").resolve()

        self.faiss_path = (
            self.storage_dir
            / "travel.index"
        )

        self.metadata_path = (
            self.storage_dir
            / "metadata.json"
        )


        # =============================================
        # Embedding service
        # =============================================

        self.embedding_service = (
            EmbeddingService()
        )


        # =============================================
        # Vector store
        # =============================================

        self.vector_store = VectorStore(
            dimension=3072
        )


        # =============================================
        # Metadata store
        # =============================================

        self.metadata_store = (
            MetadataStore()
        )


        # =============================================
        # Load persistent knowledge base
        # =============================================

        self._load_knowledge_base()


        # =============================================
        # Connect metadata to FAISS
        # =============================================

        self.vector_store.set_documents(
            self.metadata_store.all()
        )


        # =============================================
        # Retriever
        # =============================================

        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_service=self.embedding_service
        )


        # =============================================
        # RAG Service
        # =============================================

        self.rag_service = RAGService(
            retriever=self.retriever,
            llm_service=self.llm_service
        )


    # =================================================
    # Load knowledge base
    # =================================================

    def _load_knowledge_base(self):

        if not self.faiss_path.exists():

            raise FileNotFoundError(
                "FAISS knowledge base not found:\n"
                f"{self.faiss_path}\n\n"
                "Run test_full_ingestion.py first."
            )


        if not self.metadata_path.exists():

            raise FileNotFoundError(
                "RAG metadata not found:\n"
                f"{self.metadata_path}\n\n"
                "Run test_full_ingestion.py first."
            )


        print(
            "\n========================================"
        )

        print(
            "Loading TravelOS RAG knowledge base..."
        )

        print(
            "========================================"
        )


        # ---------------------------------------------
        # Load FAISS
        # ---------------------------------------------

        self.vector_store.load(
            str(self.faiss_path)
        )


        # ---------------------------------------------
        # Load metadata
        # ---------------------------------------------

        self.metadata_store.load(
            str(self.metadata_path)
        )


        # ---------------------------------------------
        # Validate
        # ---------------------------------------------

        if (
            self.vector_store.size
            != self.metadata_store.count()
        ):

            raise ValueError(
                "FAISS vector count does not "
                "match metadata count."
            )


        print(
            "FAISS vectors:",
            self.vector_store.size
        )

        print(
            "Metadata documents:",
            self.metadata_store.count()
        )

        print(
            "RAG knowledge base loaded successfully."
        )

        print(
            "========================================\n"
        )


    # =================================================
    # Get RAG service
    # =================================================

    def get_rag_service(self):

        return self.rag_service