from app.services.currency_services import CurrencyService


class LiveDataService:

    def __init__(
        self,
        currency_service: CurrencyService | None = None
    ):

        self.currency_service = (
            currency_service
            if currency_service
            else CurrencyService()
        )

    def get_currency_rate(
        self,
        base_currency: str,
        target_currency: str
    ) -> dict:

        rate = self.currency_service.get_rate(
            base_currency=base_currency,
            target_currency=target_currency
        )

        return {
            "type": "currency",
            "base_currency": base_currency.upper(),
            "target_currency": target_currency.upper(),
            "rate": rate
        }

    def close(self):

        self.currency_service.close()