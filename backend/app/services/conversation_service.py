"""
ConversationService — reply generation and trip state summary.

Extracted from chat.py to keep that file as a thin controller.
"""

from app.models.travel_state import TravelState
from app.services.llm_service import LLMService


# ===========================================================
# Question map — used when questionnaire fields are missing
# ===========================================================

_QUESTION_MAP: dict[str, str] = {
    "destination": (
        "🌍 **Where would you like to travel?**\n\n"
        "Tell me the city, country, or region you have in mind!"
    ),
    "travelers": (
        "👥 **How many people will be traveling?**\n\n"
        "*(e.g. just me, 2 adults, family of 4)*"
    ),
    "traveler_type": (
        "🎟️ **What best describes your travel group?**\n\n"
        "• 🧔 **Solo** — travelling alone\n"
        "• 👫 **Couple** — romantic getaway\n"
        "• 👨‍👩‍👧‍👦 **Family** — with kids or elderly\n"
        "• 👯 **Friends** — group trip\n"
        "• 💼 **Business** — work or conference travel\n\n"
        "*(Type your answer or pick one above!)*"
    ),
    "duration": (
        "⏳ **How many days are you planning for this trip?**\n\n"
        "*(e.g. 5 days, a week, 10 nights)*"
    ),
    "budget": (
        "💰 **What's your total budget for this trip?**\n\n"
        "Please mention the amount and currency — e.g. *₹80,000*, *$2,000*, *€1,500*"
    ),
    "origin": (
        "🛫 **Where will you be departing from?**\n\n"
        "*(e.g. Delhi, Mumbai, New York, London)*"
    ),
    "transit": (
        "🚆 **How would you like to get there?**\n\n"
        "Since this is a domestic route, I can plan either:\n\n"
        "• ✈️ **Flight** — faster, ideal when time or distance is long\n"
        "• 🚆 **Train / Express Bus** — scenic, budget-friendly\n\n"
        "Which do you prefer?"
    ),
    "accommodation": (
        "🏨 **What type of accommodation do you prefer?**\n\n"
        "• 🛏️ **Budget / Hostels** — shared dorms, guesthouses\n"
        "• 🏩 **Mid-Range Hotels** — comfortable 3–4 star stays\n"
        "• 🌟 **Luxury Resorts** — 5-star, spa, premium amenities"
    ),
    "interests": (
        "🗺️ **What kinds of experiences excite you most?**\n\n"
        "• 🧗 **Adventure** — hiking, rafting, trekking\n"
        "• 🏛️ **Culture** — temples, museums, heritage\n"
        "• 🍜 **Food & Dining** — street food, fine dining\n"
        "• 🏖️ **Beach & Relaxation** — sun, sea, wellness\n"
        "• 🎶 **Nightlife** — bars, clubs, live music\n\n"
        "*(Pick one or more, or describe in your own words!)*"
    ),
}

# Human-readable question text for each field — used as conversation_context
# passed back to the LLM for context-aware extraction.
FIELD_QUESTION_TEXT: dict[str, str] = {
    "destination":   "Where would you like to travel?",
    "travelers":     "How many people will be traveling?",
    "traveler_type": "What best describes your travel group?",
    "duration":      "How many days are you planning for this trip?",
    "budget":        "What's your total budget for this trip?",
    "origin":        "Where will you be departing from?",
    "transit":       "How would you like to get there?",
    "accommodation": "What type of accommodation do you prefer?",
    "interests":     "What kinds of experiences excite you most?",
}


class ConversationService:
    """Generates AI replies and trip state summaries."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    # -----------------------------------------------------------
    # State summary (for LLM context and CTA message)
    # -----------------------------------------------------------

    @staticmethod
    def state_summary(state: TravelState) -> str:
        parts = []
        if state.destinations:
            parts.append(f"Destination: {', '.join(state.destinations)}")
        if state.duration_days:
            parts.append(f"Duration: {state.duration_days} days")
        if state.travelers:
            parts.append(f"Travelers: {state.travelers}")
        if state.start_date:
            parts.append(f"Start: {state.start_date}")
        if state.budget:
            currency = state.currency or ""
            parts.append(f"Budget: {state.budget} {currency}")
        if state.interests:
            parts.append(f"Interests: {', '.join(state.interests)}")
        return " | ".join(parts) if parts else "No trip details yet"

    # -----------------------------------------------------------
    # Next question text (for questionnaire flow)
    # -----------------------------------------------------------

    @staticmethod
    def get_next_question(missing_field: str) -> str:
        return _QUESTION_MAP.get(
            missing_field,
            f"Could you tell me more about your **{missing_field}**?"
        )

    @staticmethod
    def get_field_question_text(field: str) -> str | None:
        """Return the plain-English question for a field (used as LLM context)."""
        return FIELD_QUESTION_TEXT.get(field)

    # -----------------------------------------------------------
    # Main reply generator
    # -----------------------------------------------------------

    def generate_reply(
        self,
        user_message: str,
        conversation_history: str,
        state_summary: str,
        route: str,
        raw_answer: str = "",
        missing: list[str] | None = None,
        enrichment: dict | None = None,
        weather: dict | None = None,
        currency: dict | None = None,
    ) -> str:
        """
        Generate a natural, context-aware conversational reply.

        Priority:
        1. Live data answers (weather / currency / flights) → use raw_answer directly
        2. RAG answers → use raw_answer directly
        3. Itinerary completion → canned confirmation message
        4. Questionnaire gate — if fields are still missing, ask the next question
        5. Fallback — let LLM generate a helpful reply
        """

        # 1. Live data pre-formatted answers (weather, currency, flights)
        if raw_answer and route == "live":
            return raw_answer

        # 2. Itinerary completion
        if enrichment and enrichment.get("itinerary"):
            dest_name = (
                state_summary.split("|")[0]
                .replace("Destination:", "")
                .strip()
                if state_summary
                else "your destination"
            )
            return (
                f"🎉 **Your complete personalised itinerary for {dest_name} is ready!**\n\n"
                "I've built your day-by-day schedule, selected hotels, and mapped out all routes.\n\n"
                "• 🗺️ **Live Map:** Sights & hotels are plotted in the **Map** panel\n"
                "• 📅 **Schedule:** Explore morning, afternoon & evening plans in the **Itinerary** tab\n"
                "• 🏨 **Accommodations:** View details & rates in the **Hotels** tab\n"
                "• 💰 **Budget:** Real-time cost allocation is available in the **Budget** tab\n\n"
                "Feel free to ask me anything about your destination, explore attractions, "
                "check safety rules, or swap activities!"
            )

        # 3. Questionnaire gate — if there are missing fields, always ask the next question
        if missing:
            next_q = _QUESTION_MAP.get(
                missing[0],
                f"Could you tell me more about your **{missing[0]}**?"
            )
            prefix = (
                "Got it! ✅\n\n"
                if (state_summary and state_summary != "No trip details yet")
                else "Happy to help plan your trip! Let me ask a few quick questions. 🌟\n\n"
            )
            return prefix + next_q

        # 4. RAG answers (when questionnaire is completed or explicit informational query)
        if raw_answer and route == "rag":
            return raw_answer

        # 4. LLM fallback
        prompt = (
            f"You are TravelOS, a friendly AI travel planning assistant.\n\n"
            f"Current conversation:\n{conversation_history}\n\n"
            f"Current trip being planned:\n{state_summary}\n\n"
            f'User just said: "{user_message}"\n\n'
            f"Respond naturally and helpfully. Be concise (2-3 sentences).\n"
            f"If the user is asking a travel question, answer accurately and politely.\n"
            f"Use a friendly, enthusiastic but professional tone.\n"
            f"Use relevant travel emojis sparingly."
        )

        try:
            return self.llm_service.generate_response(prompt)
        except Exception:
            return "I'm here to help you plan your perfect trip! What would you like to know?"
