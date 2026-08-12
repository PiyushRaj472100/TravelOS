import time

from app.rag.chunker import chunk_document


class RAGIngestionService:

    def __init__(
        self,
        embedding_service,
        vector_store,
        metadata_store
    ):

        self.embedding_service = (
            embedding_service
        )

        self.vector_store = (
            vector_store
        )

        self.metadata_store = (
            metadata_store
        )


    # =================================================
    # Ingest one document
    # =================================================

    def ingest(
        self,
        document
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


    # =================================================
    # Ingest documents in batches
    # =================================================

    def ingest_batch(
        self,
        documents: list,
        batch_size: int = 50,
        max_retries: int = 5
    ):

        all_chunks = []


        # ---------------------------------------------
        # Chunk documents first
        # ---------------------------------------------

        for document in documents:

            chunks = chunk_document(
                document
            )

            all_chunks.extend(
                chunks
            )


        print(
            f"Total chunks: {len(all_chunks)}"
        )


        # ---------------------------------------------
        # Process embedding batches
        # ---------------------------------------------

        for start in range(
            0,
            len(all_chunks),
            batch_size
        ):

            batch = all_chunks[
                start:start + batch_size
            ]


            texts = [
                chunk.text
                for chunk in batch
            ]


            batch_number = (
                start // batch_size
            ) + 1


            total_batches = (
                (
                    len(all_chunks)
                    + batch_size
                    - 1
                )
                // batch_size
            )


            print(
                f"\nEmbedding batch "
                f"{batch_number}/{total_batches}"
            )


            # -----------------------------------------
            # Retry handling
            # -----------------------------------------

            for attempt in range(
                max_retries
            ):

                try:

                    vectors = (
                        self.embedding_service
                        .embed_documents(
                            texts
                        )
                    )

                    break


                except Exception as e:

                    print(
                        f"Embedding failed "
                        f"(attempt "
                        f"{attempt + 1}/"
                        f"{max_retries}):"
                    )

                    print(e)


                    if attempt == (
                        max_retries - 1
                    ):

                        raise


                    # Exponential backoff
                    wait_time = min(
                        60,
                        10 * (
                            2 ** attempt
                        )
                    )


                    print(
                        f"Waiting "
                        f"{wait_time} seconds..."
                    )


                    time.sleep(
                        wait_time
                    )


            # -----------------------------------------
            # Add to FAISS
            # -----------------------------------------

            self.vector_store.add_batch(
                vectors,
                batch
            )


            # -----------------------------------------
            # Add metadata
            # -----------------------------------------

            self.metadata_store.add_batch(
                batch
            )


            print(
                f"Added {len(batch)} chunks."
            )