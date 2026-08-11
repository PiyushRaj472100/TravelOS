from app.models.currency import (
    CurrencyRate,
    CurrencyConversion
)

from app.services.fx_provider import FXProvider


class CurrencyService:

    def __init__(
        self,
        fx_provider: FXProvider | None = None
    ):

        self.fx_provider = (
            fx_provider
            if fx_provider
            else FXProvider()
        )

        # Local cache of rates
        self.rates = {}

    def set_rate(
        self,
        base_currency: str,
        target_currency: str,
        rate: float
    ) -> CurrencyRate:

        base_currency = base_currency.upper()
        target_currency = target_currency.upper()

        currency_rate = CurrencyRate(
            base_currency=base_currency,
            target_currency=target_currency,
            rate=rate
        )

        self.rates[
            (base_currency, target_currency)
        ] = rate

        return currency_rate

    def get_rate(
        self,
        base_currency: str,
        target_currency: str
    ) -> float:

        base_currency = base_currency.upper()
        target_currency = target_currency.upper()

        # Same currency
        if base_currency == target_currency:
            return 1.0

        key = (
            base_currency,
            target_currency
        )

        # Check local cache first
        if key in self.rates:
            return self.rates[key]

        # Otherwise get live rate
        rate = self.fx_provider.get_rate(
            base_currency,
            target_currency
        )

        # Store it in cache
        self.rates[key] = rate

        return rate

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> CurrencyConversion:

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        rate = self.get_rate(
            from_currency,
            to_currency
        )

        converted_amount = amount * rate

        return CurrencyConversion(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            exchange_rate=rate,
            converted_amount=converted_amount
        )

    def convert_to_currencies(
        self,
        amount: float,
        from_currency: str,
        target_currencies: list[str]
    ) -> list[CurrencyConversion]:

        from_currency = from_currency.upper()

        # Remove duplicate currencies
        unique_currencies = list(
            dict.fromkeys(
                currency.upper()
                for currency in target_currencies
            )
        )

        results = []

        for currency in unique_currencies:

            result = self.convert(
                amount=amount,
                from_currency=from_currency,
                to_currency=currency
            )

            results.append(result)

        return results
    
    def convert_trip_budget(
        self,
        budget: float,
        budget_currency: str,
        target_currencies: list[str]
    ) -> list[CurrencyConversion]:

        return self.convert_to_currencies(
            amount= budget,
            from_currency=budget_currency,
            target_currencies=target_currencies
        )

    def close(self):

        self.fx_provider.close()