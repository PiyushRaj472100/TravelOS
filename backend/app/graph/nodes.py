"""
TravelOS LangGraph Nodes

Each node encapsulates a focused responsibility in the orchestration pipeline,
reusing existing tested services and agents.
"""

from typing import Dict, Any, List
from app.graph.state import AgentGraphState
from app.models.chat import AgentStatus, ChatResponse, ChatSource
from app.models.travel_extraction import TravelExtraction
from app.services.state_manager import StateManager
from app.services.missing_information import (
    MissingInformationDetector,
    _get_country_for_city,
)
from app.services.conversation_service import ConversationService


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


class GraphNodes:
    """Encapsulates LangGraph node functions with injected services and agents."""

    def __init__(
        self,
        llm_service,
        query_analyzer,
        query_router,
        live_query_service,
        rag_service,
        orchestrator,
        conversation_service: ConversationService,
        handlers,
        session_manager,
    ):
        self.llm_service = llm_service
        self.query_analyzer = query_analyzer
        self.query_router = query_router
        self.live_query_service = live_query_service
        self.rag_service = rag_service
        self.orchestrator = orchestrator
        self.conversation_service = conversation_service
        self.handlers = handlers
        self.session_manager = session_manager

    # -----------------------------------------------------------------------
    # Node 1: Special Handlers (Currency switch, hotel pick, swaps, etc.)
    # -----------------------------------------------------------------------
    def special_handlers_node(self, state: AgentGraphState) -> Dict[str, Any]:
        message = state["message"]
        travel_state = state["travel_state"]
        session_id = state["session_id"]

        for handler_fn in [
            self.handlers.handle_currency_switch,
            self.handlers.handle_expensive_activities,
            self.handlers.handle_activity_replacement,
            self.handlers.handle_hotel_selection,
            self.handlers.handle_domestic_transport,
            self.handlers.handle_budget_feasibility,
            self.handlers.handle_place_overview,
        ]:
            res = handler_fn(message, travel_state, session_id)
            if res is not None:
                return {
                    "special_response": res,
                    "final_response": res,
                }

        # Calculate current questionnaire field before message extraction
        missing_before = MissingInformationDetector.detect(travel_state)
        current_field = missing_before[0] if missing_before else None

        return {
            "special_response": None,
            "current_field": current_field,
        }

    # -----------------------------------------------------------------------
    # Node 2: Context-Aware Information Extraction
    # -----------------------------------------------------------------------
    def extraction_node(self, state: AgentGraphState) -> Dict[str, Any]:
        message = state["message"]
        current_field = state.get("current_field")
        conv_context = (
            ConversationService.get_field_question_text(current_field)
            if current_field else None
        )

        try:
            extraction = self.llm_service.extract_travel_information(
                user_message=message,
                current_field=current_field,
                conversation_context=conv_context,
            )
        except Exception as e:
            print(f"[LangGraph:ExtractionNode] LLM extraction error: {e}")
            extraction = TravelExtraction()

        return {"extraction": extraction}

    # -----------------------------------------------------------------------
    # Node 3: State Update & Missing Information Detection
    # -----------------------------------------------------------------------
    def state_update_node(self, state: AgentGraphState) -> Dict[str, Any]:
        travel_state = state["travel_state"]
        extraction = state.get("extraction") or TravelExtraction()
        message = state["message"]
        session_id = state["session_id"]
        current_field = state.get("current_field")

        # Update travel state
        travel_state = StateManager.update_state(travel_state, extraction)
        travel_state = MissingInformationDetector.fill_missing_from_context(
            travel_state, message, extraction, current_field=current_field
        )
        self.session_manager.save_state(session_id, travel_state)

        # Detect questionnaire and informational query status
        is_info_query = MissingInformationDetector.is_informational_or_place_query(message)
        missing = [] if is_info_query else MissingInformationDetector.detect(travel_state)
        itinerary_ready = MissingInformationDetector.is_ready_for_itinerary(travel_state)
        state_summary = ConversationService.state_summary(travel_state)

        is_cta_click = message.strip().lower() == "build my full itinerary now"

        return {
            "travel_state": travel_state,
            "missing_information": missing,
            "is_info_query": is_info_query,
            "itinerary_ready": itinerary_ready,
            "state_summary": state_summary,
            "is_cta_click": is_cta_click,
        }

    # -----------------------------------------------------------------------
    # Node 4: Query Analyzer & Router
    # -----------------------------------------------------------------------
    def query_analyzer_node(self, state: AgentGraphState) -> Dict[str, Any]:
        message = state["message"]
        try:
            query = self.query_analyzer.analyze(message)
        except Exception as e:
            print(f"[LangGraph:QueryAnalyzerNode] Error: {e}")
            query = self.query_analyzer._heuristic_analyze(message)

        route = self.query_router.route(query)
        return {
            "query": query,
            "route": route,
        }

    # -----------------------------------------------------------------------
    # Node 5a: Live Tools (Weather, Currency, Flights)
    # -----------------------------------------------------------------------
    def live_tools_node(self, state: AgentGraphState) -> Dict[str, Any]:
        query = state.get("query")
        travel_state = state["travel_state"]

        live_result = None
        raw_answer = ""
        weather = None
        currency_data = None
        flights: List[Dict[str, Any]] = []
        agent_statuses: List[AgentStatus] = list(state.get("agent_statuses") or [])

        try:
            live_result = self.live_query_service.handle(query)
        except Exception as e:
            print(f"[LangGraph:LiveToolsNode] Error: {e}")
            live_result = None
            raw_answer = (
                f"I'm sorry, I couldn't retrieve live {getattr(query, 'category', 'data')} data right now. "
                "Please try again in a moment."
            )

        if live_result:
            cat = getattr(query, "category", "")
            if cat == "weather":
                weather = live_result
                raw_answer = (
                    f"🌤️ Current weather in {live_result['city']}, "
                    f"{live_result['country']}: "
                    f"**{live_result['temperature']}°C** "
                    f"(feels like {live_result['apparent_temperature']}°C). "
                    f"Humidity: {live_result['humidity']}%. "
                    f"Wind: {live_result['wind_speed']} km/h."
                )
            elif cat == "currency":
                currency_data = live_result
                raw_answer = (
                    f"💱 Current exchange rate: "
                    f"**1 {live_result['base_currency']} = "
                    f"{live_result['rate']} {live_result['target_currency']}**"
                )
            elif cat == "flight":
                recommended = live_result.get("recommended", [])
                flights = [
                    self.orchestrator._serialize_flight(f, travel_state.currency)
                    for f in recommended
                ]
                raw_answer = _format_flight_message(flights)
                agent_statuses.append(AgentStatus(
                    agent="flights", status="done",
                    message=f"{len(flights)} flights found",
                ))

        return {
            "live_result": live_result,
            "raw_answer": raw_answer,
            "weather": weather,
            "currency_data": currency_data,
            "flights": flights,
            "agent_statuses": agent_statuses,
        }

    # -----------------------------------------------------------------------
    # Node 5b: RAG Knowledge (Destinations, Travel Rules, Advisories)
    # -----------------------------------------------------------------------
    def rag_knowledge_node(self, state: AgentGraphState) -> Dict[str, Any]:
        query = state.get("query")
        travel_state = state["travel_state"]
        message = state["message"]
        missing = state.get("missing_information") or []
        is_info_query = state.get("is_info_query", False)

        raw_answer = ""
        sources: List[ChatSource] = []

        # Only execute RAG answer if it's an explicit info query or questionnaire is completed
        if is_info_query or not missing:
            try:
                extracted_countries = list(query.countries) if (query and query.countries) else []
                extracted_cities = list(query.cities) if (query and query.cities) else []

                for c in extracted_cities:
                    c_country = _get_country_for_city(c)
                    if c_country:
                        c_title = c_country.capitalize()
                        if c_title not in extracted_countries:
                            extracted_countries.append(c_title)

                rag_result = self.rag_service.answer_with_state(
                    question=message,
                    state=travel_state,
                    top_k=5,
                    category=query.category if (query and query.category and query.category != "general") else None,
                    countries=extracted_countries if extracted_countries else None,
                    regions=query.regions if (query and query.regions) else None,
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
                print(f"[LangGraph:RAGNode] Error: {e}")
                try:
                    dest_str = ", ".join(
                        (query.countries if query else []) or (query.cities if query else [])
                        or travel_state.destinations or travel_state.cities or ["your destination"]
                    )
                    prompt = (
                        f'You are TravelOS, a knowledgeable AI travel planning assistant.\n\n'
                        f'User Question: "{message}"\n'
                        f'Trip Context: Destination: {dest_str}.\n\n'
                        f'Provide a clear, rich, accurate, structured, and engaging answer.'
                    )
                    raw_answer = self.llm_service.generate_response(prompt)
                except Exception as e2:
                    print(f"[LangGraph:RAGNode] Fallback error: {e2}")
                    raw_answer = (
                        "Please check official local government and tourism safety advisories "
                        "for up-to-date travel rules and regulations."
                    )

        return {
            "raw_answer": raw_answer,
            "sources": sources,
        }

    # -----------------------------------------------------------------------
    # Node 5c: Orchestrator & Planning (Hotels, Activities, Itinerary, Budget)
    # -----------------------------------------------------------------------
    def orchestrator_node(self, state: AgentGraphState) -> Dict[str, Any]:
        message = state["message"]
        travel_state = state["travel_state"]
        query = state.get("query")
        live_result = state.get("live_result")
        route = state.get("route", "planning")
        session_id = state["session_id"]
        itinerary_ready = state.get("itinerary_ready", False)
        is_cta_click = state.get("is_cta_click", False)
        wants_build = (
            is_cta_click
            or self.orchestrator._is_build_trip_request(message)
            or (itinerary_ready and not travel_state.itinerary)
        )
        questionnaire_in_progress = not itinerary_ready

        enrichment: Dict[str, Any] = {}
        agent_statuses: List[AgentStatus] = list(state.get("agent_statuses") or [])
        flights = list(state.get("flights") or [])
        raw_answer = state.get("raw_answer") or ""
        sources = list(state.get("sources") or [])

        run_orchestration = (
            (wants_build and itinerary_ready)
            or (itinerary_ready and not travel_state.itinerary)
            or (not questionnaire_in_progress and self.orchestrator._is_hotel_request(message))
            or (not questionnaire_in_progress and self.orchestrator._is_activity_request(message))
            or (not questionnaire_in_progress and self.orchestrator._is_budget_request(message))
            or route == "rag"
            or (route == "live" and live_result is not None)
        )

        if run_orchestration:
            try:
                enrichment = self.orchestrator.orchestrate(
                    query=query, state=travel_state, live_result=live_result
                )
                agent_statuses.extend(enrichment.get("agent_statuses", []))

                if not flights:
                    flights = enrichment.get("flights", [])

                if enrichment.get("activities"):
                    travel_state.activities = enrichment["activities"]
                if enrichment.get("hotels"):
                    travel_state.hotels = enrichment["hotels"]
                if enrichment.get("itinerary"):
                    travel_state.itinerary = enrichment["itinerary"]
                self.session_manager.save_state(session_id, travel_state)

                if not raw_answer and enrichment.get("research_answer"):
                    raw_answer = enrichment["research_answer"]
                    if enrichment.get("research_sources"):
                        sources = [
                            ChatSource(**s) if isinstance(s, dict) else s
                            for s in enrichment["research_sources"]
                        ]
            except Exception as e:
                print(f"[LangGraph:OrchestratorNode] Error: {e}")

        # Budget Feasibility & Auto-Replanning
        if enrichment.get("budget") and enrichment["budget"].remaining is not None and enrichment["budget"].remaining < 0:
            replan_res = self.orchestrator.budget_agent.auto_replan_under_budget(
                state=travel_state,
                hotels=enrichment.get("hotels"),
                activities=enrichment.get("activities"),
                itinerary=enrichment.get("itinerary"),
            )
            if replan_res.get("adjusted"):
                enrichment["budget"] = replan_res["breakdown"]
                if replan_res.get("activities"):
                    enrichment["activities"] = replan_res["activities"]
                    travel_state.activities = replan_res["activities"]

        flights = list(enrichment.get("flights") or flights)
        weather = enrichment.get("weather") or state.get("weather")

        return {
            "enrichment": enrichment,
            "agent_statuses": agent_statuses,
            "flights": flights,
            "weather": weather,
            "raw_answer": raw_answer,
            "sources": sources,
            "travel_state": travel_state,
        }

    # -----------------------------------------------------------------------
    # Node 6: Response Generator & Final ChatResponse Builder
    # -----------------------------------------------------------------------
    def response_generator_node(self, state: AgentGraphState) -> Dict[str, Any]:
        message = state["message"]
        travel_state = state["travel_state"]
        session_id = state["session_id"]
        conversation_history = state.get("conversation_history", "")
        state_summary = state.get("state_summary", "")
        route = state.get("route", "planning")
        raw_answer = state.get("raw_answer") or ""
        missing = state.get("missing_information") or []
        enrichment = state.get("enrichment") or {}
        weather = state.get("weather") or enrichment.get("weather")
        currency_data = state.get("currency_data")
        flights = state.get("flights") or enrichment.get("flights") or []

        sources = state.get("sources") or []
        agent_statuses = state.get("agent_statuses") or []
        is_cta_click = state.get("is_cta_click", False)
        is_info_query = state.get("is_info_query", False)
        itinerary_ready = state.get("itinerary_ready", False)

        # 1. Check if CTA clicked while questionnaire is incomplete
        if not itinerary_ready and is_cta_click:
            next_q = MissingInformationDetector.next_question(travel_state)
            if next_q:
                reply = f"Almost there! I just need a few more details before building your itinerary.\n\n{next_q}"
                self.session_manager.add_message(session_id, "assistant", reply)
                map_data = self.orchestrator._build_map_data(state=travel_state, hotels=[], activities=[], itinerary=[])
                return {
                    "final_response": ChatResponse(
                        session_id=session_id,
                        message=reply,
                        missing_information=MissingInformationDetector.detect(travel_state),
                        travel_state=travel_state.model_dump(),
                        map_data=map_data,
                    )
                }

        # 2. Check CTA generation gate: trigger CTA button when all steps complete AND itinerary not yet generated
        if (
            not travel_state.itinerary
            and not enrichment.get("itinerary")
            and not getattr(travel_state, "cta_shown", False)
            and not missing
            and not is_cta_click
            and route not in ("rag", "live")
            and not raw_answer
            and not is_info_query
        ):
            travel_state.cta_shown = True
            self.session_manager.save_state(session_id, travel_state)
            cta_message = (
                "🎯 **Perfect! I have everything I need to plan your complete trip.**\n\n"
                f"{state_summary}\n\n"
                "Click below to generate your **full personalised itinerary** — "
                "day-by-day plan, hotels, activities & complete budget breakdown."
            )
            self.session_manager.add_message(session_id, "assistant", cta_message)
            map_data = self.orchestrator._build_map_data(state=travel_state, hotels=[], activities=[], itinerary=[])
            return {
                "final_response": ChatResponse(
                    session_id=session_id,
                    message=cta_message,
                    missing_information=[],
                    travel_state=travel_state.model_dump(),
                    map_data=map_data,
                    cta_action="generate_itinerary",
                )
            }


        # 3. Check budget feasibility
        feasibility = self.orchestrator.budget_agent.check_budget_feasibility(travel_state)
        if not feasibility.get("is_feasible", True):
            reply = feasibility["reason"]
            self.session_manager.add_message(session_id, "assistant", reply)
            map_data = self.orchestrator._build_map_data(state=travel_state, hotels=[], activities=[], itinerary=[])
            return {
                "final_response": ChatResponse(
                    session_id=session_id,
                    message=reply,
                    missing_information=[],
                    travel_state=travel_state.model_dump(),
                    map_data=map_data,
                )
            }

        # 4. Generate conversational reply
        reply_message = self.conversation_service.generate_reply(
            user_message=message,
            conversation_history=conversation_history,
            state_summary=state_summary,
            route=route,
            raw_answer=raw_answer,
            missing=missing,
            enrichment=enrichment,
            weather=weather,
            currency=currency_data,
        )

        # 5. Save assistant reply in session history
        self.session_manager.add_message(session_id, "assistant", reply_message)

        # 6. Build map data
        map_data = enrichment.get("map_data") if enrichment else None
        if not map_data:
            map_data = self.orchestrator._build_map_data(
                state=travel_state,
                hotels=enrichment.get("hotels", []) if enrichment else (travel_state.hotels or []),
                activities=enrichment.get("activities", []) if enrichment else (travel_state.activities or []),
                itinerary=enrichment.get("itinerary", []) if enrichment else (travel_state.itinerary or []),
            )

        # 7. Construct final ChatResponse
        response = ChatResponse(
            session_id=session_id,
            message=reply_message,
            missing_information=missing,
            travel_state=travel_state.model_dump(),
            sources=sources,
            agent_statuses=agent_statuses,
            flights=flights,
            hotels=enrichment.get("hotels") or travel_state.hotels or [],
            weather=weather,
            currency=currency_data,
            activities=enrichment.get("activities") or travel_state.activities or [],
            itinerary=enrichment.get("itinerary") or travel_state.itinerary or [],
            budget=enrichment.get("budget") if enrichment else None,
            map_data=map_data,
            cta_action=None,
        )

        return {
            "final_message": reply_message,
            "final_response": response,
        }
