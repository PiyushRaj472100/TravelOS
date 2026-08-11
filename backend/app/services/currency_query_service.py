import re

from app.services.currency_services import CurrencyService


class CurrencyQueryService:

    def __init__(
        self,
        currency_service: CurrencyService | None = None
    ):

        self.currency_service = (
            currency_service
            if currency_service
            else CurrencyService()
        )

    def extract_currency_pair(
        self,
        question: str
    ) -> tuple[str, str]:

        pattern = (
            r"\b([A-Za-z]{3})\s*"
            r"(?:to|into|in)\s*"
            r"([A-Za-z]{3})\b"
        )

        match = re.search(
            pattern,
            question,
            re.IGNORECASE
        )

        if not match:

            raise ValueError(
                "Could not identify the "
                "currency pair."
            )

        base_currency = (
            match.group(1).upper()
        )

        target_currency = (
            match.group(2).upper()
        )

        return (
            base_currency,
            target_currency
        )

    def get_rate(
        self,
        question: str
    ):

        (
            base_currency,
            target_currency
        ) = self.extract_currency_pair(
            question
        )

        rate = self.currency_service.get_rate(
            base_currency,
            target_currency
        )

        return {
            "base_currency": base_currency,
            "target_currency": target_currency,
            "rate": rate
        }

    def close(self):

        self.currency_service.close()