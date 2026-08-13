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
        # 2. Planning intent
        # ---------------------------------------------

        if query.query_type == "planning":

            return "planning"


        # ---------------------------------------------
        # 3. Knowledge categories
        # ---------------------------------------------

        if query.category in self.RAG_CATEGORIES:

            return "rag"


        # ---------------------------------------------
        # 4. Live categories
        #
        # If category is naturally live but the user
        # didn't explicitly request current information,
        # we treat it as knowledge where possible.
        # ---------------------------------------------

        if query.category in self.LIVE_CATEGORIES:

            return "rag"


        # ---------------------------------------------
        # 5. Safe fallback
        # ---------------------------------------------

        return "rag"