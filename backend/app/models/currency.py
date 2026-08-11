from pydantic import BaseModel, Field


class CurrencyRate(BaseModel):
    """
    Represents an exchange rate between two currencies.
    """

    base_currency: str
    target_currency: str

    rate: float = Field(
        gt=0,
        description="Number of target currency units per 1 base currency unit."
    )


class CurrencyConversion(BaseModel):
    """
    Represents a converted monetary amount.
    """

    amount: float = Field(
        ge=0
    )

    from_currency: str

    to_currency: str

    exchange_rate: float = Field(
        gt=0
    )

    converted_amount: float = Field(
        ge=0
    )