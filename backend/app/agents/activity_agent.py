"""Activity recommendation agent — generates activities using RAG + LLM with multi-currency support and budget optimization."""

import json
from app.models.travel_state import TravelState
from app.rag.rag_services import RAGService
from app.services.llm_service import LLMService
from app.services.currency_services import CurrencyService


class ActivityAgent:

    def __init__(
        self,
        rag_service: RAGService,
        llm_service: LLMService,
        currency_service: CurrencyService | None = None
    ):
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.currency_service = currency_service or CurrencyService()

    def _round_amount(self, amount: float, currency: str) -> float:
        """Round currency amounts appropriately."""
        zero_decimal_currencies = {"INR", "JPY", "KRW", "IDR", "VND", "THB"}
        if currency.upper() in zero_decimal_currencies:
            return float(round(amount))
        return round(amount, 2)

    # =================================================
    # Generate Activities
    # =================================================

    def generate_activities(
        self,
        state: TravelState
    ) -> dict:
        """
        Generate a list of activities for the trip.
        Uses RAG for destination knowledge + LLM to structure output,
        with realistic costs in state.currency.
        """

        destination = (
            state.destinations[0]
            if state.destinations
            else (state.cities[0] if state.cities else None)
        )

        if not destination:
            return {
                "agent": "activity",
                "status": "error",
                "message": "No destination for activity generation.",
                "activities": []
            }

        duration = state.duration_days or 7
        travelers = state.travelers or 2
        interests = state.interests or []
        interests_str = (
            ", ".join(interests) if interests else "general sightseeing"
        )
        target_currency = (state.currency or "USD").upper()

        # Exchange rate USD -> Target Currency
        try:
            usd_to_curr = self.currency_service.get_rate("USD", target_currency)
        except Exception:
            usd_to_curr = 1.0

        # -------------------------------------------------
        # Get RAG context for destination
        # -------------------------------------------------

        rag_question = (
            f"Top things to do in {destination}. "
            f"Interests: {interests_str}. "
            f"Highlight unique local experiences, cultural sites, food, "
            f"and must-see attractions."
        )

        rag_context = ""
        try:
            rag_result = self.rag_service.answer_with_state(
                question=rag_question,
                state=state,
                top_k=5
            )
            rag_context = rag_result.get("answer", "")
        except Exception as e:
            print(f"[ActivityAgent] RAG error: {e}")

        # -------------------------------------------------
        # LLM prompt to generate structured activities
        # -------------------------------------------------

        prompt = f"""You are a specialist travel activity planner for TravelOS.

Destination: {destination}
Trip duration: {duration} days
Travelers: {travelers} people
Traveler interests: {interests_str}
Travel style: {state.travel_style or "balanced"}
Target Currency: {target_currency}

Knowledge base context:
{rag_context}

Generate a list of {min(duration * 3, 18)} specific activities for this trip.

Rules:
- Activities must be real, specific places or experiences in {destination}
- Match activities to the traveler's interests: {interests_str}
- Include a diverse mix: free walking/sightseeing, cultural heritage, foodie markets, nature/parks, and a few premium adventures
- Provide realistic approximate price per person in {target_currency} (e.g. free attractions = 0, temple entries / museums = modest cost, premium day tours = higher cost)
- Mark cost_tier accurately: "budget" (free to low cost), "moderate" (standard admission/meals), "premium" (full-day tours, luxury or paid adventures)
- Spread activities across different days (1 to {duration})

Return a JSON array. Each activity object:
{{
  "id": "act_1",
  "name": "Activity name",
  "type": "cultural|food|nature|shopping|entertainment|sightseeing|adventure",
  "description": "1-2 sentence vivid description",
  "duration_hours": 2,
  "estimated_cost_per_person": 1500,
  "cost_currency": "{target_currency}",
  "cost_tier": "budget|moderate|premium",
  "cost_note": "approximate per person",
  "day_suggestion": 1,
  "area": "district or area name",
  "highlights": ["highlight1", "highlight2"],
  "best_time": "morning|afternoon|evening|any"
}}

Return ONLY valid JSON array, no markdown, no explanation."""

        try:
            raw = self.llm_service.generate_response(prompt)
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1])

            activities = json.loads(raw)
            if not isinstance(activities, list):
                activities = []

            # Ensure all currency and cost formatting is clean
            for i, act in enumerate(activities):
                if not act.get("id"):
                    act["id"] = f"act_{i+1}"
                act["cost_currency"] = target_currency
                raw_cost = float(act.get("estimated_cost_per_person", 0))
                act["estimated_cost_per_person"] = self._round_amount(raw_cost, target_currency)
                
                # Assign cost tier if missing
                if not act.get("cost_tier"):
                    cost_in_usd = raw_cost / (usd_to_curr if usd_to_curr > 0 else 1.0)
                    if cost_in_usd <= 15:
                        act["cost_tier"] = "budget"
                    elif cost_in_usd <= 50:
                        act["cost_tier"] = "moderate"
                    else:
                        act["cost_tier"] = "premium"

        except Exception as e:
            print(f"[ActivityAgent] LLM error: {e}")
            activities = []

        return {
            "agent": "activity",
            "status": "done",
            "destination": destination,
            "activities": activities
        }

    # =================================================
    # Find Expensive Activities
    # =================================================

    def find_expensive_activities(
        self,
        activities: list[dict],
        state: TravelState,
        top_n: int = 3
    ) -> list[dict]:
        """
        Identify top most expensive activities for the trip,
        calculating individual and total group costs.
        """
        if not activities:
            return []

        travelers = max(1, state.travelers or 2)
        target_currency = (state.currency or "USD").upper()

        sorted_acts = sorted(
            activities,
            key=lambda a: float(a.get("estimated_cost_per_person", 0)),
            reverse=True
        )

        expensive_list = []
        for act in sorted_acts[:top_n]:
            cost_pp = float(act.get("estimated_cost_per_person", 0))
            if cost_pp <= 0:
                continue
            total_group_cost = cost_pp * travelers
            expensive_list.append({
                "id": act.get("id"),
                "name": act.get("name"),
                "cost_per_person": cost_pp,
                "total_group_cost": total_group_cost,
                "currency": target_currency,
                "type": act.get("type", "activity"),
                "area": act.get("area", ""),
                "day_suggestion": act.get("day_suggestion"),
                "cost_tier": act.get("cost_tier", "premium"),
                "description": act.get("description", "")
            })

        return expensive_list

    # =================================================
    # Replace Activity with Cheaper Alternative
    # =================================================

    def replace_activity_with_cheaper_option(
        self,
        state: TravelState,
        old_activity: dict,
        current_activities: list[dict]
    ) -> dict | None:
        """
        Generate a budget-friendly or free replacement for an expensive activity.
        """
        destination = (
            state.destinations[0]
            if state.destinations
            else (state.cities[0] if state.cities else "the destination")
        )
        target_currency = (state.currency or "USD").upper()
        old_name = old_activity.get("name", "Current Activity")
        old_area = old_activity.get("area", "central area")
        old_type = old_activity.get("type", "sightseeing")
        old_cost = float(old_activity.get("estimated_cost_per_person", 0))
        day = old_activity.get("day_suggestion", 1)

        prompt = f"""You are a travel budget specialist.
A traveler wants to replace an expensive activity with a high-quality, budget-friendly or FREE alternative in {destination}.

Expensive Activity to replace:
- Name: {old_name}
- Type: {old_type}
- Area/District: {old_area}
- Current Cost: {old_cost} {target_currency} per person
- Day: Day {day}

Suggest ONE authentic, exciting, but very affordable or free alternative (e.g. scenic public observation deck, free temple garden, walking tour, street food market, cultural district walk).
Cost must be substantially lower than {old_cost} {target_currency} (ideally 0 to 25% of the old cost).

Return a JSON object:
{{
  "id": "act_rep_{day}",
  "name": "New Budget Activity Name",
  "type": "{old_type}",
  "description": "1-2 sentence description highlighting why it's a great budget-friendly experience",
  "duration_hours": 2,
  "estimated_cost_per_person": 0,
  "cost_currency": "{target_currency}",
  "cost_tier": "budget",
  "cost_note": "free entry / low cost alternative",
  "day_suggestion": {day},
  "area": "{old_area}",
  "highlights": ["highlight 1", "highlight 2"],
  "best_time": "afternoon"
}}

Return ONLY valid JSON, no markdown."""

        try:
            raw = self.llm_service.generate_response(prompt)
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1])

            replacement = json.loads(raw)
            if isinstance(replacement, dict):
                replacement["cost_currency"] = target_currency
                raw_cost = float(replacement.get("estimated_cost_per_person", 0))
                replacement["estimated_cost_per_person"] = self._round_amount(raw_cost, target_currency)
                replacement["cost_tier"] = "budget"
                return replacement
        except Exception as e:
            print(f"[ActivityAgent] Replacement error: {e}")

        # Fallback replacement
        return {
            "id": f"act_rep_{day}",
            "name": f"Free Walking & Cultural Exploration in {old_area}",
            "type": old_type,
            "description": f"Scenic self-guided walking exploration and photography around {old_area}.",
            "duration_hours": 2,
            "estimated_cost_per_person": 0.0,
            "cost_currency": target_currency,
            "cost_tier": "budget",
            "cost_note": "free",
            "day_suggestion": day,
            "area": old_area,
            "highlights": ["Historic architecture", "Scenic viewpoints"],
            "best_time": "afternoon"
        }
