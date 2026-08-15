from app.rag.query import RAGQuery


class QueryRouter:

    LIVE_CATEGORIES = {
        "weather",
        "currency",
        "flight",
        "accommodation",
    }

    RAG_CATEGORIES = {
        "visa",
        "entry_requirements",
        "regulations",
        "culture",
        "safety",
        "packing",
        "destination_information",
        "transportation",
        "restaurants",
        "activities",
        "accommodation",
        "general",
    }

    def route(
        self,
        query: RAGQuery
    ) -> str:

        # ---------------------------------------------
        # 1. Explicit live information always wins
        # ---------------------------------------------

        if query.needs_live_data:
            return "live"

        # ---------------------------------------------
        # 2. Planning intent always routes to planning!
        # ---------------------------------------------

        if query.query_type == "planning":
            return "planning"

        # ---------------------------------------------
        # 3. Knowledge queries / specific RAG categories
        # ---------------------------------------------

        if query.query_type == "knowledge":
            return "rag"

        # Knowledge categories take priority for informational topics
        if query.category in {
            "safety",
            "regulations",
            "visa",
            "entry_requirements",
            "culture",
            "packing",
        }:
            return "rag"

        # ---------------------------------------------
        # 4. Other Knowledge / Live categories fallback
        # ---------------------------------------------

        if query.category in self.RAG_CATEGORIES:
            return "rag"

        if query.category in self.LIVE_CATEGORIES:
            return "live"

        # ---------------------------------------------
        # 5. Safe fallback
        # ---------------------------------------------

        return "planning"
