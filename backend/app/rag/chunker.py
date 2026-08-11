from app.rag.document import RAGDocument


def chunk_document(
    document: RAGDocument,
    chunk_size: int = 500
) -> list[RAGDocument]:

    words = document.text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):

        chunk_text = " ".join(
            words[i:i + chunk_size]
        )

        chunks.append(
            RAGDocument(
                text=chunk_text,
                country=document.country,
                region=document.region,
                city=document.city,
                category=document.category,
                source=document.source,
                title=document.title
            )
        )

    return chunks