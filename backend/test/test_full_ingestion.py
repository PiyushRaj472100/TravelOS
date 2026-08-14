from pathlib import Path

from app.rag.dataset_loader import (
    RAGDatasetLoader
)

from app.rag.embeddings import (
    EmbeddingService
)

from app.rag.vector_store import (
    VectorStore
)

from app.rag.metadata_store import (
    MetadataStore
)

from app.rag.ingestion import (
    RAGIngestionService
)


# =================================================
# Paths
# =================================================

VECTOR_STORE_DIR = Path(
    "data/vector_store"
)

FAISS_PATH = (
    VECTOR_STORE_DIR
    / "travel.index"
)

METADATA_PATH = (
    VECTOR_STORE_DIR
    / "metadata.json"
)


# =================================================
# Load dataset
# =================================================

loader = RAGDatasetLoader()

documents = loader.load_documents()


print(
    "\n========================================"
)

print(
    "DOCUMENTS LOADED:",
    len(documents)
)

print(
    "========================================"
)


# =================================================
# Services
# =================================================

embedding_service = (
    EmbeddingService()
)


vector_store = VectorStore(
    dimension=3072
)


metadata_store = MetadataStore()


ingestion = RAGIngestionService(
    embedding_service=embedding_service,
    vector_store=vector_store,
    metadata_store=metadata_store
)


# =================================================
# Ingest in batches
# =================================================

print(
    "\n========================================"
)

print(
    "STARTING BATCH INGESTION"
)

print(
    "========================================"
)


ingestion.ingest_batch(
    documents,
    batch_size=50
)


# =================================================
# Save FAISS
# =================================================

print(
    "\nSaving FAISS index..."
)

vector_store.save(
    str(FAISS_PATH)
)


# =================================================
# Save metadata
# =================================================

print(
    "Saving metadata..."
)

metadata_store.save(
    str(METADATA_PATH)
)


# =================================================
# Final statistics
# =================================================

print(
    "\n========================================"
)

print(
    "INGESTION COMPLETE"
)

print(
    "========================================"
)

print(
    "Documents:",
    len(documents)
)

print(
    "FAISS vectors:",
    vector_store.size
)

print(
    "Metadata:",
    metadata_store.count()
)

print(
    "FAISS file:",
    FAISS_PATH
)

print(
    "Metadata file:",
    METADATA_PATH
)