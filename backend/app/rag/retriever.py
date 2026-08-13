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


    # =================================================
    # Normalize metadata values
    # =================================================

    @staticmethod
    def _normalize(
        value: str | None
    ) -> str | None:

        if value is None:
            return None

        return value.strip().lower()


    # =================================================
    # Check whether document matches metadata filters
    # =================================================

    def _matches_filters(
        self,
        document,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        category: str | None = None
    ) -> bool:

        # ---------------------------------------------
        # Country
        # ---------------------------------------------

        if country:

            if (
                self._normalize(document.country)
                != self._normalize(country)
            ):
                return False


        # ---------------------------------------------
        # Region
        # ---------------------------------------------

        if region:

            if (
                self._normalize(document.region)
                != self._normalize(region)
            ):
                return False


        # ---------------------------------------------
        # City
        # ---------------------------------------------

        if city:

            if (
                self._normalize(document.city)
                != self._normalize(city)
            ):
                return False


        # ---------------------------------------------
        # Category
        # ---------------------------------------------

        if category:

            if (
                self._normalize(document.category)
                != self._normalize(category)
            ):
                return False


        return True


    # =================================================
    # Single-location search
    # =================================================

    def search(
        self,
        query: str,
        top_k: int = 5,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        category: str | None = None
    ):

        # ---------------------------------------------
        # 1. Convert query to embedding
        # ---------------------------------------------

        query_vector = (
            self.embedding_service.embed_query(
                query
            )
        )


        # ---------------------------------------------
        # 2. Decide how many FAISS candidates
        #    to retrieve
        # ---------------------------------------------

        has_filters = any(
            [
                country,
                region,
                city,
                category
            ]
        )


        if has_filters:

            # -----------------------------------------
            # We currently have only 240 documents.
            #
            # Retrieve all candidates so that metadata
            # filtering cannot accidentally remove the
            # correct document.
            # -----------------------------------------

            candidate_k = self.vector_store.size

        else:

            candidate_k = top_k


        # ---------------------------------------------
        # 3. Semantic search
        # ---------------------------------------------

        results = self.vector_store.search(
            query_vector,
            top_k=candidate_k
        )


        # ---------------------------------------------
        # 4. Metadata filtering
        # ---------------------------------------------

        filtered = []

        for result in results:

            document = result["document"]

            if not self._matches_filters(
                document=document,
                country=country,
                region=region,
                city=city,
                category=category
            ):
                continue

            filtered.append(
                result
            )


        # ---------------------------------------------
        # 5. FAISS already returns similarity order,
        #    but explicitly sort for safety.
        # ---------------------------------------------

        filtered.sort(
            key=lambda result: result["score"],
            reverse=True
        )


        # ---------------------------------------------
        # 6. Return top results
        # ---------------------------------------------

        return filtered[:top_k]


    # =================================================
    # Multi-destination search
    # =================================================

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


        # ---------------------------------------------
        # 1. Search each country
        # ---------------------------------------------

        for country in countries:

            results = self.search(
                query=query,
                top_k=top_k,
                country=country,
                category=category
            )

            all_results.extend(
                results
            )


        # ---------------------------------------------
        # 2. Search each region
        # ---------------------------------------------

        for region in regions:

            results = self.search(
                query=query,
                top_k=top_k,
                region=region,
                category=category
            )

            all_results.extend(
                results
            )


        # ---------------------------------------------
        # 3. Search each city
        # ---------------------------------------------

        for city in cities:

            results = self.search(
                query=query,
                top_k=top_k,
                city=city,
                category=category
            )

            all_results.extend(
                results
            )


        # ---------------------------------------------
        # 4. No location specified
        # ---------------------------------------------

        if not countries and not regions and not cities:

            all_results = self.search(
                query=query,
                top_k=top_k,
                category=category
            )


        # ---------------------------------------------
        # 5. Remove duplicates
        # ---------------------------------------------

        unique_results = []

        seen = set()


        for result in all_results:

            document = result["document"]


            # Prefer document_id when available
            if document.document_id:

                key = document.document_id

            else:

                key = (
                    document.title,
                    document.country,
                    document.region,
                    document.city,
                    document.category,
                    document.source
                )


            if key in seen:
                continue


            seen.add(
                key
            )

            unique_results.append(
                result
            )


        # ---------------------------------------------
        # 6. Global ranking
        # ---------------------------------------------

        unique_results.sort(
            key=lambda result: result["score"],
            reverse=True
        )


        # ---------------------------------------------
        # 7. Return top results
        # ---------------------------------------------

        return unique_results[:top_k]