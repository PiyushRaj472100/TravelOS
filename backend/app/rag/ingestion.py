from app.rag.document import RAGDocument
from app.rag.chunker import chunk_document


class RAGIngestionService:

    def __init__(
        self,
        embedding_service,
        vector_store,
        metadata_store
    ):

        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.metadata_store = metadata_store

    def ingest(
        self,
        document: RAGDocument
    ):

        chunks = chunk_document(
            document
        )

        for chunk in chunks:

            vector = (
                self.embedding_service
                .embed_document(
                    chunk.text
                )
            )

            self.vector_store.add(
                vector,
                chunk
            )

            self.metadata_store.add(
                chunk
            )