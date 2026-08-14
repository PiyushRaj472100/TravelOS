"""
ConversationHandlers — mid-conversation special-case handlers.

Each handler inspects the incoming message and either returns a fully
formed ChatResponse (short-circuit) or returns None (fall through to
the main pipeline in chat.py).

Extracted from chat.py so that the route file stays as a thin controller.
"""

import re
from typing import Optional

from app.models.travel_state import TravelState
from app.models.chat import AgentStatus, ChatResponse
from app.services.session_manager import SessionManager
from app.services.missing_information import MissingInformationDetector
from app.services.live_query_service import LiveQueryService
from app.agents.activity_agent import ActivityAgent
from app.agents.hotel_agent import HotelAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.supervisor import OrchestratorAgent
from app.services.llm_service import LLMService


# ---------------------------------------------------------------------------
# Currency alias table (shared across handlers that need currency detection)
# ---------------------------------------------------------------------------

_CURRENCY_MAP = [
    ("japanese currency", "JPY"), ("jappanese currency", "JPY"),
    ("japan currency", "JPY"), ("japanese yen", "JPY"),
    ("yen", "JPY"), ("jpy", "JPY"),
    ("indian currency", "INR"), ("india currency", "INR"),
    ("indian rupee", "INR"), ("indian rupees", "INR"),
    ("rupee", "INR"), ("rupees", "INR"), ("inr", "INR"),
    ("us dollar", "USD"), ("us dollars", "USD"), ("us currency", "USD"),
    ("american dollar", "USD"), ("dollar", "USD"), ("dollars", "USD"), ("usd", "USD"),
    ("euro", "EUR"), ("euros", "EUR"), ("eur", "EUR"),
    ("british pound", "GBP"), ("pound", "GBP"), ("pounds", "GBP"), ("gbp", "GBP"),
    ("australian dollar", "AUD"), ("aud", "AUD"),
    ("canadian dollar", "CAD"), ("cad", "CAD"),
    ("singapore dollar", "SGD"), ("sgd", "SGD"),
    ("uae dirham", "AED"), ("dirham", "AED"), ("dirhams", "AED"), ("aed", "AED"),
    ("swiss franc", "CHF"), ("chf", "CHF"),
    ("thai baht", "THB"), ("baht", "THB"), ("thb", "THB"),
]


class ConversationHandlers:
    """
    Collection of special-case mid-conversation handlers.

    All handlers follow the same contract:
        handle_*(message, state, session_id) -> ChatResponse | None
    Returning None signals "not handled — fall through to main pipeline".
    """

    def __init__(
        self,
        session_manager: SessionManager,
        live_query_service: LiveQueryService,
        activity_agent: ActivityAgent,
        hotel_agent: HotelAgent,
        budget_agent: BudgetAgent,
        orchestrator: OrchestratorAgent,
        llm_service: LLMService,
    ):
        self.session_manager = session_manager
        self.live_query_service = live_query_service
        self.activity_agent = activity_agent
        self.hotel_agent = hotel_agent
        self.budget_agent = budget_agent
        self.orchestrator = orchestrator
        self.llm_service = llm_service

    # -----------------------------------------------------------------------
    # 1. Currency Switch
    # -----------------------------------------------------------------------

    def handle_currency_switch(
        self,
        message: str,
        state: TravelState,
        session_id: str,
    ) -> Optional[ChatResponse]:
        msg_lower = message.lower()

        has_switch_verb = any(v in msg_lower for v in [
            "change", "switch", "convert", "show in", "update currency",
            "transform", "in japanese", "in indian", "in us", "in euro",
            "to inr", "to usd", "to jpy", "to eur", "to gbp",
        ])
        has_currency_word = any(c in msg_lower for c in [
            "currency", "currecy", "currncy", "budget", "jpy", "inr", "usd",
            "eur", "gbp", "yen", "rupee", "rupees", "dollar", "dollars",
            "euro", "euros", "pound", "pounds", "aud", "cad", "aed", "chf", "thb",
        ])
        is_new_budget = "budget of " in msg_lower or "budget is " in msg_lower or "budget: " in msg_lower

        if not (has_switch_verb and has_currency_word and not is_new_budget):
            return None

        source_currency = (state.currency or "USD").upper()
        target_currency: Optional[str] = None

        to_match = re.search(r'(?:to|tov|into|in)\s+([a-zA-Z\s]+)', msg_lower)
        if to_match:
            to_part = to_match.group(1).strip()
            for alias, code in _CURRENCY_MAP:
                if alias in to_part:
                    target_currency = code
                    break

        from_match = re.search(r'(?:from|tfriom)\s+([a-zA-Z\s]+?)\s+(?:to|tov|into)', msg_lower)
        if from_match:
            from_part = from_match.group(1).strip()
            for alias, code in _CURRENCY_MAP:
                if alias in from_part:
                    source_currency = code
                    break

        if not target_currency:
            for alias, code in _CURRENCY_MAP:
                if alias in msg_lower and code != source_currency:
                    target_currency = code
                    break

        if not target_currency:
            return None
        if target_currency == source_currency and state.currency == target_currency:
            return None

        try:
            rate = self.live_query_service.currency_service.get_rate(source_currency, target_currency)
        except Exception as e:
            print(f"[ConversationHandlers] Currency switch rate error: {e}")
            rate = 1.0

        def _convert(val: Optional[float]) -> Optional[float]:
            if val is None:
                return None
            converted = float(val) * rate
            if target_currency in ["INR", "JPY", "KRW", "IDR", "THB"]:
                return float(round(converted))
            return round(converted, 2)

        if state.budget is not None:
            state.budget = _convert(state.budget)
        state.currency = target_currency

        for act in (state.activities or []):
            act["cost_currency"] = target_currency
            if act.get("estimated_cost_per_person") is not None:
                act["estimated_cost_per_person"] = _convert(act["estimated_cost_per_person"])

        for h in (state.hotels or []):
            h["currency"] = target_currency
            if h.get("price") is not None:
                h["price"] = _convert(h["price"])
            if h.get("published_rate") is not None:
                h["published_rate"] = _convert(h["published_rate"])

        for day in (state.itinerary or []):
            day["cost_currency"] = target_currency
            if day.get("estimated_daily_cost") is not None:
                day["estimated_daily_cost"] = _convert(day["estimated_daily_cost"])

        budget_breakdown = self.budget_agent.estimate(
            state=state,
            hotels=state.hotels,
            itinerary=state.itinerary,
            activities=state.activities,
        )
        self.session_manager.save_state(session_id, state)

        budget_str = f"{target_currency} {state.budget:,.0f}" if state.budget else "Not set"
        total_est = sum(item.amount for item in budget_breakdown.items)
        est_str = f"{target_currency} {total_est:,.0f}"
        remaining_str = (
            f"{target_currency} {budget_breakdown.remaining:,.0f}"
            if budget_breakdown.remaining is not None else "N/A"
        )

        reply = (
            f"💱 **Currency Converted to {target_currency}!**\n\n"
            f"All trip costs, hotels, adventures, activities, daily itineraries, and budget allocations "
            f"have been converted from **{source_currency}** to **{target_currency}** "
            f"at live rate (1 {source_currency} = {rate:.4f} {target_currency}):\n\n"
            f"• **Your Total Budget:** {budget_str}\n"
            f"• **Estimated Total Spend:** {est_str}\n"
            f"• **Flights:** {target_currency} {budget_breakdown.flights:,.0f}\n"
            f"• **Hotels:** {target_currency} {budget_breakdown.hotels:,.0f}\n"
            f"• **Food & Dining:** {target_currency} {budget_breakdown.food:,.0f}\n"
            f"• **Activities & Attractions:** {target_currency} {budget_breakdown.activities:,.0f}\n"
            f"• **Local Transport:** {target_currency} {budget_breakdown.transport:,.0f}\n"
            f"• **Remaining Balance:** {remaining_str}\n\n"
            f"Every card, panel, and calculation across your workspace now strictly reflects **{target_currency}**."
        )
        self.session_manager.add_message(session_id, "assistant", reply)

        return ChatResponse(
            message=reply,
            session_id=session_id,
            route="live",
            travel_state=state.model_dump(),
            activities=state.activities or [],
            hotels=state.hotels or [],
            itinerary=state.itinerary or [],
            budget=budget_breakdown,
            agent_statuses=[
                AgentStatus(
                    agent="budget",
                    status="done",
                    message=f"All items converted to {target_currency}",
                )
            ],
        )

    # -----------------------------------------------------------------------
    # 2. Expensive Activities Query
    # -----------------------------------------------------------------------

    def handle_expensive_activities(
        self,
        message: str,
        state: TravelState,
        session_id: str,
    ) -> Optional[ChatResponse]:
        msg_lower = message.lower()
        triggers = [
            "expensive activity", "expensive activities", "expensive thing", "expensive things",
            "costly activity", "costly activities", "pricey activity", "pricey activities",
            "which activities are expensive", "what are the expensive", "highest cost activity",
            "costliest", "which activity costs the most", "most expensive activities",
            "tell me expensive activities", "show expensive activities",
        ]
        if not any(t in msg_lower for t in triggers):
            return None

        if not state.activities and (state.destinations or state.cities):
            act_res = self.activity_agent.generate_activities(state)
            state.activities = act_res.get("activities", [])
            self.session_manager.save_state(session_id, state)

        target_currency = (state.currency or "USD").upper()
        travelers = max(1, state.travelers or 2)
        expensive_list = self.activity_agent.find_expensive_activities(state.activities, state, top_n=3)

        budget_breakdown = self.budget_agent.estimate(
            state=state,
            hotels=state.hotels,
            itinerary=state.itinerary,
            activities=state.activities,
        )

        if not expensive_list:
            reply = (
                f"🌟 **Great news!** All the activities currently in your trip for "
                f"{', '.join(state.destinations or state.cities or ['your trip'])} "
                f"are very budget-friendly or free! None exceed standard leisure costs in **{target_currency}**."
            )
        else:
            lines = [f"💰 **Top Most Expensive Activities in Your Trip ({target_currency}):**\n"]
            for i, item in enumerate(expensive_list, 1):
                act_name = item["name"]
                cost_pp = item["cost_per_person"]
                grp_cost = item["total_group_cost"]
                day_str = f" · Day {item['day_suggestion']}" if item.get("day_suggestion") else ""
                area_str = f" ({item['area']})" if item.get("area") else ""
                lines.append(
                    f"**{i}. {act_name}**{area_str}{day_str}\n"
                    f"   • Cost: **{target_currency} {cost_pp:,.0f}** / person "
                    f"(**{target_currency} {grp_cost:,.0f}** total for {travelers} "
                    f"traveler{'s' if travelers > 1 else ''})\n"
                    f"   • Description: {item.get('description', 'Exciting experience')}"
                )
            lines.append(
                f"\n🎯 **What would you like to do?**\n"
                f"• Say **'Leave [Activity Name]'** to remove it and save that cost.\n"
                f"• Say **'Give another option for [Activity Name]'** to swap it for a "
                f"budget-friendly alternative.\n"
                f"• Everything will immediately reflect on your budget and itinerary!"
            )
            reply = "\n".join(lines)

        self.session_manager.add_message(session_id, "assistant", reply)
        return ChatResponse(
            message=reply,
            session_id=session_id,
            route="planning",
            travel_state=state.model_dump(),
            activities=state.activities or [],
            hotels=state.hotels or [],
            itinerary=state.itinerary or [],
            budget=budget_breakdown,
            agent_statuses=[AgentStatus(agent="budget", status="done", message="Analyzed expensive activities")],
        )

    # -----------------------------------------------------------------------
    # 3. Activity Replacement / Removal ("Leave it" / "Give another option")
    # -----------------------------------------------------------------------

    def handle_activity_replacement(
        self,
        message: str,
        state: TravelState,
        session_id: str,
    ) -> Optional[ChatResponse]:
        msg_lower = message.lower()

        is_remove = any(v in msg_lower for v in [
            "leave it", "leave this", "leave the", "leave ",
            "remove it", "remove this", "remove the", "remove ",
            "drop it", "drop this", "drop the", "drop ",
            "delete activity", "delete ", "cancel activity", "cancel ",
        ])
        is_replace = any(v in msg_lower for v in [
            "give another option", "give another", "another option", "give option",
            "replace it", "replace this", "replace the", "replace ",
            "suggest alternative", "cheaper option", "budget alternative",
            "budget option", "find alternative", "swap ",
        ])

        if not (is_remove or is_replace):
            return None

        if not state.activities and (state.destinations or state.cities):
            act_res = self.activity_agent.generate_activities(state)
            state.activities = act_res.get("activities", [])

        if not state.activities:
            return None

        target_currency = (state.currency or "USD").upper()
        travelers = max(1, state.travelers or 2)

        # Find the activity mentioned in the message
        target_act = None
        for act in state.activities:
            act_name = act.get("name", "").lower()
            if act_name and (
                act_name in msg_lower
                or any(w in msg_lower for w in act_name.split() if len(w) > 4)
            ):
                target_act = act
                break

        # Fallback: most expensive activity
        if not target_act:
            sorted_acts = sorted(
                state.activities,
                key=lambda a: float(a.get("estimated_cost_per_person", 0)),
                reverse=True,
            )
            if sorted_acts:
                target_act = sorted_acts[0]

        if not target_act:
            return None

        old_name = target_act.get("name", "Selected Activity")
        old_cost_pp = float(target_act.get("estimated_cost_per_person", 0))
        old_total_group = old_cost_pp * travelers

        # CASE A: Remove
        if is_remove and not is_replace:
            state.activities = [
                a for a in state.activities
                if a.get("id") != target_act.get("id") and a.get("name") != old_name
            ]
            if state.itinerary:
                for day in state.itinerary:
                    for slot in ["morning", "afternoon", "evening"]:
                        if isinstance(day.get(slot), dict):
                            slot_act = day[slot].get("activity", "")
                            if old_name.lower() in slot_act.lower() or slot_act.lower() in old_name.lower():
                                day[slot]["activity"] = "Free Leisure & Scenic Exploration"
                                day[slot]["description"] = "Self-guided walk and leisure time."

            budget_breakdown = self.budget_agent.estimate(
                state=state, hotels=state.hotels,
                itinerary=state.itinerary, activities=state.activities,
            )
            self.session_manager.save_state(session_id, state)

            total_est = sum(item.amount for item in budget_breakdown.items)
            rem_str = (
                f"{target_currency} {budget_breakdown.remaining:,.0f}"
                if budget_breakdown.remaining is not None else "N/A"
            )
            reply = (
                f"🗑️ **Removed '{old_name}' from your trip!**\n\n"
                f"• **Saved Amount:** **{target_currency} {old_total_group:,.0f}** for your group "
                f"({travelers} traveler{'s' if travelers > 1 else ''})\n"
                f"• **New Estimated Spend:** {target_currency} {total_est:,.0f}\n"
                f"• **Updated Remaining Budget:** {rem_str}\n\n"
                f"Your itinerary and activities panels have been updated."
            )
            self.session_manager.add_message(session_id, "assistant", reply)
            return ChatResponse(
                message=reply, session_id=session_id, route="planning",
                travel_state=state.model_dump(),
                activities=state.activities or [], hotels=state.hotels or [],
                itinerary=state.itinerary or [], budget=budget_breakdown,
                agent_statuses=[AgentStatus(
                    agent="budget", status="done",
                    message=f"Removed {old_name}, saved {target_currency} {old_total_group:,.0f}",
                )],
            )

        # CASE B: Replace
        new_act = self.activity_agent.replace_activity_with_cheaper_option(state, target_act, state.activities)
        if not new_act:
            return None

        new_activities = []
        replaced = False
        for a in state.activities:
            if not replaced and (a.get("id") == target_act.get("id") or a.get("name") == old_name):
                new_activities.append(new_act)
                replaced = True
            else:
                new_activities.append(a)
        if not replaced:
            new_activities.append(new_act)
        state.activities = new_activities

        if state.itinerary:
            for day in state.itinerary:
                for slot in ["morning", "afternoon", "evening"]:
                    if isinstance(day.get(slot), dict):
                        slot_act = day[slot].get("activity", "")
                        if old_name.lower() in slot_act.lower() or slot_act.lower() in old_name.lower():
                            day[slot]["activity"] = new_act.get("name", "Alternative Sightseeing")
                            day[slot]["description"] = new_act.get("description", "Budget-friendly experience.")

        budget_breakdown = self.budget_agent.estimate(
            state=state, hotels=state.hotels,
            itinerary=state.itinerary, activities=state.activities,
        )
        self.session_manager.save_state(session_id, state)

        new_cost_pp = float(new_act.get("estimated_cost_per_person", 0))
        new_total_group = new_cost_pp * travelers
        saved_amount = max(0.0, old_total_group - new_total_group)
        total_est = sum(item.amount for item in budget_breakdown.items)
        rem_str = (
            f"{target_currency} {budget_breakdown.remaining:,.0f}"
            if budget_breakdown.remaining is not None else "N/A"
        )
        reply = (
            f"🔄 **Replaced '{old_name}' with a budget-friendly option!**\n\n"
            f"✨ **New Activity:** **{new_act.get('name')}** ({new_act.get('type', 'Activity').capitalize()})\n"
            f"📍 **Area:** {new_act.get('area', 'Local district')}\n"
            f"📝 **Highlights:** {new_act.get('description', '')}\n"
            f"💵 **New Cost:** {target_currency} {new_cost_pp:,.0f} / person "
            f"(previously {target_currency} {old_cost_pp:,.0f})\n"
            f"🎉 **Total Group Savings:** **{target_currency} {saved_amount:,.0f}**\n\n"
            f"• **New Estimated Spend:** {target_currency} {total_est:,.0f}\n"
            f"• **Updated Remaining Budget:** {rem_str}\n\n"
            f"The new activity and updated budget are reflected live in all panels."
        )
        self.session_manager.add_message(session_id, "assistant", reply)
        return ChatResponse(
            message=reply, session_id=session_id, route="planning",
            travel_state=state.model_dump(),
            activities=state.activities or [], hotels=state.hotels or [],
            itinerary=state.itinerary or [], budget=budget_breakdown,
            agent_statuses=[AgentStatus(
                agent="budget", status="done",
                message=f"Replaced with {new_act.get('name')}, saved {target_currency} {saved_amount:,.0f}",
            )],
        )

    # -----------------------------------------------------------------------
    # 4. Hotel Selection
    # -----------------------------------------------------------------------

    def handle_hotel_selection(
        self,
        message: str,
        state: TravelState,
        session_id: str,
    ) -> Optional[ChatResponse]:
        msg_lower = message.lower()
        if not any(t in msg_lower for t in ["select hotel", "choose hotel", "book hotel", "selected hotel", "pick hotel", "set hotel"]):
            return None

        if not state.hotels and (state.destinations or state.cities):
            hotel_res = self.hotel_agent.search(state)
            state.hotels = hotel_res.get("hotels", [])

        if not state.hotels:
            return None

        selected_hotel = None
        for h in state.hotels:
            h_name = h.get("name", "").lower()
            if h_name and (h_name in msg_lower or any(p in msg_lower for p in h_name.split() if len(p) > 3)):
                selected_hotel = h
                break

        if not selected_hotel:
            selected_hotel = state.hotels[0]

        other_hotels = [h for h in state.hotels if h.get("name") != selected_hotel.get("name")]
        state.hotels = [selected_hotel] + other_hotels

        budget_breakdown = self.budget_agent.estimate(
            state=state, hotels=state.hotels,
            itinerary=state.itinerary, activities=state.activities,
        )
        self.session_manager.save_state(session_id, state)

        target_currency = (state.currency or "USD").upper()
        price_night = selected_hotel.get("price", 0)
        duration = max(1, state.duration_days or 1)
        travelers = max(1, state.travelers or 1)
        rooms = max(1, (travelers + 1) // 2)
        total_hotel_cost = price_night * duration * rooms

        reply = (
            f"🏨 **Selected '{selected_hotel.get('name')}' for your stay!**\n\n"
            f"• **Rate per Night:** {target_currency} {price_night:,.0f}\n"
            f"• **Total Accommodation Cost:** **{target_currency} {total_hotel_cost:,.0f}** "
            f"({duration} night{'s' if duration > 1 else ''}, {rooms} room{'s' if rooms > 1 else ''})\n"
            f"• **Updated Total Estimated Spend:** {target_currency} {sum(i.amount for i in budget_breakdown.items):,.0f}\n\n"
            f"Your budget breakdown and trip workspace have been updated."
        )
        self.session_manager.add_message(session_id, "assistant", reply)
        return ChatResponse(
            message=reply, session_id=session_id, route="planning",
            travel_state=state.model_dump(),
            activities=state.activities or [], hotels=state.hotels or [],
            itinerary=state.itinerary or [], budget=budget_breakdown,
            agent_statuses=[AgentStatus(
                agent="hotel", status="done",
                message=f"Selected hotel: {selected_hotel.get('name')}",
            )],
        )

    # -----------------------------------------------------------------------
    # 5. Domestic Transport Preference
    # -----------------------------------------------------------------------

    def handle_domestic_transport(
        self,
        message: str,
        state: TravelState,
        session_id: str,
    ) -> Optional[ChatResponse]:
        msg_lower = message.lower()
        if not any(t in msg_lower for t in [
            "prefer train", "prefer bus", "no flight", "dont need flight", "don't need flight",
            "can flight fit", "flight fit in budget", "is flight in budget",
            "can i afford flight", "flight or train", "train or flight",
        ]):
            return None

        target_currency = (state.currency or "USD").upper()

        if any(k in msg_lower for k in ["no flight", "prefer train", "prefer bus", "dont need flight", "don't need flight"]):
            state.transportation_preference = "train"
            budget_breakdown = self.budget_agent.estimate(
                state=state, flights=[],
                hotels=state.hotels, itinerary=state.itinerary, activities=state.activities,
            )
            self.session_manager.save_state(session_id, state)
            reply = (
                f"🚆 **Updated Preference to Train / Ground Transport!**\n\n"
                f"• **Flight Cost Set to:** {target_currency} 0\n"
                f"• **New Total Estimated Spend:** {target_currency} {sum(i.amount for i in budget_breakdown.items):,.0f}\n\n"
                f"This keeps your transport expenses budget-friendly!"
            )
        else:
            budget_breakdown = self.budget_agent.estimate(
                state=state, hotels=state.hotels,
                itinerary=state.itinerary, activities=state.activities,
            )
            rem = budget_breakdown.remaining if budget_breakdown.remaining is not None else 0
            if rem >= 0:
                reply = (
                    f"✈️ **Great news! A flight fits within your budget!**\n\n"
                    f"• **Target Budget:** {target_currency} {state.budget:,.0f}\n"
                    f"• **Total Estimated Trip Cost (including flight):** "
                    f"{target_currency} {sum(i.amount for i in budget_breakdown.items):,.0f}\n"
                    f"• **Remaining Surplus:** {target_currency} {rem:,.0f}\n\n"
                    f"Your budget accommodates air travel without exceeding your limit!"
                )
            else:
                reply = (
                    f"🚆 **Train / Ground Transport Recommended:**\n\n"
                    f"Adding flights will exceed your target budget by **{target_currency} {abs(rem):,.0f}**.\n"
                    f"We recommend choosing express train or bus transport for this route, "
                    f"which keeps your trip comfortable and strictly under budget!"
                )

        self.session_manager.add_message(session_id, "assistant", reply)
        return ChatResponse(
            message=reply, session_id=session_id, route="planning",
            travel_state=state.model_dump(),
            activities=state.activities or [], hotels=state.hotels or [],
            itinerary=state.itinerary or [], budget=budget_breakdown,
            agent_statuses=[AgentStatus(agent="budget", status="done", message="Analyzed transport budget preference")],
        )

    # -----------------------------------------------------------------------
    # 6. Budget Feasibility Check
    # -----------------------------------------------------------------------

    def handle_budget_feasibility(
        self,
        message: str,
        state: TravelState,
        session_id: str,
    ) -> Optional[ChatResponse]:
        if not MissingInformationDetector.is_budget_feasibility_check(message):
            return None
        if state.budget is None:
            return None

        target_currency = (state.currency or "USD").upper()
        budget_val = state.budget
        msg_lower = message.lower()

        is_luxury_hotel = any(k in msg_lower for k in [
            "luxury hotel", "5 star", "five star", "luxury resort", "luxury stay",
            "premium hotel", "high-end hotel", "resort", "spa hotel",
        ])
        is_business_class = any(k in msg_lower for k in [
            "business class", "first class", "premium economy", "business seat",
            "upgrade", "first class flight",
        ])
        is_private_tour = any(k in msg_lower for k in [
            "private tour", "private guide", "private transfer",
        ])

        duration = max(1, state.duration_days or 5)
        travelers = max(1, state.travelers or 2)
        rooms = max(1, (travelers + 1) // 2)

        _USD_RATES = {"INR": 84.0, "EUR": 0.93, "GBP": 0.79, "JPY": 155.0, "AUD": 1.55}
        usd_to_curr = _USD_RATES.get(target_currency, 1.0)

        if is_luxury_hotel:
            feature_label = "a luxury hotel stay"
            feature_cost = 200 * usd_to_curr * duration * rooms
        elif is_business_class:
            feature_label = "business class flights"
            feature_cost = 1500 * usd_to_curr * travelers
        elif is_private_tour:
            feature_label = "a private tour guide"
            feature_cost = 150 * usd_to_curr * duration
        else:
            feature_label = "that feature"
            feature_cost = budget_val * 0.30

        remaining_after = budget_val - feature_cost
        fits = remaining_after >= 0

        next_q_text = MissingInformationDetector.next_question(state)

        if fits:
            reply = (
                f"✅ **No problem!** {feature_label.capitalize()} will be comfortably managed "
                f"under your **{target_currency} {budget_val:,.0f}** budget.\n\n"
                f"• **Estimated cost for {feature_label}:** {target_currency} {feature_cost:,.0f}\n"
                f"• **Remaining for rest of trip:** {target_currency} {remaining_after:,.0f}\n\n"
            )
        else:
            overage = abs(remaining_after)
            reply = (
                f"⚠️ **Heads up!** {feature_label.capitalize()} may stretch your "
                f"**{target_currency} {budget_val:,.0f}** budget slightly — "
                f"estimated cost is **{target_currency} {feature_cost:,.0f}**, "
                f"which is **{target_currency} {overage:,.0f}** over your limit.\n\n"
                f"You could either increase your budget or opt for a slightly less premium option. "
                f"I'll do my best to find the best value!\n\n"
            )

        if next_q_text:
            reply += f"Now, back to planning your trip — {next_q_text}"

        self.session_manager.add_message(session_id, "assistant", reply)
        map_data = self.orchestrator._build_map_data(state=state, hotels=[], activities=[], itinerary=[])
        return ChatResponse(
            message=reply, session_id=session_id, route="planning",
            travel_state=state.model_dump(),
            missing_information=MissingInformationDetector.detect(state),
            map_data=map_data,
        )

    # -----------------------------------------------------------------------
    # 7. Post-Itinerary Place Overview & Alternative Swap
    # -----------------------------------------------------------------------

    def handle_place_overview(
        self,
        message: str,
        state: TravelState,
        session_id: str,
    ) -> Optional[ChatResponse]:
        msg_lower = message.lower().strip()

        if not state.itinerary and not state.activities:
            return None

        is_swap_request = any(k in msg_lower for k in [
            "show me other options", "other options instead", "show other options",
            "replace this", "change this", "swap this", "something else instead",
            "different option", "another option for", "alternative for",
            "instead of this", "instead of the",
        ])
        is_place_query = any(k in msg_lower for k in [
            "tell me about", "what is", "info about", "details about",
            "show me", "describe", "overview of", "explain",
        ])

        if not (is_swap_request or is_place_query):
            return None

        # Extract place name
        place_name = None
        patterns = [
            r'tell me about (.+)', r'what is (.+)', r'info about (.+)',
            r'details about (.+)', r'show me (.+)', r'describe (.+)',
            r'overview of (.+)', r'explain (.+)', r'instead of (.+)',
            r'instead of the (.+)', r'other options instead of (.+)',
            r'alternative for (.+)', r'another option for (.+)',
            r'replace (.+)', r'swap (.+)', r'change (.+)',
        ]
        for pat in patterns:
            m = re.search(pat, msg_lower)
            if m:
                place_name = m.group(1).strip().rstrip("?.,!")
                break

        if not place_name:
            return None

        for filler in ["this", "the", "that", "it", "my ", "our "]:
            place_name = place_name.replace(filler, "").strip()

        if len(place_name) < 3:
            return None

        place_encoded = place_name.replace(" ", "+")
        image_url = f"https://source.unsplash.com/800x400/?{place_encoded},travel,landmark"
        wiki_search = place_name.replace(" ", "+")
        target_currency = (state.currency or "USD").upper()
        travelers = max(1, state.travelers or 2)

        # Swap path
        if is_swap_request and state.activities:
            target_act = None
            for act in state.activities:
                act_name_lower = act.get("name", "").lower()
                if place_name in act_name_lower or any(
                    w in act_name_lower for w in place_name.split() if len(w) > 3
                ):
                    target_act = act
                    break

            if target_act:
                new_act = self.activity_agent.replace_activity_with_cheaper_option(state, target_act, state.activities)
                if new_act:
                    state.activities = [
                        new_act if (a.get("name") == target_act.get("name")) else a
                        for a in state.activities
                    ]
                    if state.itinerary:
                        old_name = target_act.get("name", "")
                        for day in state.itinerary:
                            for slot in ["morning", "afternoon", "evening"]:
                                if isinstance(day.get(slot), dict):
                                    slot_act = day[slot].get("activity", "")
                                    if old_name.lower() in slot_act.lower():
                                        day[slot]["activity"] = new_act.get("name", "Alternative Experience")
                                        day[slot]["description"] = new_act.get("description", "")

                    budget_breakdown = self.budget_agent.estimate(
                        state=state, hotels=state.hotels,
                        itinerary=state.itinerary, activities=state.activities,
                    )
                    self.session_manager.save_state(session_id, state)

                    old_cost = float(target_act.get("estimated_cost_per_person", 0))
                    new_cost = float(new_act.get("estimated_cost_per_person", 0))
                    saved = max(0.0, (old_cost - new_cost) * travelers)
                    new_place = new_act.get("name", "Alternative")
                    new_place_enc = new_place.replace(" ", "+")
                    new_image_url = f"https://source.unsplash.com/800x400/?{new_place_enc},travel,landmark"

                    reply = (
                        f"### 🔄 Swapped: {target_act.get('name')} → {new_place}\n\n"
                        f"![{new_place}]({new_image_url})\n\n"
                        f"**{new_place}** ({new_act.get('type', 'Activity').capitalize()})\n\n"
                        f"- 📍 **Area:** {new_act.get('area', 'Local district')}\n"
                        f"- 📝 {new_act.get('description', 'A great alternative experience.')}\n"
                        f"- 💵 **Cost:** {target_currency} {new_cost:,.0f} / person "
                        f"(was {target_currency} {old_cost:,.0f})\n"
                        f"- 💰 **Group savings: {target_currency} {saved:,.0f}**\n\n"
                        f"[📖 Learn more about {new_place}]"
                        f"(https://en.wikipedia.org/wiki/Special:Search?search={new_place_enc})"
                    )
                    self.session_manager.add_message(session_id, "assistant", reply)
                    return ChatResponse(
                        message=reply, session_id=session_id, route="planning",
                        travel_state=state.model_dump(),
                        activities=state.activities or [], hotels=state.hotels or [],
                        itinerary=state.itinerary or [], budget=budget_breakdown,
                        agent_statuses=[AgentStatus(
                            agent="activities", status="done",
                            message=f"Swapped to {new_place}, saved {target_currency} {saved:,.0f}",
                        )],
                    )

        # Place overview path
        prompt = (
            f'You are TravelOS, a world-class travel guide AI.\n\n'
            f'The user wants to know about: "{place_name}"\n\n'
            f'Respond ONLY with a markdown section in this exact format (no preamble):\n\n'
            f'### 📍 {place_name.title()}\n\n'
            f'![{place_name.title()}]({image_url})\n\n'
            f'3-4 punchy bullet points:\n'
            f'- **What it is**: one-sentence overview\n'
            f'- **Why it\'s famous**: top highlights\n'
            f'- **Best time to visit / insider tip**\n'
            f'- **Estimated entry / activity cost** (if applicable)\n\n'
            f'[📖 Explore more about {place_name.title()}]'
            f'(https://en.wikipedia.org/wiki/Special:Search?search={wiki_search})\n\n'
            f'Return ONLY the markdown. No intro. No outro.'
        )
        try:
            raw_answer = self.llm_service.generate_response(prompt)
        except Exception:
            raw_answer = (
                f"### 📍 {place_name.title()}\n\n"
                f"![{place_name.title()}]({image_url})\n\n"
                f"- A renowned landmark celebrated for its rich history and stunning scenery.\n"
                f"- Attracts visitors from around the world with unique cultural experiences.\n"
                f"- Best visited during the morning for smaller crowds.\n\n"
                f"[📖 Explore more about {place_name.title()}]"
                f"(https://en.wikipedia.org/wiki/Special:Search?search={wiki_search})"
            )

        self.session_manager.add_message(session_id, "assistant", raw_answer)
        map_data = self.orchestrator._build_map_data(
            state=state, hotels=state.hotels or [],
            activities=state.activities or [], itinerary=[],
        )
        return ChatResponse(
            message=raw_answer, session_id=session_id, route="rag",
            travel_state=state.model_dump(),
            activities=state.activities or [], hotels=state.hotels or [],
            itinerary=state.itinerary or [], map_data=map_data,
        )
