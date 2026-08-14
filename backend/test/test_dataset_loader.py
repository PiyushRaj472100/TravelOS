import random

from app.rag.dataset_loader import RAGDatasetLoader
from app.rag.chunker import chunk_document


# ---------------------------------------------
# 1. Load all documents
# ---------------------------------------------

loader = RAGDatasetLoader()

documents = loader.load_documents()


print(
    "\n========================================"
)

print(
    "TOTAL DOCUMENTS:",
    len(documents)
)

print(
    "========================================"
)


# ---------------------------------------------
# 2. Select different country/category pairs
# ---------------------------------------------

test_cases = [
    ("Australia", "visa"),
    ("United Arab Emirates", "safety"),
    ("Japan", "culture"),
    ("India", "transportation"),
    ("France", "activities"),
    ("Canada", "packing"),
    ("Italy", "entry_requirements"),
    ("Thailand", "destination_information"),
]


# ---------------------------------------------
# 3. Test each case
# ---------------------------------------------

for country, category in test_cases:

    matching_documents = [
        document
        for document in documents
        if (
            document.country == country
            and document.category == category
        )
    ]


    print(
        "\n\n========================================"
    )

    print(
        f"TEST: {country} → {category}"
    )

    print(
        "========================================"
    )


    # -----------------------------------------
    # No matching document
    # -----------------------------------------

    if not matching_documents:

        print(
            "❌ Document not found"
        )

        continue


    # -----------------------------------------
    # Get document
    # -----------------------------------------

    document = matching_documents[0]


    print(
        "\nOriginal Document"
    )

    print(
        "-------------------------"
    )

    print(
        "Country:",
        document.country
    )

    print(
        "Category:",
        document.category
    )

    print(
        "Title:",
        document.title
    )

    print(
        "Source URL:",
        document.source_url
    )

    print(
        "Fallback URL:",
        document.fallback_search_url
    )


    # -----------------------------------------
    # Chunk document
    # -----------------------------------------

    chunks = chunk_document(
        document,
        chunk_size=50
    )


    print(
        "\nChunks:",
        len(chunks)
    )


    # -----------------------------------------
    # Verify first chunk
    # -----------------------------------------

    chunk = chunks[0]


    print(
        "\nFirst Chunk Metadata"
    )

    print(
        "-------------------------"
    )

    print(
        "Country:",
        chunk.country
    )

    print(
        "Category:",
        chunk.category
    )

    print(
        "Title:",
        chunk.title
    )

    print(
        "Source URL:",
        chunk.source_url
    )

    print(
        "Fallback URL:",
        chunk.fallback_search_url
    )


    # -----------------------------------------
    # Verify metadata
    # -----------------------------------------

    if (
        chunk.country == document.country
        and
        chunk.category == document.category
        and
        chunk.source_url == document.source_url
        and
        chunk.fallback_search_url
        == document.fallback_search_url
    ):

        print(
            "\n✅ Metadata preserved correctly"
        )

    else:

        print(
            "\n❌ Metadata preservation FAILED"
        )


print(
    "\n\n========================================"
)

print(
    "RANDOM ADDITIONAL TESTS"
)

print(
    "========================================"
)


# ---------------------------------------------
# 4. Random tests from the complete dataset
# ---------------------------------------------

random_documents = random.sample(
    documents,
    min(5, len(documents))
)


for document in random_documents:

    print(
        f"\n🌍 {document.country}"
    )

    print(
        f"📚 {document.category}"
    )

    print(
        f"📄 {document.title}"
    )

    print(
        f"🔗 {document.source_url}"
    )

    print(
        f"🔎 {document.fallback_search_url}"
    )