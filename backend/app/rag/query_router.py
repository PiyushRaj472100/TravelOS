from app.rag.query import RAGQuery


class QueryRouter:

    LIVE_CATEGORIES = {
        "weather",
        "currency",
        "flight",
    }

    RAG_CATEGORIES = {
        "visa",
        "entry_requirements",
        "regulations",
        "transportation",
        "restaurants",
        "activities",
        "culture",
        "safety",
        "packing",
        "destination_information",
    }

    def route(
        self,
        query: RAGQuery
    ) -> str:

        # -----------------------------------------
        # 1. Explicit current/live request
        # -----------------------------------------

        if query.needs_live_data:
            return "live"

        # -----------------------------------------
        # 2. User is planning their own trip
        # -----------------------------------------

        if query.query_type == "planning":
            return "planning"

        # -----------------------------------------
        # 3. User wants knowledge from RAG
        # -----------------------------------------

        if query.query_type == "knowledge":

            if query.category in self.RAG_CATEGORIES:
                return "rag"

            return "rag"

        # -----------------------------------------
        # 4. Live category fallback
        # -----------------------------------------

        if query.category in self.LIVE_CATEGORIES:
            return "live"

        # -----------------------------------------
        # 5. Safe default
        # -----------------------------------------

        return "planning"