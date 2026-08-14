from datetime import datetime, date, timedelta


class DateService:

    @staticmethod
    def normalize(
        date_text: str
    ) -> str:

        if not date_text:
            return (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")

        text = date_text.strip().lower()
        today = date.today()

        # -------------------------------------------------
        # Relative keywords
        # -------------------------------------------------
        if text in ("today", "now"):
            return today.strftime("%Y-%m-%d")
        if text in ("tomorrow",):
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        if "next week" in text:
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        if "next month" in text:
            return (today + timedelta(days=30)).strftime("%Y-%m-%d")
        if "in 2 weeks" in text or "in two weeks" in text:
            return (today + timedelta(days=14)).strftime("%Y-%m-%d")

        # -------------------------------------------------
        # Already ISO format
        # -------------------------------------------------
        try:
            parsed = datetime.strptime(
                date_text.strip(),
                "%Y-%m-%d"
            )
            return parsed.strftime("%Y-%m-%d")
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
                    date_text.strip(),
                    fmt
                )
                return parsed.strftime("%Y-%m-%d")
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
                    date_text.strip(),
                    fmt
                )
                year = today.year
                candidate = date(
                    year,
                    parsed.month,
                    parsed.day
                )
                if candidate < today:
                    candidate = date(
                        year + 1,
                        parsed.month,
                        parsed.day
                    )
                return candidate.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # -------------------------------------------------
        # Month name only (e.g. "March", "in November")
        # -------------------------------------------------
        month_names = {
            "january": 1, "jan": 1, "february": 2, "feb": 2,
            "march": 3, "mar": 3, "april": 4, "apr": 4,
            "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
            "august": 8, "aug": 8, "september": 9, "sep": 9,
            "october": 10, "oct": 10, "november": 11, "nov": 11,
            "december": 12, "dec": 12,
        }
        for m_name, m_num in month_names.items():
            if m_name in text:
                year = today.year
                candidate = date(year, m_num, 15)
                if candidate < today:
                    candidate = date(year + 1, m_num, 15)
                return candidate.strftime("%Y-%m-%d")

        # Fallback to default 30 days from now
        return (today + timedelta(days=30)).strftime("%Y-%m-%d")