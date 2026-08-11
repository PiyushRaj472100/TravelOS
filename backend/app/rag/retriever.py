from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore


class RAGRetriever:

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def search(
        self,
        query: str,
        top_k: int = 5,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        category: str | None = None
    ):

        # Convert the user's question into an embedding
        query_vector = self.embedding_service.embed_query(
            query
        )

        # Retrieve extra candidates because
        # metadata filtering may remove some results.
        results = self.vector_store.search(
            query_vector,
            top_k=top_k * 3
        )

        filtered = []

        for result in results:

            document = result["document"]

            # Filter by country
            if country and document.country != country:
                continue

            # Filter by region
            if region and document.region != region:
                continue

            # Filter by city
            if city and document.city != city:
                continue

            # Filter by category
            if category and document.category != category:
                continue

            filtered.append(result)

            # Stop once we have enough results
            if len(filtered) >= top_k:
                break

        return filtered

    def search_multi(
        self,
        query: str,
        top_k: int = 5,
        countries: list[str] | None = None,
        regions: list[str] | None = None,
        cities: list[str] | None = None,
        category: str | None = None
    ):

        countries = countries or []
        regions = regions or []
        cities = cities or []

        all_results = []

        # -------------------------------------------------
        # Search each country
        # -------------------------------------------------

        for country in countries:

            results = self.search(
                query=query,
                top_k=top_k,
                country=country,
                category=category
            )

            all_results.extend(results)

        # -------------------------------------------------
        # Search each region
        # -------------------------------------------------

        for region in regions:

            results = self.search(
                query=query,
                top_k=top_k,
                region=region,
                category=category
            )

            all_results.extend(results)

        # -------------------------------------------------
        # Search each city
        # -------------------------------------------------

        for city in cities:

            results = self.search(
                query=query,
                top_k=top_k,
                city=city,
                category=category
            )

            all_results.extend(results)

        # -------------------------------------------------
        # Global search if no location was provided
        # -------------------------------------------------

        if not countries and not regions and not cities:

            all_results = self.search(
                query=query,
                top_k=top_k,
                category=category
            )

        # -------------------------------------------------
        # Remove duplicate documents
        # -------------------------------------------------

        unique_results = []

        seen = set()

        for result in all_results:

            document = result["document"]

            key = (
                document.title,
                document.source,
                document.text
            )

            if key not in seen:

                seen.add(key)

                unique_results.append(result)

       
        # Return only the requested number of results
        
        unique_results.sort(    # global ranking by score
            key=lambda result: result["score"],
            reverse=True
        )
        
        
        
        return unique_results[:top_k]