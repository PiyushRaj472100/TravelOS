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
        "general",
    }

    def route(self, query: RAGQuery) -> str:

        if query.needs_live_data:
            return "live"

        if query.category in self.RAG_CATEGORIES:
            return "rag"

        if query.category in self.LIVE_CATEGORIES:
            return "live"

        return "rag"