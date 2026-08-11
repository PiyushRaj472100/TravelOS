from app.rag.query import RAGQuery

from app.services.currency_query_service import (
    CurrencyQueryService
)


class LiveQueryService:

    def __init__(
        self,
        currency_query_service: CurrencyQueryService | None = None
    ):

        self.currency_query_service = (
            currency_query_service
            if currency_query_service
            else CurrencyQueryService()
        )

    def handle(
        self,
        query: RAGQuery
    ):

        if query.category == "currency":

            return self.currency_query_service.get_rate(
                query.question
            )

        raise ValueError(
            f"No live service is available for "
            f"category: {query.category}"
        )

    def close(self):

        self.currency_query_service.close()