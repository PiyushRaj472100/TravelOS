"""Itinerary planning agent — builds day-by-day structured itinerary with multi-currency support."""

import json

from app.models.travel_state import TravelState
from app.services.llm_service import LLMService
from app.services.currency_services import CurrencyService


class ItineraryAgent:

    def __init__(
        self,
        llm_service: LLMService,
        currency_service: CurrencyService | None = None
    ):
        self.llm_service = llm_service
        self.currency_service = currency_service or CurrencyService()

    def _round_amount(self, amount: float, currency: str) -> float:
        """Round currency amounts appropriately."""
        zero_decimal_currencies = {"INR", "JPY", "KRW", "IDR", "VND", "THB"}
        if currency.upper() in zero_decimal_currencies:
            return float(round(amount))
        return round(amount, 2)

    # =================================================
    # Build Itinerary
    # =================================================

    def build(
        self,
        state: TravelState,
        activities: list[dict] | None = None,
        hotels: list[dict] | None = None
    ) -> dict:
        """
        Build a day-by-day itinerary from TravelState + activities + hotels.
        """

        destination = (
            state.destinations[0]
            if state.destinations
            else (state.cities[0] if state.cities else "the destination")
        )

        duration = state.duration_days or 7
        start_date = state.start_date or "your departure date"
        travelers = state.travelers or 2
        interests = ", ".join(state.interests) if state.interests else "sightseeing"
        target_currency = (state.currency or "USD").upper()

        # Format activities for prompt
        activities_text = ""
        if activities:
            acts = activities[:15]
            activities_text = "\n".join([
                f"- {a.get('name', '')} ({a.get('type', '')}): "
                f"{a.get('description', '')} "
                f"[{a.get('duration_hours', 2)}h, "
                f"cost: {a.get('estimated_cost_per_person', 0)} {target_currency}, "
                f"area: {a.get('area', 'central')}]"
                for a in acts
            ])

        # Selected hotel info
        hotel_text = ""
        if hotels:
            h = hotels[0]
            hotel_text = (
                f"Hotel: {h.get('name', '')} "
                f"({'★' * int(h.get('stars') or 3)} stars)"
            )

        prompt = f"""You are an expert travel itinerary planner for TravelOS.

Destination: {destination}
Duration: {duration} days
Start date: {start_date}
Travelers: {travelers}
Interests: {interests}
Travel style: {state.travel_style or "balanced"}
Accommodation preference: {state.accommodation_preference or "hotel"}
Target Currency: {target_currency}
{hotel_text}

Available activities:
{activities_text if activities_text else "Generate appropriate activities for this destination."}

Build a complete {duration}-day itinerary for this trip.

Rules:
- Each day must have a clear theme (e.g., "Tokyo highlights", "Mount Fuji day trip")
- Include morning, afternoon, and evening slots
- Account for travel time between locations
- Day 1 should include arrival and check-in
- Last day should include check-out and departure logistics
- Include specific meal recommendations (breakfast spot, lunch, dinner)
- Keep the pace realistic — maximum 4-5 activities per day
- Group activities by geographical area to minimize travel
- Provide estimated daily cost per person in {target_currency}

Return a JSON array of day objects:
[
  {{
    "day": 1,
    "date": "2026-09-15",
    "theme": "Arrival & First Impressions",
    "morning": {{
      "time": "09:00",
      "activity": "Activity name",
      "description": "Brief description",
      "duration_hours": 2,
      "type": "cultural|food|transport|etc",
      "area": "area name"
    }},
    "afternoon": {{
      "time": "13:00",
      "activity": "Activity name",
      "description": "Brief description",
      "duration_hours": 3,
      "type": "sightseeing",
      "area": "area name"
    }},
    "evening": {{
      "time": "18:00",
      "activity": "Dinner at local restaurant",
      "description": "Brief description",
      "duration_hours": 2,
      "type": "food",
      "area": "area name"
    }},
    "meals": {{
      "breakfast": "Coffee and toast at hotel",
      "lunch": "Ramen at Ichiran",
      "dinner": "Yakitori near Shinjuku"
    }},
    "tips": ["Useful tip for this day"],
    "estimated_daily_cost": 5000,
    "cost_currency": "{target_currency}"
  }}
]

Return ONLY valid JSON array, no markdown, no explanation."""

        try:
            raw = self.llm_service.generate_response(prompt)

            # Strip markdown if present
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1])

            itinerary = json.loads(raw)

            if not isinstance(itinerary, list):
                itinerary = []

            for day in itinerary:
                day["cost_currency"] = target_currency
                if "estimated_daily_cost" in day and day["estimated_daily_cost"] is not None:
                    day["estimated_daily_cost"] = self._round_amount(
                        float(day["estimated_daily_cost"]), target_currency
                    )

        except Exception as e:
            print(f"[ItineraryAgent] LLM error: {e}")
            itinerary = self._fallback_itinerary(destination, duration, target_currency)

        return {
            "agent": "itinerary",
            "status": "done",
            "destination": destination,
            "duration_days": duration,
            "itinerary": itinerary
        }

    # =================================================
    # Fallback Itinerary
    # =================================================

    def _fallback_itinerary(
        self,
        destination: str,
        duration: int,
        currency: str = "USD"
    ) -> list[dict]:
        """Minimal fallback if LLM fails."""

        return [
            {
                "day": i + 1,
                "theme": f"Day {i + 1} in {destination}",
                "morning": {
                    "activity": "Explore the area",
                    "description": "Start your day with local exploration",
                    "type": "sightseeing"
                },
                "afternoon": {
                    "activity": "Visit local attractions",
                    "description": "Afternoon at key sites",
                    "type": "cultural"
                },
                "evening": {
                    "activity": "Local dinner",
                    "description": "Experience local cuisine",
                    "type": "food"
                },
                "cost_currency": currency
            }
            for i in range(duration)
        ]
