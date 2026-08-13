from datetime import datetime, date


class DateService:

    @staticmethod
    def normalize(
        date_text: str
    ) -> str:

        if not date_text:
            raise ValueError(
                "Departure date is required."
            )

        date_text = date_text.strip()

        # -------------------------------------------------
        # Already ISO format
        # -------------------------------------------------

        try:

            parsed = datetime.strptime(
                date_text,
                "%Y-%m-%d"
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            pass


        # -------------------------------------------------
        # Common natural date formats
        # -------------------------------------------------

        formats = [

            "%B %d, %Y",
            "%B %d %Y",

            "%b %d, %Y",
            "%b %d %Y",

            "%d %B %Y",
            "%d %b %Y",

            "%d/%m/%Y",
            "%d-%m-%Y",

            "%m/%d/%Y",
            "%m-%d-%Y"
        ]


        for fmt in formats:

            try:

                parsed = datetime.strptime(
                    date_text,
                    fmt
                )

                return parsed.strftime(
                    "%Y-%m-%d"
                )

            except ValueError:
                continue


        # -------------------------------------------------
        # Month + day without year
        # -------------------------------------------------

        formats_without_year = [

            "%B %d",
            "%b %d",
            "%d %B",
            "%d %b"
        ]


        for fmt in formats_without_year:

            try:

                parsed = datetime.strptime(
                    date_text,
                    fmt
                )

                today = date.today()

                year = today.year

                candidate = date(
                    year,
                    parsed.month,
                    parsed.day
                )

                # If date already passed this year,
                # assume the user means next year.

                if candidate < today:

                    candidate = date(
                        year + 1,
                        parsed.month,
                        parsed.day
                    )

                return candidate.strftime(
                    "%Y-%m-%d"
                )

            except ValueError:
                continue


        raise ValueError(
            f"Could not understand departure date: "
            f"'{date_text}'. "
            f"Please use a date such as "
            f"'September 15' or '2026-09-15'."
        )