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

RETRIEVAL METADATA:
This score is only used internally to estimate
retrieval relevance. It is NOT travel information.
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


        filtered_results = (
            self._filter_by_score(
                results,
                min_score
            )
        )

        # ---------------------------------------------
        # 4. Fallback if no sufficiently relevant knowledge
        # ---------------------------------------------

        if not filtered_results:
            fallback_prompt = f"""You are TravelOS, a helpful AI travel assistant.
User question: "{question}"

Provide a clear, accurate, and comprehensive answer to help the traveler."""
            try:
                fallback_ans = self.llm_service.generate_response(fallback_prompt)
                return {
                    "answer": fallback_ans,
                    "sources": []
                }
            except Exception:
                return {
                    "answer": f"Great question about {city or country or 'your destination'}! Here are the best recommendations and details to consider.",
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
            list(countries)
            if countries is not None
            else list(context["countries"] or [])
        )

        regions = (
            list(regions)
            if regions is not None
            else list(context["regions"] or [])
        )

        cities = (
            list(cities)
            if cities is not None
            else list(context["cities"] or [])
        )

        # Map known cities to countries if country is missing
        city_to_country = {
            "paris": "France",
            "parris": "France",
            "tokyo": "Japan",
            "kyoto": "Japan",
            "osaka": "Japan",
            "london": "United Kingdom",
            "rome": "Italy",
            "new york": "USA",
            "dubai": "UAE",
            "bangkok": "Thailand",
            "bali": "Indonesia",
            "singapore": "Singapore",
            "sydney": "Australia",
            "berlin": "Germany",
            "amsterdam": "Netherlands",
            "cairo": "Egypt",
            "madrid": "Spain",
            "barcelona": "Spain",
            "mumbai": "India",
            "delhi": "India",
            "rishikesh": "India",
        }
        for city_item in cities:
            c_low = city_item.lower().strip()
            if c_low in city_to_country:
                matched_country = city_to_country[c_low]
                if matched_country not in countries:
                    countries.append(matched_country)

        # ---------------------------------------------
        # 3. Multi-destination retrieval
        # ---------------------------------------------

        results = self.retriever.search_multi(
            query=question,
            top_k=top_k,
            countries=countries if countries else None,
            regions=regions if regions else None,
            cities=cities if cities else None,
            category=category
        )

        filtered_results = (
            self._filter_by_score(
                results,
                min_score
            )
        )

        # If score filtering removed everything, keep top results
        if not filtered_results and results:
            filtered_results = results[:top_k]

        # ---------------------------------------------
        # 4. Fallback if no vector results
        # ---------------------------------------------

        if not filtered_results:
            target_dest = ", ".join(countries or cities or state.destinations or state.cities or ["your destination"])
            fallback_prompt = f"""You are TravelOS, a knowledgeable AI travel planning assistant.

User Question: "{question}"
Target Destination: {target_dest}

Provide a comprehensive, accurate, structured, and engaging travel response answering the user's question directly.
Cover safety guidelines, laws & regulations, scams to avoid, emergency numbers, cultural etiquette, and practical traveler tips where applicable."""
            try:
                fallback_answer = self.llm_service.generate_response(fallback_prompt)
                return {
                    "answer": fallback_answer,
                    "sources": []
                }
            except Exception as e:
                print(f"[RAGService] LLM fallback error: {e}")
                return {
                    "answer": f"Here are the important travel details and official guidance for {target_dest}. Always check official government advisories and stay vigilant in crowded areas.",
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

        prompt = f"""You are the TravelOS official travel knowledge assistant.

Answer the user's question clearly, thoroughly, and helpfully using the retrieved travel knowledge below as primary context.
Supplement with accurate, up-to-date travel facts, official emergency numbers, local laws, scam warnings, and actionable advice.

Format your response with clear Markdown headings, bullet points, and highlight important advice or emergency contact numbers (e.g. European emergency 112, Police 17, Medical 15 in France).

STRICT RULES:
1. Do not invent false facts or incorrect emergency numbers.
2. Address the user's specific query directly and comprehensively.
3. Keep the answer professional, reassuring, structured, and easy to read.

USER QUESTION:
{question}

RETRIEVED TRAVEL KNOWLEDGE & OFFICIAL DIRECTORIES:
{knowledge}

Provide the complete response:"""

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