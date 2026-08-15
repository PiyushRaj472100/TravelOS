"""
OrchestratorAgent — decides which agents to invoke for each user message.

This is the coordination layer of TravelOS.
It reads TravelState + query intent and routes to appropriate agents.
"""

from app.models.travel_state import TravelState
from app.services.geo_service import GeoService
from app.models.chat import (
    AgentStatus,
    BudgetBreakdown,
    MapData,
    MapMarker,
    MapRoute,
)
from app.rag.query import RAGQuery


from app.services.currency_services import CurrencyService
from app.services.flight_service import FlightService
from app.services.weather_service import WeatherService
from app.services.flight_ranker import FlightRanker


class OrchestratorAgent:

    def __init__(
        self,
        research_agent,
        hotel_agent,
        activity_agent,
        itinerary_agent,
        budget_agent,
        currency_service: CurrencyService | None = None,
        flight_service: FlightService | None = None,
        weather_service: WeatherService | None = None,
    ):
        self.research_agent = research_agent
        self.hotel_agent = hotel_agent
        self.activity_agent = activity_agent
        self.itinerary_agent = itinerary_agent
        self.budget_agent = budget_agent
        self.currency_service = currency_service or CurrencyService()
        self.flight_service = flight_service or FlightService()
        self.weather_service = weather_service or WeatherService()


    # =================================================
    # Orchestrate — main entry point
    # =================================================

    def orchestrate(
        self,
        query: RAGQuery,
        state: TravelState,
        live_result: dict | None = None,
    ) -> dict:
        """
        Determine which agents to run and collect their results.

        Returns enrichment dict:
        {
            agent_statuses, flights, hotels, activities,
            itinerary, budget, map_data, research_answer, research_sources
        }
        """

        agent_statuses: list[AgentStatus] = []
        flights: list[dict] = []
        hotels: list[dict] = []
        activities: list[dict] = []
        itinerary: list[dict] = []
        budget: BudgetBreakdown | None = None
        research_answer: str = ""
        research_sources: list = []


        # -------------------------------------------------
        # 1. Research Agent — run when there's a destination
        #    and the user is asking knowledge questions
        # -------------------------------------------------

        should_research = (
            bool(state.destinations or state.cities)
            and query.query_type in ("knowledge", "planning")
            and query.category in (
                "destination_information", "culture", "activities",
                "safety", "packing", "general", "restaurants",
                "transportation", "entry_requirements", "visa"
            )
        )

        if should_research:
            agent_statuses.append(
                AgentStatus(agent="research", status="working", message="Researching destination...")
            )
            try:
                research_result = self.research_agent.research(state)
                research_answer = research_result.get("answer", "")
                research_sources = research_result.get("sources", [])
                agent_statuses[-1] = AgentStatus(
                    agent="research", status="done",
                    message="Destination research complete"
                )
            except Exception as e:
                print(f"[Orchestrator] Research agent error: {e}")
                agent_statuses[-1] = AgentStatus(
                    agent="research", status="failed",
                    message=str(e)
                )


        # -------------------------------------------------
        # 2. Hotel Agent — run when hotel search is requested
        # -------------------------------------------------

        should_search_hotels = (
            query.category in ("accommodation",)
            and query.needs_live_data
        ) or self._is_hotel_request(query.question)

        if should_search_hotels and (
            state.destinations or state.cities
        ):
            agent_statuses.append(
                AgentStatus(agent="hotel", status="working", message="Searching hotels...")
            )
            try:
                hotel_result = self.hotel_agent.search(state)
                raw_hotels = hotel_result.get("hotels", [])
                hotels = [self._serialize_hotel(h, state.currency) for h in raw_hotels]
                agent_statuses[-1] = AgentStatus(
                    agent="hotel", status="done",
                    message=f"{len(hotels)} hotels found"
                )
            except Exception as e:
                print(f"[Orchestrator] Hotel agent error: {e}")
                agent_statuses[-1] = AgentStatus(
                    agent="hotel", status="failed",
                    message="Hotel search unavailable"
                )


        # -------------------------------------------------
        # 3. Live data — flights/weather/currency
        # -------------------------------------------------

        if live_result:
            category = query.category

            if category == "flight":
                # live_result contains all/cheapest/fastest/recommended
                recommended = live_result.get("recommended", [])
                flights = [
                    self._serialize_flight(f, state.currency) for f in recommended
                ]
                agent_statuses.append(
                    AgentStatus(
                        agent="flights", status="done",
                        message=f"{len(flights)} flights found"
                    )
                )


        # -------------------------------------------------
        # 4. Build Full Trip — when explicitly requested or all info ready
        # -------------------------------------------------

        from app.services.missing_information import MissingInformationDetector
        has_minimum_state = bool(
            (state.destinations or state.cities)
            and state.duration_days
            and not MissingInformationDetector.detect(state)
        )
        is_build_request = (
            self._is_build_trip_request(query.question)
            or (has_minimum_state and not state.itinerary)
            or "build my full itinerary now" in (query.question or "").lower()
        )

        weather_data: dict | None = None

        if has_minimum_state and (is_build_request or not state.itinerary):

            # Flights (auto-search from origin to destination if origin is known)
            if not flights and state.origin and (state.destinations or state.cities):
                agent_statuses.append(
                    AgentStatus(agent="flights", status="working", message="Searching flights...")
                )
                try:
                    from datetime import date, timedelta
                    dep_date = state.start_date or (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
                    dest_name = state.destinations[0] if state.destinations else state.cities[0]
                    pax = state.travelers or 1
                    raw_flights = self.flight_service.search_flights(
                        origin=state.origin,
                        destination=dest_name,
                        departure_date=dep_date,
                        passengers=pax,
                    )
                    if raw_flights:
                        ranked = FlightRanker.balanced(raw_flights, limit=5) or raw_flights[:5]
                        flights = [self._serialize_flight(f, state.currency) for f in ranked]
                        agent_statuses[-1] = AgentStatus(
                            agent="flights", status="done",
                            message=f"{len(flights)} flights found"
                        )
                    else:
                        agent_statuses[-1] = AgentStatus(
                            agent="flights", status="done",
                            message="No flights found for route"
                        )
                except Exception as e:
                    print(f"[Orchestrator] Flight auto-search error: {e}")
                    agent_statuses[-1] = AgentStatus(
                        agent="flights", status="failed",
                        message="Flight search unavailable"
                    )

            # Weather (auto-fetch destination weather)
            if state.destinations or state.cities:
                try:
                    dest_city = state.cities[0] if state.cities else state.destinations[0]
                    weather_data = self.weather_service.get_current_weather(dest_city)
                    agent_statuses.append(
                        AgentStatus(agent="weather", status="done", message=f"Weather retrieved for {dest_city}")
                    )
                except Exception as e:
                    print(f"[Orchestrator] Weather fetch error: {e}")

            # Activities
            agent_statuses.append(
                AgentStatus(agent="activities", status="working", message="Finding activities...")
            )
            try:
                activity_result = self.activity_agent.generate_activities(state)
                activities = activity_result.get("activities", [])
                agent_statuses[-1] = AgentStatus(
                    agent="activities", status="done",
                    message=f"{len(activities)} activities found"
                )
            except Exception as e:
                print(f"[Orchestrator] Activity agent error: {e}")
                agent_statuses[-1] = AgentStatus(
                    agent="activities", status="failed",
                    message="Activity generation failed"
                )

            # Hotels (if not already fetched)
            if not hotels and (state.destinations or state.cities):
                agent_statuses.append(
                    AgentStatus(agent="hotel", status="working", message="Searching hotels...")
                )
                try:
                    hotel_result = self.hotel_agent.search(state)
                    raw_hotels = hotel_result.get("hotels", [])
                    hotels = [self._serialize_hotel(h, state.currency) for h in raw_hotels]
                    agent_statuses[-1] = AgentStatus(
                        agent="hotel", status="done",
                        message=f"{len(hotels)} hotels found"
                    )
                except Exception as e:
                    print(f"[Orchestrator] Hotel agent error: {e}")
                    agent_statuses[-1] = AgentStatus(
                        agent="hotel", status="failed",
                        message="Hotel search unavailable"
                    )

            # Itinerary
            agent_statuses.append(
                AgentStatus(agent="itinerary", status="working", message="Building itinerary...")
            )
            try:
                itinerary_result = self.itinerary_agent.build(
                    state=state,
                    activities=activities,
                    hotels=hotels
                )
                itinerary = itinerary_result.get("itinerary", [])
                agent_statuses[-1] = AgentStatus(
                    agent="itinerary", status="done",
                    message=f"{len(itinerary)}-day itinerary ready"
                )
            except Exception as e:
                print(f"[Orchestrator] Itinerary agent error: {e}")
                agent_statuses[-1] = AgentStatus(
                    agent="itinerary", status="failed",
                    message="Itinerary generation failed"
                )

            # Budget
            agent_statuses.append(
                AgentStatus(agent="budget", status="working", message="Calculating budget...")
            )
            try:
                budget = self.budget_agent.estimate(
                    state=state,
                    flights=flights,
                    hotels=hotels,
                    itinerary=itinerary,
                    activities=activities
                )
                agent_statuses[-1] = AgentStatus(
                    agent="budget", status="done",
                    message="Budget calculated"
                )
            except Exception as e:
                print(f"[Orchestrator] Budget agent error: {e}")
                agent_statuses[-1] = AgentStatus(
                    agent="budget", status="failed",
                    message="Budget calculation failed"
                )


        # -------------------------------------------------
        # 5. Budget-only request
        # -------------------------------------------------

        elif self._is_budget_request(query.question) and has_minimum_state:
            agent_statuses.append(
                AgentStatus(agent="budget", status="working", message="Calculating budget...")
            )
            try:
                budget = self.budget_agent.estimate(
                    state=state,
                    flights=flights,
                    hotels=hotels,
                    itinerary=[],
                    activities=state.activities or []
                )
                agent_statuses[-1] = AgentStatus(
                    agent="budget", status="done",
                    message="Budget estimated"
                )
            except Exception as e:
                print(f"[Orchestrator] Budget agent error: {e}")
                agent_statuses[-1] = AgentStatus(
                    agent="budget", status="failed",
                    message="Budget calculation failed"
                )


        # -------------------------------------------------
        # 6. Activity-only request
        # -------------------------------------------------

        elif self._is_activity_request(query.question) and has_minimum_state:
            agent_statuses.append(
                AgentStatus(agent="activities", status="working", message="Finding activities...")
            )
            try:
                activity_result = self.activity_agent.generate_activities(state)
                activities = activity_result.get("activities", [])
                agent_statuses[-1] = AgentStatus(
                    agent="activities", status="done",
                    message=f"{len(activities)} activities found"
                )
            except Exception as e:
                print(f"[Orchestrator] Activity agent error: {e}")
                agent_statuses[-1] = AgentStatus(
                    agent="activities", status="failed",
                    message="Activity generation failed"
                )


        # -------------------------------------------------
        # 7. Map data — build from state.locations + legs
        # -------------------------------------------------

        map_data = self._build_map_data(state, hotels, activities, itinerary)


        return {
            "agent_statuses": agent_statuses,
            "flights": flights,
            "hotels": hotels,
            "activities": activities,
            "itinerary": itinerary,
            "budget": budget,
            "weather": weather_data,
            "map_data": map_data,
            "research_answer": research_answer,
            "research_sources": research_sources,
        }



    # =================================================
    # Build Map Data
    # =================================================

    def _build_map_data(
        self,
        state: TravelState,
        hotels: list[dict],
        activities: list[dict],
        itinerary: list[dict]
    ) -> MapData | None:

        markers: list[MapMarker] = []
        routes: list[MapRoute] = []
        known_names: set[str] = set()

        # 1. Destination markers from state.locations
        for i, loc in enumerate(state.locations):
            if loc.latitude and loc.longitude:
                markers.append(MapMarker(
                    id=f"dest_{i}",
                    name=loc.name,
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    marker_type="destination",
                    description=loc.country or "Destination"
                ))
                known_names.add(loc.name.lower())

        # Fallback: resolve from state.destinations / cities if locations list is empty
        all_dests = (state.destinations or []) + (state.cities or [])
        for d in all_dests:
            if d.lower() not in known_names:
                geo = GeoService.find_location(d)
                if geo and geo.latitude and geo.longitude:
                    markers.append(MapMarker(
                        id=f"dest_fb_{d}",
                        name=geo.name,
                        latitude=geo.latitude,
                        longitude=geo.longitude,
                        marker_type="destination",
                        description=geo.country or "Destination"
                    ))
                    known_names.add(d.lower())

        # 2. Origin marker & flight route
        if state.origin:
            orig_geo = GeoService.find_location(state.origin)
            if orig_geo and orig_geo.latitude and orig_geo.longitude:
                markers.append(MapMarker(
                    id="origin_loc",
                    name=f"Origin: {orig_geo.name}",
                    latitude=orig_geo.latitude,
                    longitude=orig_geo.longitude,
                    marker_type="airport",
                    description=f"Departure from {orig_geo.name}"
                ))
                # Add route to first destination
                dest_markers = [m for m in markers if m.marker_type == "destination"]
                if dest_markers:
                    dest_m = dest_markers[0]
                    routes.append(MapRoute(
                        from_name=orig_geo.name,
                        to_name=dest_m.name,
                        from_lat=orig_geo.latitude,
                        from_lng=orig_geo.longitude,
                        to_lat=dest_m.latitude,
                        to_lng=dest_m.longitude,
                        transport_type="flight",
                        order=0
                    ))

        # 3. Hotel markers (fallback to state.hotels if empty)
        active_hotels = hotels if hotels else (state.hotels or [])
        for i, hotel in enumerate(active_hotels[:6]):
            lat = hotel.get("latitude")
            lng = hotel.get("longitude")
            if lat and lng:
                markers.append(MapMarker(
                    id=f"hotel_{i}",
                    name=hotel.get("name", "Hotel"),
                    latitude=lat,
                    longitude=lng,
                    marker_type="hotel",
                    description=(
                        f"★{hotel.get('stars', '?')} | "
                        f"{hotel.get('price', '?')} {hotel.get('currency', '')}"
                    )
                ))

        # 4. Activity markers (exclude restaurant markers to keep map view focused & clean)
        active_activities = activities if activities else (state.activities or [])
        dest_m = next((m for m in markers if m.marker_type == "destination"), None)
        if dest_m and active_activities:
            import math
            filtered_activities = [
                a for a in active_activities
                if not any(k in (a.get("type") or "").lower() for k in ["restaurant", "dining", "food"])
            ]
            for i, act in enumerate(filtered_activities[:10]):
                angle = (i * (2 * math.pi / max(1, min(len(filtered_activities), 10))))
                radius = 0.015 + (i * 0.005)  # ~1.5 - 4km spread
                act_lat = dest_m.latitude + (radius * math.cos(angle))
                act_lng = dest_m.longitude + (radius * math.sin(angle) * 1.2)
                markers.append(MapMarker(
                    id=f"act_{i}",
                    name=act.get("name", "Attraction"),
                    latitude=act_lat,
                    longitude=act_lng,
                    marker_type="activity",
                    day=act.get("day_suggestion"),
                    description=act.get("type", "Sightseeing").capitalize() + (f" · {act.get('area')}" if act.get('area') else "")
                ))


        # 5. Route legs from state.travel_legs
        for leg in state.travel_legs:
            f = leg.from_location
            t = leg.to_location
            if all([
                f.latitude, f.longitude,
                t.latitude, t.longitude
            ]):
                routes.append(MapRoute(
                    from_name=f.name,
                    to_name=t.name,
                    from_lat=f.latitude,
                    from_lng=f.longitude,
                    to_lat=t.latitude,
                    to_lng=t.longitude,
                    transport_type="flight",
                    order=leg.order
                ))

        if not markers and not routes:
            return None

        # Calculate map center
        if markers:
            avg_lat = sum(m.latitude for m in markers) / len(markers)
            avg_lng = sum(m.longitude for m in markers) / len(markers)
        else:
            avg_lat = avg_lng = None

        zoom = 4 if len(markers) > 1 else 11

        return MapData(
            markers=markers,
            routes=routes,
            center_lat=avg_lat,
            center_lng=avg_lng,
            zoom=zoom
        )


    # =================================================
    # Intent Detection Helpers
    # =================================================

    def _is_hotel_request(self, text: str) -> bool:
        text = text.lower()
        keywords = [
            "hotel", "hotels", "accommodation", "stay",
            "where to stay", "place to stay", "hostel",
            "airbnb", "resort", "lodge"
        ]
        return any(k in text for k in keywords)

    def _is_build_trip_request(self, text: str) -> bool:
        if not text:
            return False
        text = text.lower().strip()
        keywords = [
            "build my trip", "plan my trip", "create itinerary",
            "full itinerary", "complete trip", "plan everything",
            "build itinerary", "generate trip", "make a plan",
            "plan the trip", "full plan", "plan my vacation",
            "plan a trip", "plan a ", "plan my", "plan vacation",
            "plan holiday", "build a trip", "design my trip",
            "build my full itinerary now", "build full itinerary",
            "build my itinerary", "generate itinerary", "generate my itinerary",
            "want to go", "want to visit", "trip to", "travel to", "going to",
            "planning to", "planning a trip", "vacation to", "holiday in",
        ]
        if any(k in text for k in keywords):
            return True
        import re
        if re.search(r'(?:plan|build|create|generate|want to go|going to|travel to|visit)\s+.*(?:trip|vacation|getaway|holiday|itinerary|visit|tour|days|budget)', text):
            return True
        if re.search(r'\b\d+\s*(?:day|night|d|n)\b', text) and any(w in text for w in ["budget", "hotel", "wife", "husband", "friend", "family", "delhi", "mumbai", "paris", "tokyo"]):
            return True
        return False

    def _is_budget_request(self, text: str) -> bool:
        text = text.lower()
        keywords = [
            "budget", "cost", "how much", "price", "spend",
            "expensive", "cheap", "afford", "estimate"
        ]
        return any(k in text for k in keywords)

    def _is_activity_request(self, text: str) -> bool:
        text = text.lower()
        keywords = [
            "what to do", "things to do", "activities",
            "sightseeing", "places to visit", "attractions",
            "what should i see", "what should i do",
            "recommend", "suggestions", "must see", "must do"
        ]
        return any(k in text for k in keywords)


    # =================================================
    # Serialize Flight for JSON
    # =================================================

    def _serialize_flight(self, flight, target_currency: str | None = None) -> dict:
        """Convert TransportationOption to dict for JSON response with currency conversion."""
        try:
            raw_price = flight.price
            raw_curr = (flight.currency or "USD").upper()
            curr = (target_currency or raw_curr).upper()
            price = raw_price

            if raw_price is not None and curr != raw_curr:
                try:
                    rate = self.currency_service.get_rate(raw_curr, curr)
                    converted = raw_price * rate
                    price = float(round(converted)) if curr in ["INR", "JPY", "KRW", "IDR", "THB"] else round(converted, 2)
                except Exception:
                    price = raw_price
                    curr = raw_curr

            return {
                "provider": flight.provider,
                "origin": flight.origin,
                "destination": flight.destination,
                "departure": (
                    flight.departure.isoformat()
                    if flight.departure else None
                ),
                "arrival": (
                    flight.arrival.isoformat()
                    if flight.arrival else None
                ),
                "duration_minutes": flight.duration_minutes,
                "stops": flight.stops,
                "price": price,
                "currency": curr,
                "option_id": flight.option_id,
            }
        except AttributeError:
            if isinstance(flight, dict):
                return flight
            return {}

    def _serialize_hotel(self, hotel: dict, target_currency: str | None = None) -> dict:
        """Convert hotel dict ensuring price is converted to target_currency."""
        if not isinstance(hotel, dict):
            return {}
        h = dict(hotel)
        raw_price = h.get("price")
        raw_curr = (h.get("currency") or "USD").upper()
        curr = (target_currency or raw_curr).upper()

        if raw_price is not None and curr != raw_curr:
            try:
                rate = self.currency_service.get_rate(raw_curr, curr)
                converted = float(raw_price) * rate
                h["price"] = float(round(converted)) if curr in ["INR", "JPY", "KRW", "IDR", "THB"] else round(converted, 2)
                h["currency"] = curr
            except Exception:
                pass
        return h
