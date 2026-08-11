import httpx


class FXProvider:

    BASE_URL = "https://fxapi.app/api"

    def __init__(self):

        self.client = httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,
                read=20.0,
                write=10.0,
                pool=10.0
            ),
            follow_redirects=True
        )

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

        url = (
            f"{self.BASE_URL}/"
            f"{base_currency}/"
            f"{target_currency}.json"
        )

        try:

            response = self.client.get(
                url
            )

            response.raise_for_status()

            data = response.json()

            if "rate" not in data:

                raise ValueError(
                    "FX provider response does not "
                    "contain a rate."
                )

            return float(
                data["rate"]
            )

        except httpx.TimeoutException as exc:

            raise RuntimeError(
                "The FX provider took too long "
                "to respond."
            ) from exc

        except httpx.HTTPStatusError as exc:

            raise RuntimeError(
                f"FX provider returned HTTP "
                f"{exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:

            raise RuntimeError(
                "Could not connect to the FX provider."
            ) from exc

    def close(self):

        self.client.close()