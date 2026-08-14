from app.models.travel_state import TravelState
from app.rag.rag_services import RAGService


class ResearchAgent:

    def __init__(
        self,
        rag_service: RAGService
    ):
        self.rag_service = rag_service


    # =================================================
    # Research Destination
    # =================================================

    def research(
        self,
        state: TravelState
    ) -> dict:

        destination = (
            state.destinations[0]
            if state.destinations
            else (
            
                state.countries[0]
                if state.countries
                else None
            )
        )

        if not destination:
            raise ValueError(
                "A destination is required "
                "for travel research."
            )


        # ---------------------------------------------
        # Build research question
        # ---------------------------------------------

        question_parts = [
            f"Research {destination} for this trip."
        ]


        if state.duration_days:

            question_parts.append(
                f"The trip is "
                f"{state.duration_days} days."
            )


        if state.travel_style:

            question_parts.append(
                f"Travel style: "
                f"{state.travel_style}."
            )


        if state.interests:

            interests = ", ".join(
                state.interests
            )

            question_parts.append(
                f"Interests: {interests}."
            )


        question_parts.append(
            "Provide useful information about "
            "important places to visit, destination "
            "highlights, culture, activities, and "
            "travel considerations."
        )


        question = " ".join(
            question_parts
        )


        # ---------------------------------------------
        # Query RAG
        # ---------------------------------------------

        result = (
            self.rag_service.answer_with_state(
                question=question,
                state=state,
                top_k=5
            )
        )


        # ---------------------------------------------
        # Return research result
        # ---------------------------------------------

        return {
            "agent": "research",

            "destination": destination,

            "question": question,

            "answer": result["answer"],

            "sources": result["sources"]
        }