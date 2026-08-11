from app.models.geo import GeoLocation, TravelLeg


class RouteService:

    @staticmethod
    def build_route(
        locations: list[GeoLocation]
    ) -> list[GeoLocation]:

        return locations.copy()

    @staticmethod
    def build_legs(
        route: list[GeoLocation]
    ) -> list[TravelLeg]:

        legs = []

        for index in range(len(route) - 1):

            legs.append(
                TravelLeg(
                    from_location=route[index],
                    to_location=route[index + 1],
                    order=index + 1
                )
            )

        return legs