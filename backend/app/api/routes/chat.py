"""
TravelOS Chat Route — Thin Controller

Flow:
 1. Session setup
 2. Add user message to history
 3. Run special-case handlers (currency switch, activity ops, hotel, transport, etc.)
 4. Extract travel info via LLM (context-aware: passes current field + question)
 5. Update TravelState
 6. Analyze query → route (live | rag | planning)
 7. Execute route
 8. Orchestrate enrichment (hotels, activities, itinerary, budget)
 9. Generate conversational reply
10. Return enriched ChatResponse
"""

from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.rag.rag_manager import RAGManager
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.query_router import QueryRouter

from app.models.travel_state import TravelState
from app.models.chat import (
    AgentStatus,
    ChatRequest,
    ChatResponse,
    ChatSource,
)

from app.services.llm_service import LLMService
from app.services.state_manager import StateManager
from app.services.missing_information import (
    MissingInformationDetector,
    _get_country_for_city,
)
from app.services.session_manager import session_manager
from app.services.live_query_service import LiveQueryService
from app.services.conversation_service import ConversationService
from app.services.conversation_handlers import ConversationHandlers

from app.agents.research_agent import ResearchAgent
from app.agents.hotel_agent import HotelAgent
from app.agents.activity_agent import ActivityAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.supervisor import OrchestratorAgent


# =============================================================
# Router
# =============================================================

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# =============================================================
# Service / Agent initialization
# =============================================================

llm_service = LLMService()

query_analyzer = QueryAnalyzer(llm_service)
query_router = QueryRouter()
live_query_service = LiveQueryService()
rag_manager = RAGManager(llm_service=llm_service)
rag_service = rag_manager.get_rag_service()

# Agents
research_agent = ResearchAgent(rag_service=rag_service)
hotel_agent = HotelAgent()
activity_agent = ActivityAgent(
    rag_service=rag_service,
    llm_service=llm_service,
    currency_service=live_query_service.currency_service,
)
itinerary_agent = ItineraryAgent(
    llm_service=llm_service,
    currency_service=live_query_service.currency_service,
)
budget_agent = BudgetAgent(
    currency_service=live_query_service.currency_service
)

orchestrator = OrchestratorAgent(
    research_agent=research_agent,
    hotel_agent=hotel_agent,
    activity_agent=activity_agent,
    itinerary_agent=itinerary_agent,
    budget_agent=budget_agent,
    currency_service=live_query_service.currency_service,
)

# Services
conversation_service = ConversationService(llm_service=llm_service)

handlers = ConversationHandlers(
    session_manager=session_manager,
    live_query_service=live_query_service,
    activity_agent=activity_agent,
    hotel_agent=hotel_agent,
    budget_agent=budget_agent,
    orchestrator=orchestrator,
    llm_service=llm_service,
)


# =============================================================
# Helpers
# =============================================================

def _format_flight_message(flights: list[dict]) -> str:
    if not flights:
        return "I couldn't find any flights matching your search."
    lines = ["✈️ Here are the recommended flights:"]
    for i, f in enumerate(flights[:3], 1):
        provider = f.get("provider") or "Unknown airline"
        origin = f.get("origin", "")
        dest = f.get("destination", "")
        price = f.get("price")
        currency = f.get("currency", "")
        stops = f.get("stops", 0)
        duration = f.get("duration_minutes")
        line = f"\n**{i}. {provider}** — {origin} → {dest}"
        if price:
            line += f" | {price:.0f} {currency}"
        if stops == 0:
            line += " | Direct"
        elif stops == 1:
            line += " | 1 stop"
        else:
            line += f" | {stops} stops"
        if duration:
            h, m = divmod(duration, 60)
            line += f" | {h}h {m}m"
        lines.append(line)
    return "\n".join(lines)


# =============================================================
# Chat endpoint
# =============================================================

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):

    # ----------------------------------------------------------
    # 1. Session setup
    # ----------------------------------------------------------
    session_id = request.session_id or str(uuid4())
    state = session_manager.get_state(session_id)
    history = session_manager.get_history(session_id)
    conversation_history = session_manager.get_history_text(session_id)

    # ----------------------------------------------------------
    # 2. Add user message to history
    # ----------------------------------------------------------
    session_manager.add_message(session_id, "user", request.message)

    # ----------------------------------------------------------
    # 3. Special-case handlers (short-circuit if handled)
    # ----------------------------------------------------------
    for handler_fn in [
        handlers.handle_currency_switch,
        handlers.handle_expensive_activities,
        handlers.handle_activity_replacement,
        handlers.handle_hotel_selection,
        handlers.handle_domestic_transport,
        handlers.handle_budget_feasibility,
        handlers.handle_place_overview,
    ]:
        result = handler_fn(request.message, state, session_id)
        if result is not None:
            return result

    # ----------------------------------------------------------
    # 4. Context-aware travel information extraction
    #    Pass the current questionnaire field so the LLM knows
    #    which field is being collected and classifies the user's
    #    answer correctly (e.g. "Mumbai" → origin, not destination)
    # ----------------------------------------------------------
    missing_before = MissingInformationDetector.detect(state)
    current_field = missing_before[0] if missing_before else None
    conv_context = (
        ConversationService.get_field_question_text(current_field)
        if current_field else None
    )

    try:
        print(f"\n[Chat] User: {request.message[:80]}")
        extraction = llm_service.extract_travel_information(
            user_message=request.message,
            current_field=current_field,
            conversation_context=conv_context,
        )
        print(f"[Chat] Extracted: {extraction.model_dump()}")
    except Exception as e:
        print(f"[Chat] LLM extraction error: {e}")
        from app.models.travel_extraction import TravelExtraction
        extraction = TravelExtraction()

    # ----------------------------------------------------------
    # 5. Update TravelState
    # ----------------------------------------------------------
    state = StateManager.update_state(state, extraction)
    state = MissingInformationDetector.fill_missing_from_context(state, request.message, extraction)
    session_manager.save_state(session_id, state)
    state_summary = ConversationService.state_summary(state)
    print(f"[Chat] State: {state_summary}")

    # ----------------------------------------------------------
    # 6. Analyze query
    # ----------------------------------------------------------
    try:
        query = query_analyzer.analyze(request.message)
        print(f"[Chat] Query: category={query.category} type={query.query_type} live={query.needs_live_data}")
    except Exception as e:
        print(f"[Chat] Query analysis error: {e}")
        query = query_analyzer._heuristic_analyze(request.message)

    # ----------------------------------------------------------
    # 7. Route
    # ----------------------------------------------------------
    route = query_router.route(query)
    print(f"[Chat] Route: {route}")

    # ----------------------------------------------------------
    # 8. Execute route
    # ----------------------------------------------------------
    live_result = None
    raw_answer = ""
    sources: list[ChatSource] = []
    weather = None
    currency_data = None
    flights: list[dict] = []
    agent_statuses: list[AgentStatus] = []

    # Detect if user explicitly asked an informational / knowledge question
    is_info_query = MissingInformationDetector.is_informational_or_place_query(request.message)
    missing = [] if is_info_query else MissingInformationDetector.detect(state)
    questionnaire_in_progress = bool(missing)

    if route == "live":
        try:
            live_result = live_query_service.handle(query)
        except Exception as e:
            print(f"[Chat] Live data error: {e}")
            live_result = None
            raw_answer = (
                f"I'm sorry, I couldn't retrieve live {query.category} data right now. "
                "Please try again in a moment."
            )

        if live_result:
            if query.category == "weather":
                weather = live_result
                raw_answer = (
                    f"🌤️ Current weather in {live_result['city']}, "
                    f"{live_result['country']}: "
                    f"**{live_result['temperature']}°C** "
                    f"(feels like {live_result['apparent_temperature']}°C). "
                    f"Humidity: {live_result['humidity']}%. "
                    f"Wind: {live_result['wind_speed']} km/h."
                )
            elif query.category == "currency":
                currency_data = live_result
                raw_answer = (
                    f"💱 Current exchange rate: "
                    f"**1 {live_result['base_currency']} = "
                    f"{live_result['rate']} {live_result['target_currency']}**"
                )
            elif query.category == "flight":
                recommended = live_result.get("recommended", [])
                flights = [
                    orchestrator._serialize_flight(f, state.currency)
                    for f in recommended
                ]
                raw_answer = _format_flight_message(flights)
                agent_statuses.append(AgentStatus(
                    agent="flights", status="done",
                    message=f"{len(flights)} flights found",
                ))

    elif route == "rag" and (is_info_query or not questionnaire_in_progress):
        # Only execute full RAG guide if it's an explicit info question or questionnaire is done
        try:
            extracted_countries = list(query.countries) if query.countries else []
            extracted_cities = list(query.cities) if query.cities else []

            for c in extracted_cities:
                c_country = _get_country_for_city(c)
                if c_country:
                    c_title = c_country.capitalize()
                    if c_title not in extracted_countries:
                        extracted_countries.append(c_title)

            rag_result = rag_service.answer_with_state(
                question=request.message,
                state=state,
                top_k=5,
                category=query.category if query.category and query.category != "general" else None,
                countries=extracted_countries if extracted_countries else None,
                regions=query.regions if query.regions else None,
                cities=extracted_cities if extracted_cities else None,
            )
            raw_answer = rag_result.get("answer", "")
            raw_sources = rag_result.get("sources", [])
            sources = [
                ChatSource(
                    title=s.get("title"),
                    source=s.get("source"),
                    source_url=s.get("source_url"),
                    fallback_search_url=s.get("fallback_search_url"),
                    country=s.get("country"),
                    region=s.get("region"),
                    city=s.get("city"),
                    category=s.get("category"),
                    score=s.get("score"),
                )
                for s in raw_sources
            ]
        except Exception as e:
            print(f"[Chat] RAG error: {e}")
            try:
                dest_str = ", ".join(
                    query.countries or query.cities
                    or state.destinations or state.cities or ["your destination"]
                )
                prompt = (
                    f'You are TravelOS, a knowledgeable AI travel planning assistant.\n\n'
                    f'User Question: "{request.message}"\n'
                    f'Trip Context: Destination: {dest_str}.\n\n'
                    f'Provide a clear, rich, accurate, structured, and engaging answer.'
                )
                raw_answer = llm_service.generate_response(prompt)
            except Exception as e2:
                print(f"[Chat] Fallback error: {e2}")
                raw_answer = (
                    "Please check official local government and tourism safety advisories "
                    "for up-to-date travel rules and regulations."
                )

    # ----------------------------------------------------------
    # 9. Orchestrator enrichment
    #    - Full trip build: ONLY on CTA button click
    #    - Explicit hotel/activity/budget requests post-questionnaire
    #    - RAG knowledge queries always run research agent
    # ----------------------------------------------------------
    enrichment: dict = {}
    itinerary_ready = MissingInformationDetector.is_ready_for_itinerary(state)

    _CTA_PHRASE = "build my full itinerary now"
    is_cta_click = request.message.strip().lower() == _CTA_PHRASE
    wants_build = is_cta_click

    # If questionnaire not complete AND user clicked CTA, redirect to next question
    if not itinerary_ready and is_cta_click:
        next_q = MissingInformationDetector.next_question(state)
        if next_q:
            _missing_now = MissingInformationDetector.detect(state)
            reply = (
                f"Almost there! I just need a few more details before building your itinerary.\n\n{next_q}"
            )
            session_manager.add_message(session_id, "assistant", reply)
            map_data = orchestrator._build_map_data(state=state, hotels=[], activities=[], itinerary=[])
            return ChatResponse(
                session_id=session_id, message=reply,
                missing_information=_missing_now,
                travel_state=state.model_dump(), map_data=map_data,
            )

    _questionnaire_in_progress = not itinerary_ready

    run_orchestration = (
        (wants_build and itinerary_ready)
        or (not _questionnaire_in_progress and orchestrator._is_hotel_request(request.message))
        or (not _questionnaire_in_progress and orchestrator._is_activity_request(request.message))
        or (not _questionnaire_in_progress and orchestrator._is_budget_request(request.message))
        or route == "rag"
        or (route == "live" and live_result is not None)
    )

    if run_orchestration:
        try:
            enrichment = orchestrator.orchestrate(
                query=query, state=state, live_result=live_result,
            )
            agent_statuses.extend(enrichment.get("agent_statuses", []))

            if not flights:
                flights = enrichment.get("flights", [])

            if enrichment.get("activities"):
                state.activities = enrichment["activities"]
            if enrichment.get("hotels"):
                state.hotels = enrichment["hotels"]
            if enrichment.get("itinerary"):
                state.itinerary = enrichment["itinerary"]
            session_manager.save_state(session_id, state)

            if not raw_answer and enrichment.get("research_answer"):
                raw_answer = enrichment["research_answer"]
                if enrichment.get("research_sources"):
                    sources = [
                        ChatSource(**s) if isinstance(s, dict) else s
                        for s in enrichment["research_sources"]
                    ]
        except Exception as e:
            print(f"[Chat] Orchestrator error: {e}")

    # ----------------------------------------------------------
    # 9b. Informational queries
    # ----------------------------------------------------------
    is_info_query = MissingInformationDetector.is_informational_or_place_query(request.message)
    missing = [] if is_info_query else MissingInformationDetector.detect(state)

    # CTA gate: show once when questionnaire is just complete
    if (
        not state.itinerary
        and not getattr(state, "cta_shown", False)
        and not missing
        and not is_cta_click
        and route not in ("rag", "live")
        and not raw_answer
        and not is_info_query
    ):
        state.cta_shown = True
        session_manager.save_state(session_id, state)
        cta_message = (
            "🎯 **Perfect! I have everything I need to plan your complete trip.**\n\n"
            f"{state_summary}\n\n"
            "Click below to generate your **full personalised itinerary** — "
            "day-by-day plan, hotels, activities & complete budget breakdown."
        )
        session_manager.add_message(session_id, "assistant", cta_message)
        map_data = orchestrator._build_map_data(state=state, hotels=[], activities=[], itinerary=[])
        return ChatResponse(
            session_id=session_id, message=cta_message,
            missing_information=[], travel_state=state.model_dump(),
            map_data=map_data, cta_action="generate_itinerary",
        )

    # Informational place queries
    if is_info_query and not raw_answer:
        clean_q = (
            request.message
            .replace("Tell me more about ", "")
            .replace("tell me about ", "")
            .replace("Tell TravelOS about ", "")
            .replace("what makes it special", "")
            .strip()
        )
        search_enc = clean_q.replace(" ", "+")
        prompt = (
            f'The user is asking for details about a specific landmark or place: "{request.message}".\n\n'
            f'Provide a rich, exciting Markdown overview:\n'
            f'1. ### 📍 {clean_q}\n'
            f'2. ![Image](https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=800&q=80)\n'
            f'3. Concise 3-4 bullet points detailing:\n'
            f'   - What this place is\n'
            f'   - Why it is famous & top things to see/do there\n'
            f'   - Best time/tip to visit\n'
            f'4. Clickable reference link: [📖 Click here to explore more about {clean_q}]'
            f'(https://en.wikipedia.org/wiki/Special:Search?search={search_enc})'
        )
        try:
            raw_answer = llm_service.generate_response(prompt)
        except Exception:
            raw_answer = (
                f"### 📍 {clean_q}\n\n"
                f"![Image](https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=800&q=80)\n\n"
                f"A renowned destination featuring rich culture, iconic scenery, and vibrant history.\n\n"
                f"[📖 Click here to explore more about {clean_q}]"
                f"(https://en.wikipedia.org/wiki/Special:Search?search={search_enc})"
            )

        message = conversation_service.generate_reply(
            user_message=request.message,
            conversation_history=conversation_history,
            state_summary=state_summary,
            route=route,
            raw_answer=raw_answer,
            missing=[],
            enrichment=enrichment,
            weather=weather,
            currency=currency_data,
        )
        session_manager.add_message(session_id, "assistant", message)
        map_data = orchestrator._build_map_data(
            state=state,
            hotels=enrichment.get("hotels", []),
            activities=enrichment.get("activities", []),
            itinerary=[],
        )
        return ChatResponse(
            session_id=session_id, message=message,
            missing_information=[], travel_state=state.model_dump(),
            map_data=map_data,
        )

    # Budget feasibility check
    feasibility = budget_agent.check_budget_feasibility(state)
    if not feasibility.get("is_feasible", True):
        reply = feasibility["reason"]
        session_manager.add_message(session_id, "assistant", reply)
        map_data = orchestrator._build_map_data(state=state, hotels=[], activities=[], itinerary=[])
        return ChatResponse(
            session_id=session_id, message=reply,
            missing_information=[], travel_state=state.model_dump(),
            map_data=map_data,
        )

    # Auto re-plan if budget exceeded
    if enrichment.get("budget") and enrichment["budget"].remaining is not None and enrichment["budget"].remaining < 0:
        replan_res = budget_agent.auto_replan_under_budget(
            state=state,
            hotels=enrichment.get("hotels"),
            activities=enrichment.get("activities"),
            itinerary=enrichment.get("itinerary"),
        )
        if replan_res.get("adjusted"):
            enrichment["budget"] = replan_res["breakdown"]
            if replan_res.get("activities"):
                enrichment["activities"] = replan_res["activities"]
                state.activities = replan_res["activities"]

    # ----------------------------------------------------------
    # 10. Generate conversational reply
    # ----------------------------------------------------------
    message = conversation_service.generate_reply(
        user_message=request.message,
        conversation_history=conversation_history,
        state_summary=state_summary,
        route=route,
        raw_answer=raw_answer,
        missing=missing,
        enrichment=enrichment,
        weather=weather,
        currency=currency_data,
    )

    # ----------------------------------------------------------
    # 11. Save assistant reply to history
    # ----------------------------------------------------------
    session_manager.add_message(session_id, "assistant", message)

    # ----------------------------------------------------------
    # 12. Build map data
    # ----------------------------------------------------------
    map_data = enrichment.get("map_data") if enrichment else None
    if not map_data:
        map_data = orchestrator._build_map_data(
            state=state,
            hotels=enrichment.get("hotels", []) if enrichment else (state.hotels or []),
            activities=enrichment.get("activities", []) if enrichment else (state.activities or []),
            itinerary=enrichment.get("itinerary", []) if enrichment else (state.itinerary or []),
        )

    # ----------------------------------------------------------
    # 13. Return enriched response
    # ----------------------------------------------------------
    return ChatResponse(
        session_id=session_id,
        message=message,
        missing_information=missing,
        travel_state=state.model_dump(),
        sources=sources,
        agent_statuses=agent_statuses,
        flights=flights,
        hotels=enrichment.get("hotels") or state.hotels or [],
        weather=weather,
        currency=currency_data,
        activities=enrichment.get("activities") or state.activities or [],
        itinerary=enrichment.get("itinerary") or state.itinerary or [],
        budget=enrichment.get("budget") if enrichment else None,
        map_data=map_data,
        cta_action=None,
    )