from app.rag.document import RAGDocument


def chunk_document(
    document: RAGDocument,
    chunk_size: int = 500
) -> list[RAGDocument]:

    # ---------------------------------------------
    # 1. Split document text into words
    # ---------------------------------------------

    words = document.text.split()

    chunks = []


    # ---------------------------------------------
    # 2. Create chunks
    # ---------------------------------------------

    for i in range(
        0,
        len(words),
        chunk_size
    ):

        chunk_text = " ".join(
            words[i:i + chunk_size]
        )


        # -----------------------------------------
        # 3. Preserve ALL document metadata
        # -----------------------------------------

        chunks.append(
            RAGDocument(

                # Knowledge content
                text=chunk_text,

                title=document.title,


                # Geographic metadata
                country=document.country,
                region=document.region,
                city=document.city,


                # Category
                category=document.category,


                # Source / provenance
                source=document.source,
                source_url=document.source_url,

                fallback_search_url=(
                    document.fallback_search_url
                ),


                # Freshness
                last_updated=(
                    document.last_updated
                ),


                # Document ID
                document_id=document.document_id
            )
        )


    # ---------------------------------------------
    # 4. Return chunks
    # ---------------------------------------------

    return chunks