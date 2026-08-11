class CountryCurrencyService:

    def __init__(self):

        self.country_currencies = {
            "india": "INR",
            "united states": "USD",
            "usa": "USD",
            "united kingdom": "GBP",
            "uk": "GBP",

            "france": "EUR",
            "germany": "EUR",
            "italy": "EUR",
            "spain": "EUR",
            "portugal": "EUR",
            "netherlands": "EUR",
            "belgium": "EUR",
            "austria": "EUR",
            "ireland": "EUR",
            "greece": "EUR",

            "switzerland": "CHF",

            "japan": "JPY",
            "china": "CNY",
            "south korea": "KRW",

            "australia": "AUD",
            "canada": "CAD",

            "singapore": "SGD",

            "thailand": "THB",
            "malaysia": "MYR",
            "indonesia": "IDR",

            "uae": "AED",
            "united arab emirates": "AED",

            "saudi arabia": "SAR",

            "turkey": "TRY",

            "nepal": "NPR",

            "bangladesh": "BDT",

            "sri lanka": "LKR"
        }

    def get_currency(
        self,
        country: str
    ) -> str:

        country = country.strip().lower()

        if country not in self.country_currencies:

            raise ValueError(
                f"Currency not known for country: "
                f"{country}"
            )

        return self.country_currencies[country]

    def get_currencies(
        self,
        countries: list[str]
    ) -> list[str]:

        currencies = []

        for country in countries:

            currency = self.get_currency(
                country
            )

            currencies.append(currency)

        # Remove duplicate currencies
        return list(
            dict.fromkeys(currencies)
        )