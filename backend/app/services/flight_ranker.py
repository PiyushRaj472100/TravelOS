from app.models.transportation import TransportationOption


class FlightRanker:

    @staticmethod
    def cheapest(
        flights: list[TransportationOption],
        limit: int = 5
    ) -> list[TransportationOption]:

        valid = [
            flight
            for flight in flights
            if flight.price is not None
        ]

        return sorted(
            valid,
            key=lambda flight: flight.price
        )[:limit]


    @staticmethod
    def fastest(
        flights: list[TransportationOption],
        limit: int = 5
    ) -> list[TransportationOption]:

        valid = [
            flight
            for flight in flights
            if flight.duration_minutes is not None
        ]

        return sorted(
            valid,
            key=lambda flight: flight.duration_minutes
        )[:limit]


    @staticmethod
    def fewest_stops(
        flights: list[TransportationOption],
        limit: int = 5
    ) -> list[TransportationOption]:

        valid = [
            flight
            for flight in flights
            if flight.stops is not None
        ]

        return sorted(
            valid,
            key=lambda flight: flight.stops
        )[:limit]


    @staticmethod
    def balanced(
        flights: list[TransportationOption],
        limit: int = 5
    ) -> list[TransportationOption]:

        valid = [
            flight
            for flight in flights
            if (
                flight.price is not None
                and flight.duration_minutes is not None
                and flight.stops is not None
            )
        ]

        if not valid:
            return []


        # ---------------------------------------------
        # Normalize values
        # ---------------------------------------------

        min_price = min(
            flight.price
            for flight in valid
        )

        max_price = max(
            flight.price
            for flight in valid
        )

        min_duration = min(
            flight.duration_minutes
            for flight in valid
        )

        max_duration = max(
            flight.duration_minutes
            for flight in valid
        )


        def normalize(
            value,
            minimum,
            maximum
        ):

            if maximum == minimum:
                return 0

            return (
                (value - minimum)
                / (maximum - minimum)
            )


        # ---------------------------------------------
        # Calculate score
        # ---------------------------------------------

        scored = []

        for flight in valid:

            price_score = normalize(
                flight.price,
                min_price,
                max_price
            )

            duration_score = normalize(
                flight.duration_minutes,
                min_duration,
                max_duration
            )

            stops_score = (
                flight.stops
                / max(
                    f.stops
                    for f in valid
                )
                if max(
                    f.stops
                    for f in valid
                ) > 0
                else 0
            )


            score = (
                0.45 * price_score
                + 0.40 * duration_score
                + 0.15 * stops_score
            )

            scored.append(
                (
                    score,
                    flight
                )
            )


        scored.sort(
            key=lambda item: item[0]
        )

        return [
            flight
            for _, flight in scored[:limit]
        ]