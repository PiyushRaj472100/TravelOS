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
            doc_c = self._normalize(document.country)
            target_c = self._normalize(country)
            if doc_c and target_c:
                if doc_c != target_c and doc_c not in target_c and target_c not in doc_c:
                    return False
            elif doc_c != target_c:
                return False

        # ---------------------------------------------
        # Region
        # ---------------------------------------------

        if region:
            doc_r = self._normalize(document.region)
            target_r = self._normalize(region)
            if doc_r and target_r:
                if doc_r != target_r and doc_r not in target_r and target_r not in doc_r:
                    return False
            elif doc_r != target_r:
                return False

        # ---------------------------------------------
        # City
        # ---------------------------------------------

        if city:
            doc_city = self._normalize(document.city)
            target_city = self._normalize(city)
            # If document has a city specified, match against it
            if doc_city is not None and target_city is not None:
                if doc_city != target_city and doc_city not in target_city and target_city not in doc_city:
                    return False

        # ---------------------------------------------
        # Category
        # ---------------------------------------------

        if category:
            doc_cat = self._normalize(document.category)
            target_cat = self._normalize(category)
            if doc_cat and target_cat:
                if doc_cat != target_cat and doc_cat not in target_cat and target_cat not in doc_cat:
                    # Allow related safety/regulations cross-matching
                    if target_cat in ("safety", "regulations", "rules") and doc_cat in ("safety", "regulations", "visa", "entry_requirements"):
                        pass
                    else:
                        return False
            elif doc_cat != target_cat:
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
        # 4. Fallback if no location specified or 0 results found
        # ---------------------------------------------

        if not all_results:
            all_results = self.search(
                query=query,
                top_k=top_k,
                category=category
            )

        if not all_results:
            all_results = self.search(
                query=query,
                top_k=top_k
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