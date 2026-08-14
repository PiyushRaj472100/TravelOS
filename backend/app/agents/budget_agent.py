"""Budget planning agent — estimates realistic destination-aware trip costs and tracks allocation with full multi-currency FX conversion."""

from app.models.travel_state import TravelState
from app.models.chat import BudgetBreakdown, BudgetItem
from app.services.currency_services import CurrencyService


class BudgetAgent:

    # Per-person-per-day cost estimates in base USD
    DESTINATION_TIERS = {
        # Budget destinations (e.g. Thailand, Vietnam, Bali, India)
        "budget": {
            "flight_per_person_intl": 450,
            "flight_per_person_regional": 180,
            "hotel_per_night_room": 45,
            "food_per_day": 20,
            "activities_per_day": 18,
            "transport_per_day": 10,
        },
        # Mid-range (e.g. Southern Europe, South Korea, UAE, Brazil, South Africa)
        "mid": {
            "flight_per_person_intl": 750,
            "flight_per_person_regional": 300,
            "hotel_per_night_room": 110,
            "food_per_day": 45,
            "activities_per_day": 35,
            "transport_per_day": 20,
        },
        # Expensive destinations (e.g. Japan, Switzerland, UK, USA, Singapore, Norway, Australia)
        "expensive": {
            "flight_per_person_intl": 1150,
            "flight_per_person_regional": 450,
            "hotel_per_night_room": 180,
            "food_per_day": 70,
            "activities_per_day": 55,
            "transport_per_day": 30,
        },
    }

    EXPENSIVE_DESTINATIONS = {
        "japan", "tokyo", "kyoto", "osaka", "hokkaido", "switzerland", "zurich", "geneva",
        "norway", "oslo", "denmark", "copenhagen", "sweden", "stockholm",
        "singapore", "hong kong", "dubai", "london", "uk", "united kingdom", "paris", "france",
        "new york", "usa", "united states", "san francisco", "los angeles", "sydney", "melbourne", "australia",
        "iceland", "reykjavik", "monaco", "maldives"
    }

    BUDGET_DESTINATIONS = {
        "vietnam", "hanoi", "ho chi minh", "thailand", "bangkok", "phuket",
        "chiang mai", "india", "delhi", "mumbai", "goa", "nepal", "kathmandu",
        "cambodia", "phnom penh", "indonesia", "bali", "jakarta",
        "philippines", "manila", "morocco", "marrakech", "egypt", "cairo"
    }

    def __init__(self, currency_service: CurrencyService | None = None):
        self.currency_service = currency_service or CurrencyService()

    def _round_amount(self, amount: float, currency: str) -> float:
        """Round currency amounts appropriately (integers for JPY, INR, KRW, IDR)."""
        zero_decimal_currencies = {"INR", "JPY", "KRW", "IDR", "VND", "THB"}
        if currency.upper() in zero_decimal_currencies:
            return float(round(amount))
        return round(amount, 2)

    def estimate(
        self,
        state: TravelState,
        flights: list[dict] | None = None,
        hotels: list[dict] | None = None,
        itinerary: list[dict] | None = None,
        activities: list[dict] | None = None
    ) -> BudgetBreakdown:
        """
        Estimate total trip budget.

        Uses live prices for flights + hotels when available, converts them
        into state.currency, and estimates food, activities, and local transit
        tailored to destination cost tier, travelers, duration, and user interests.
        """

        target_currency = (state.currency or "USD").upper()
        duration = max(1, state.duration_days or 7)
        travelers = max(1, state.travelers or 2)
        rooms_needed = max(1, (travelers + 1) // 2)

        # Get USD -> Target Currency exchange rate
        try:
            usd_to_target_rate = self.currency_service.get_rate("USD", target_currency)
        except Exception:
            usd_to_target_rate = 1.0

        # Determine destination cost tier
        tier = self._get_destination_tier(state)
        tier_costs = self.DESTINATION_TIERS[tier]

        # -------------------------------------------------
        # 1. Flights (Live or Realistic Distance-Aware Estimate)
        # -------------------------------------------------
        flight_cost = None
        flight_is_live = False

        if flights:
            best_flight = next((f for f in flights if f.get("price")), None)
            if best_flight:
                raw_price = float(best_flight.get("price", 0))
                flight_curr = (best_flight.get("currency") or "USD").upper()
                try:
                    curr_to_target = self.currency_service.get_rate(flight_curr, target_currency)
                    price_in_target = raw_price * curr_to_target
                except Exception:
                    price_in_target = raw_price * usd_to_target_rate

                flight_cost = price_in_target * travelers
                flight_is_live = True

        if flight_cost is None:
            is_domestic = bool(state.origin and any(
                d.lower() in state.origin.lower() for d in (state.destinations or [])
            ))
            base_flight_usd = (
                tier_costs["flight_per_person_regional"]
                if is_domestic
                else tier_costs["flight_per_person_intl"]
            )
            flight_cost = (base_flight_usd * travelers) * usd_to_target_rate

        # -------------------------------------------------
        # 2. Hotels (Live or Tier-Aware Estimate)
        # -------------------------------------------------
        hotel_cost = None
        hotel_is_live = False

        if hotels:
            best_hotel = next((h for h in hotels if h.get("price")), None)
            if best_hotel:
                raw_price = float(best_hotel.get("price", 0))
                hotel_curr = (best_hotel.get("currency") or "USD").upper()
                try:
                    curr_to_target = self.currency_service.get_rate(hotel_curr, target_currency)
                    price_in_target = raw_price * curr_to_target
                except Exception:
                    price_in_target = raw_price * usd_to_target_rate

                hotel_cost = price_in_target * duration * rooms_needed
                hotel_is_live = True

        if hotel_cost is None:
            base_hotel_usd = tier_costs["hotel_per_night_room"]
            if state.accommodation_preference:
                pref = state.accommodation_preference.lower()
                if "luxury" in pref or "5 star" in pref:
                    base_hotel_usd *= 1.8
                elif "budget" in pref or "hostel" in pref:
                    base_hotel_usd *= 0.5
            hotel_cost = (base_hotel_usd * duration * rooms_needed) * usd_to_target_rate

        # -------------------------------------------------
        # 3. Food & Dining
        # -------------------------------------------------
        base_food_usd = tier_costs["food_per_day"]
        if state.food_preferences:
            base_food_usd *= 1.15
        food_cost = (base_food_usd * travelers * duration) * usd_to_target_rate

        # -------------------------------------------------
        # 4. Activities & Attractions / Adventures
        # -------------------------------------------------
        active_activities = activities if activities is not None else (state.activities or [])
        if active_activities:
            # Sum actual activities
            total_act_sum = 0.0
            for act in active_activities:
                act_cost = act.get("estimated_cost_per_person", 0)
                act_curr = (act.get("cost_currency") or target_currency).upper()
                if act_curr != target_currency:
                    try:
                        act_rate = self.currency_service.get_rate(act_curr, target_currency)
                        act_cost = float(act_cost) * act_rate
                    except Exception:
                        pass
                total_act_sum += float(act_cost)
            activity_cost = total_act_sum * travelers
        else:
            base_act_usd = tier_costs["activities_per_day"]
            if state.interests:
                # More active interests increase adventure budget
                if any(i in ["adventure", "nightlife", "luxury", "theme parks", "tours"] for i in state.interests):
                    base_act_usd *= 1.25
            activity_cost = (base_act_usd * travelers * duration) * usd_to_target_rate

            # If itinerary exists with specific activities count
            if itinerary:
                total_itinerary_acts = sum(
                    len([k for k in ["morning", "afternoon", "evening"] if d.get(k)])
                    for d in itinerary
                )
                if total_itinerary_acts > 0:
                    est_per_act_usd = 22.0 if tier == "expensive" else (14.0 if tier == "mid" else 8.0)
                    activity_cost = max(activity_cost, (total_itinerary_acts * est_per_act_usd * travelers) * usd_to_target_rate)

        # -------------------------------------------------
        # 5. Local Transport
        # -------------------------------------------------
        base_trans_usd = tier_costs["transport_per_day"]
        transport_cost = (base_trans_usd * travelers * duration) * usd_to_target_rate

        # -------------------------------------------------
        # Total & Remaining
        # -------------------------------------------------
        flight_cost = self._round_amount(flight_cost, target_currency)
        hotel_cost = self._round_amount(hotel_cost, target_currency)
        food_cost = self._round_amount(food_cost, target_currency)
        activity_cost = self._round_amount(activity_cost, target_currency)
        transport_cost = self._round_amount(transport_cost, target_currency)

        total_estimated = flight_cost + hotel_cost + food_cost + activity_cost + transport_cost
        total_estimated = self._round_amount(total_estimated, target_currency)

        total_budget = state.budget
        remaining = None
        if total_budget is not None:
            remaining = self._round_amount(total_budget - total_estimated, target_currency)

        cost_per_day = self._round_amount(total_estimated / duration, target_currency)
        cost_per_person = self._round_amount(total_estimated / travelers, target_currency)

        # -------------------------------------------------
        # Build Item Breakdown
        # -------------------------------------------------
        items = [
            BudgetItem(
                label="Flights",
                amount=flight_cost,
                currency=target_currency,
                is_live=flight_is_live
            ),
            BudgetItem(
                label="Hotels",
                amount=hotel_cost,
                currency=target_currency,
                is_live=hotel_is_live
            ),
            BudgetItem(
                label="Food & Dining",
                amount=food_cost,
                currency=target_currency,
                is_live=False
            ),
            BudgetItem(
                label="Activities & Attractions",
                amount=activity_cost,
                currency=target_currency,
                is_live=bool(active_activities)
            ),
            BudgetItem(
                label="Local Transport",
                amount=transport_cost,
                currency=target_currency,
                is_live=False
            ),
        ]

        note = (
            f"Tailored for {travelers} traveler(s), {duration} days in {tier}-tier destination ({rooms_needed} room(s)). "
            + ("Flight & hotel costs from live searches. " if (flight_is_live or hotel_is_live) else "Estimated with destination cost indices.")
        )

        return BudgetBreakdown(
            total_budget=total_budget,
            currency=target_currency,
            flights=flight_cost,
            hotels=hotel_cost,
            food=food_cost,
            activities=activity_cost,
            transport=transport_cost,
            remaining=remaining,
            cost_per_day=cost_per_day,
            cost_per_person=cost_per_person,
            duration_days=duration,
            travelers=travelers,
            items=items,
            note=note
        )

    def _get_destination_tier(self, state: TravelState) -> str:
        all_destinations = (
            state.destinations
            + state.cities
            + state.countries
        )

        for dest in all_destinations:
            dest_lower = dest.lower()
            if any(exp in dest_lower for exp in self.EXPENSIVE_DESTINATIONS):
                return "expensive"
            if any(bud in dest_lower for bud in self.BUDGET_DESTINATIONS):
                return "budget"

        if state.accommodation_preference:
            pref = state.accommodation_preference.lower()
            if "budget" in pref or "hostel" in pref or "cheap" in pref:
                return "budget"
            if "luxury" in pref or "five star" in pref or "5 star" in pref:
                return "expensive"

        return "mid"

    def check_budget_feasibility(self, state: TravelState) -> dict:
        """
        Check if user's budget is physically impossible for the destination, travelers, and duration.
        """
        if state.budget is None:
            return {"is_feasible": True}

        target_currency = (state.currency or "USD").upper()
        duration = max(1, state.duration_days or 3)
        travelers = max(1, state.travelers or 1)

        try:
            usd_to_target_rate = self.currency_service.get_rate("USD", target_currency)
        except Exception:
            usd_to_target_rate = 1.0

        tier = self._get_destination_tier(state)

        # Bare minimum USD baseline costs per person
        if tier == "expensive":
            min_flight_pp = 350.0
            min_stay_pp_day = 40.0 # hostel / budget stay
            min_food_trans_pp_day = 30.0
        elif tier == "mid":
            min_flight_pp = 200.0
            min_stay_pp_day = 25.0
            min_food_trans_pp_day = 20.0
        else: # budget
            min_flight_pp = 80.0
            min_stay_pp_day = 12.0
            min_food_trans_pp_day = 10.0

        total_min_usd = (min_flight_pp * travelers) + ((min_stay_pp_day + min_food_trans_pp_day) * travelers * duration)
        total_min_target = self._round_amount(total_min_usd * usd_to_target_rate, target_currency)

        dest_name = ", ".join(state.destinations or state.cities or ["your destination"])

        if state.budget < total_min_target:
            # Map destination keywords to unsplash imagery
            img_url = "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80"
            dest_lower = dest_name.lower()
            if "korea" in dest_lower or "busan" in dest_lower or "seoul" in dest_lower:
                img_url = "https://images.unsplash.com/photo-1538485399081-7191377e8241?auto=format&fit=crop&w=800&q=80"
            elif "japan" in dest_lower or "tokyo" in dest_lower or "kyoto" in dest_lower:
                img_url = "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=800&q=80"
            elif "thailand" in dest_lower or "bangkok" in dest_lower or "phuket" in dest_lower:
                img_url = "https://images.unsplash.com/photo-1508009603885-50cf7c579365?auto=format&fit=crop&w=800&q=80"
            elif "goa" in dest_lower or "mumbai" in dest_lower or "india" in dest_lower:
                img_url = "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=80"

            reason_msg = (
                f"### 📍 Welcome to {dest_name.title()}\n\n"
                f"![{dest_name}]({img_url})\n\n"
                f"✨ **Why Visit {dest_name.title()}?**\n"
                f"{dest_name.title()} offers breathtaking landscapes, unique cultural heritage, world-class culinary experiences, and iconic landmarks that make it an unforgettable getaway for any traveler.\n\n"
                f"⚠️ **Budget Assessment:**\n"
                f"I cannot plan a complete trip to **{dest_name.title()}** with a budget of **{target_currency} {state.budget:,.0f}**. "
                f"The absolute minimum estimated baseline cost for **{travelers} traveler(s)** for **{duration} day(s)** "
                f"is approximately **{target_currency} {total_min_target:,.0f}** (covering essential transit, budget stay, and basic daily meals).\n\n"
                f"💡 **Suggestions to proceed:**\n"
                f"1. Increase your budget to at least **{target_currency} {total_min_target:,.0f}**.\n"
                f"2. Reduce the number of days (e.g. {max(1, duration - 3)} days) or travelers.\n"
                f"3. Consider a closer or more budget-friendly destination."
            )

            return {
                "is_feasible": False,
                "minimum_required": total_min_target,
                "currency": target_currency,
                "destination": dest_name,
                "reason": reason_msg
            }

        return {"is_feasible": True, "minimum_required": total_min_target, "currency": target_currency}

    def auto_replan_under_budget(
        self,
        state: TravelState,
        hotels: list[dict] | None = None,
        activities: list[dict] | None = None,
        itinerary: list[dict] | None = None
    ) -> dict:
        """
        If budget is genuine but current breakdown exceeds state.budget,
        automatically re-plan components to get strictly under state.budget.
        """
        breakdown = self.estimate(state, hotels=hotels, activities=activities, itinerary=itinerary)
        
        if state.budget is None or breakdown.remaining is None or breakdown.remaining >= 0:
            return {"adjusted": False, "breakdown": breakdown, "adjustments": []}

        target_currency = (state.currency or "USD").upper()
        adjustments = []

        # 1. Adjust accommodation preference to budget / hostel
        state.accommodation_preference = "budget"
        adjustments.append("Updated accommodation preference to budget-friendly stays & hostels")

        # 2. Filter / optimize activities to free or low cost options
        if activities:
            cheaper_acts = [
                a for a in activities
                if float(a.get("estimated_cost_per_person", 0)) <= 15.0 or a.get("type") in ["nature", "culture", "walk"]
            ]
            if cheaper_acts:
                activities = cheaper_acts
                adjustments.append("Replaced premium activities with free/low-cost scenic & cultural tours")

        # 3. Recalculate breakdown with adjusted state
        replanned_breakdown = self.estimate(state, hotels=hotels, activities=activities, itinerary=itinerary)

        user_question = (
            f"⚠️ Your initial trip estimate exceeded your max budget of {target_currency} {state.budget:,.0f}.\n\n"
            f"🛠️ **Adjustments Made to Stay Under Budget:**\n"
            + "\n".join([f"• {adj}" for adj in adjustments]) + "\n\n"
            f"📊 **New Estimated Total:** **{target_currency} {sum(i.amount for i in replanned_breakdown.items):,.0f}** "
            f"(Remaining: {target_currency} {replanned_breakdown.remaining:,.0f})\n\n"
            f"**Is this updated budget-friendly plan okay with you?** "
            f"If not, say 'No' and I can show alternative options (like shortening duration or changing dates)."
        )

        return {
            "adjusted": True,
            "breakdown": replanned_breakdown,
            "adjustments": adjustments,
            "user_question": user_question,
            "activities": activities
        }

