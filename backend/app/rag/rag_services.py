from app.rag.retriever import RAGRetriever
from app.models.travel_state import TravelState
from app.rag.context_builder import RAGContextBuilder


class RAGService:

    def __init__(
        self,
        retriever: RAGRetriever,
        llm_service
    ):
        self.retriever = retriever
        self.llm_service = llm_service
        self.context_builder = RAGContextBuilder()

    def answer(
        self,
        question: str,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        category: str | None = None,
        top_k: int = 5
    ):

        # -------------------------------------------------
        # 1. Retrieve relevant knowledge
        # -------------------------------------------------

        results = self.retriever.search(
            query=question,
            top_k=top_k,
            country=country,
            region=region,
            city=city,
            category=category
        )

        # -------------------------------------------------
        # 2. No knowledge found
        # -------------------------------------------------

        if not results:

            return {
                "answer": (
                    "I couldn't find reliable information "
                    "about this in my travel knowledge base."
                ),
                "sources": []
            }

        # -------------------------------------------------
        # 3. Build context
        # -------------------------------------------------

        context_parts = []
        sources = []

        for result in results:

            document = result["document"]

            context_parts.append(
                f"""
SOURCE: {document.title or "Unknown"}
COUNTRY: {document.country or "Unknown"}
CATEGORY: {document.category or "Unknown"}

CONTENT:
{document.text}
"""
            )

            sources.append({
                "title": document.title,
                "source": document.source,
                "country": document.country,
                "category": document.category,
                "score": result["score"]
            })

        context = "\n\n".join(
            context_parts
        )

        # -------------------------------------------------
        # 4. Ground the LLM in retrieved context
        # -------------------------------------------------

        prompt = f"""
You are the knowledge assistant for TravelOS.

Answer the user's question using ONLY the
provided travel knowledge.

Do not invent facts.

If the provided knowledge does not contain
enough information to answer the question,
say that the available knowledge is insufficient.

User question:
{question}

Retrieved travel knowledge:
{context}

Give a clear and useful answer.
"""

        # -------------------------------------------------
        # 5. Ask the LLM
        # -------------------------------------------------

        response = self.llm_service.generate_response(
            prompt
        )

        return {
            "answer": response,
            "sources": sources
        }

    def answer_with_state(
        self,
        question: str,
        state: TravelState,
        top_k: int = 5
    ):

        # -------------------------------------------------
        # 1. Build RAG context from TravelState
        # -------------------------------------------------

        context = self.context_builder.build(
            state,
            question
        )

        # -------------------------------------------------
        # 2. Multi-destination retrieval
        # -------------------------------------------------

        results = self.retriever.search_multi(
            query=question,
            top_k=top_k,
            countries=context["countries"],
            regions=context["regions"],
            cities=context["cities"]
        )

        # -------------------------------------------------
        # 3. No knowledge found
        # -------------------------------------------------

        if not results:

            return {
                "answer": (
                    "I couldn't find relevant travel "
                    "knowledge for this question."
                ),
                "sources": []
            }

        # -------------------------------------------------
        # 4. Build knowledge context
        # -------------------------------------------------

        context_parts = []
        sources = []

        for result in results:

            document = result["document"]

            context_parts.append(
                f"""
SOURCE: {document.title or "Unknown"}

COUNTRY: {document.country or "Unknown"}

REGION: {document.region or "Unknown"}

CITY: {document.city or "Unknown"}

CATEGORY: {document.category or "Unknown"}

CONTENT:
{document.text}
"""
            )

            sources.append({
                "title": document.title,
                "source": document.source,
                "country": document.country,
                "region": document.region,
                "city": document.city,
                "category": document.category,
                "score": result["score"]
            })

        knowledge = "\n\n".join(
            context_parts
        )

        # -------------------------------------------------
        # 5. Create grounded prompt
        # -------------------------------------------------

        prompt = f"""
You are the TravelOS travel knowledge assistant.

Answer the user's question using the retrieved
travel knowledge below.

The user's trip may contain multiple destinations.

Do not invent facts.

If the retrieved knowledge does not contain
enough information, clearly say that the available
knowledge is insufficient.

USER QUESTION:
{question}

TRAVEL KNOWLEDGE:
{knowledge}

Give a clear, useful answer.
"""

        # -------------------------------------------------
        # 6. Generate answer
        # -------------------------------------------------

        response = self.llm_service.generate_response(
            prompt
        )

        # -------------------------------------------------
        # 7. Return answer + sources
        # -------------------------------------------------

        return {
            "answer": response,
            "sources": sources
        }