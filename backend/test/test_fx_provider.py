from app.services.country_currency_services import (
    CountryCurrencyService
)


service = CountryCurrencyService()


countries = [
    "France",
    "Switzerland",
    "Italy",
    "Japan"
]


print("\n==============================")
print("COUNTRY → CURRENCY")
print("==============================")


for country in countries:

    currency = service.get_currency(
        country
    )

    print(
        f"{country} → {currency}"
    )


print("\n==============================")
print("UNIQUE CURRENCIES")
print("==============================")


currencies = service.get_currencies(
    countries
)

print(currencies)