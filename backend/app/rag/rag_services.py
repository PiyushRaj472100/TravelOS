from app.rag.retriever import RAGRetriever
from app.models.travel_state import TravelState
from app.rag.context_builder import RAGContextBuilder


class RAGService:

    # =================================================
    # Minimum similarity score
    # =================================================

    DEFAULT_MIN_SCORE = 0.35


    def __init__(
        self,
        retriever: RAGRetriever,
        llm_service
    ):

        self.retriever = retriever
        self.llm_service = llm_service
        self.context_builder = RAGContextBuilder()


    # =================================================
    # Filter results using similarity score
    # =================================================

    def _filter_by_score(
        self,
        results,
        min_score: float
    ):

        return [
            result
            for result in results
            if result["score"] >= min_score
        ]


    # =================================================
    # Build source information
    # =================================================

    @staticmethod
    def _build_source(
        result
    ):

        document = result["document"]

        return {
            "title": document.title,
            "source": document.source,

            "source_url": (
                document.source_url
            ),

            "fallback_search_url": (
                document.fallback_search_url
            ),

            "country": document.country,
            "region": document.region,
            "city": document.city,
            "category": document.category,

            "score": result["score"]
        }


    # =================================================
    # Build document context
    # =================================================

    @staticmethod
    def _build_context(
        results
    ):

        context_parts = []

        for result in results:

            document = result["document"]

            context_parts.append(
                f"""
SOURCE:
{document.title or "Unknown"}

COUNTRY:
{document.country or "Unknown"}

REGION:
{document.region or "Unknown"}

CITY:
{document.city or "Unknown"}

CATEGORY:
{document.category or "Unknown"}

OFFICIAL SOURCE URL:
{document.source_url or "Not available"}

FALLBACK SEARCH URL:
{document.fallback_search_url or "Not available"}

CONTENT:
{document.text}

SIMILARITY SCORE:
{result["score"]:.4f}
"""
            )

        return "\n\n".join(
            context_parts
        )


    # =================================================
    # Standard RAG answer
    # =================================================

    def answer(
        self,
        question: str,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        category: str | None = None,
        top_k: int = 5,
        min_score: float = DEFAULT_MIN_SCORE
    ):

        # ---------------------------------------------
        # 1. Retrieve relevant knowledge
        # ---------------------------------------------

        results = self.retriever.search(
            query=question,
            top_k=top_k,
            country=country,
            region=region,
            city=city,
            category=category
        )


        # ---------------------------------------------
        # 2. No results
        # ---------------------------------------------

        if not results:

            return {
                "answer": (
                    "I couldn't find reliable information "
                    "about this in the TravelOS knowledge base."
                ),
                "sources": []
            }


        # ---------------------------------------------
        # 3. Apply similarity threshold
        # ---------------------------------------------

        filtered_results = (
            self._filter_by_score(
                results,
                min_score
            )
        )


        # ---------------------------------------------
        # 4. No sufficiently relevant knowledge
        # ---------------------------------------------

        if not filtered_results:

            return {
                "answer": (
                    "I couldn't find sufficiently relevant "
                    "information in the TravelOS knowledge base "
                    "to answer this reliably."
                ),
                "sources": []
            }


        # ---------------------------------------------
        # 5. Build context
        # ---------------------------------------------

        context = self._build_context(
            filtered_results
        )


        # ---------------------------------------------
        # 6. Build sources
        # ---------------------------------------------

        sources = [
            self._build_source(result)
            for result in filtered_results
        ]


        # ---------------------------------------------
        # 7. Grounded prompt
        # ---------------------------------------------

        prompt = f"""
You are the knowledge assistant for TravelOS.

Your job is to answer the user's question using
ONLY the retrieved travel knowledge below.

STRICT RULES:

1. Do not invent facts.
2. Do not use outside knowledge.
3. Do not make assumptions that are not supported
   by the retrieved knowledge.
4. If the retrieved knowledge does not contain
   enough information, clearly say so.
5. Prefer information relevant to the requested
   country, region, city, and category.
6. Do not treat similarity scores as factual
   information.
7. Keep the answer clear and useful.

USER QUESTION:

{question}

RETRIEVED TRAVEL KNOWLEDGE:

{context}

Answer the question using the retrieved knowledge.
"""


        # ---------------------------------------------
        # 8. Generate answer
        # ---------------------------------------------

        response = (
            self.llm_service.generate_response(
                prompt
            )
        )


        # ---------------------------------------------
        # 9. Return answer + sources
        # ---------------------------------------------

        return {
            "answer": response,
            "sources": sources
        }


    # =================================================
    # RAG answer using TravelState
    # =================================================

    def answer_with_state(
        self,
        question: str,
        state: TravelState,
        top_k: int = 5,
        min_score: float = DEFAULT_MIN_SCORE,
        category: str | None = None,
        countries: list[str] | None = None,
        regions: list[str] | None = None,
        cities: list[str] | None = None
    ):

        # ---------------------------------------------
        # 1. Build RAG context from TravelState
        # ---------------------------------------------

        context = self.context_builder.build(
            state,
            question
        )


        # ---------------------------------------------
        # 2. Use QueryAnalyzer locations when provided
        #
        # Otherwise fall back to TravelState context.
        # ---------------------------------------------

        countries = (
            countries
            if countries is not None
            else context["countries"]
        )

        regions = (
            regions
            if regions is not None
            else context["regions"]
        )

        cities = (
            cities
            if cities is not None
            else context["cities"]
        )


        # ---------------------------------------------
        # 3. Multi-destination retrieval
        # ---------------------------------------------

        results = self.retriever.search_multi(
            query=question,
            top_k=top_k,
            countries=countries,
            regions=regions,
            cities=cities,
            category=category
        )


        # ---------------------------------------------
        # 4. No results
        # ---------------------------------------------

        if not results:

            return {
                "answer": (
                    "I couldn't find relevant travel "
                    "knowledge for this question."
                ),
                "sources": []
            }


        # ---------------------------------------------
        # 5. Apply similarity threshold
        # ---------------------------------------------

        filtered_results = (
            self._filter_by_score(
                results,
                min_score
            )
        )


        # ---------------------------------------------
        # 6. No sufficiently relevant knowledge
        # ---------------------------------------------

        if not filtered_results:

            return {
                "answer": (
                    "I couldn't find sufficiently relevant "
                    "travel knowledge to answer this reliably."
                ),
                "sources": []
            }


        # ---------------------------------------------
        # 7. Build knowledge context
        # ---------------------------------------------

        knowledge = self._build_context(
            filtered_results
        )


        # ---------------------------------------------
        # 8. Build sources
        # ---------------------------------------------

        sources = [
            self._build_source(result)
            for result in filtered_results
        ]


        # ---------------------------------------------
        # 9. Grounded prompt
        # ---------------------------------------------

        prompt = f"""
You are the TravelOS travel knowledge assistant.

Answer the user's question using ONLY the retrieved
travel knowledge below.

The user's trip may contain multiple destinations.

STRICT RULES:

1. Do not invent facts.
2. Do not use outside knowledge.
3. Use only information supported by the retrieved
   travel knowledge.
4. If the knowledge is insufficient, clearly say so.
5. Prefer information relevant to the user's
   destinations.
6. Do not treat similarity scores as factual
   information.
7. Give a clear and useful answer.

USER QUESTION:

{question}

TRAVEL KNOWLEDGE:

{knowledge}

Answer the user's question using the retrieved
knowledge.
"""


        # ---------------------------------------------
        # 10. Generate answer
        # ---------------------------------------------

        response = (
            self.llm_service.generate_response(
                prompt
            )
        )


        # ---------------------------------------------
        # 11. Return answer + sources
        # ---------------------------------------------

        return {
            "answer": response,
            "sources": sources
        }