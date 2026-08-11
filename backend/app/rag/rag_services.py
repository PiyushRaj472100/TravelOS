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

        # 1. Retrieve relevant knowledge
        results = self.retriever.search(
            query=question,
            top_k=top_k,
            country=country,
            region=region,
            city=city,
            category=category
        )

        # 2. No knowledge found
        if not results:
            return {
                "answer": (
                    "I couldn't find reliable information "
                    "about this in my travel knowledge base."
                ),
                "sources": []
            }

        # 3. Build context
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

        # 4. Ground the LLM in retrieved context
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

        # 5. Ask the LLM
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
            context = self.context_builder.build(
             state,
             question
    )

            countries = context["countries"]
            regions = context["regions"]
            cities = context["cities"]

            country = countries[0] if countries else None
            region = regions[0] if regions else None
            city = cities[0] if cities else None

            return self.answer(
              question=question,
              country=country,
              region=region,
              city=city,
              top_k=top_k
    )