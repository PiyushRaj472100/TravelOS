"""
TravelOS LangGraph Graph Builder & Runner
"""

from uuid import uuid4
# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, START, END

from app.graph.state import AgentGraphState
from app.graph.nodes import GraphNodes
from app.graph.edges import (
    route_after_special_handlers,
    route_after_query_analysis,
)

from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService
from app.services.session_manager import session_manager
from app.services.live_query_service import LiveQueryService
from app.services.conversation_service import ConversationService
from app.services.conversation_handlers import ConversationHandlers

from app.rag.rag_manager import RAGManager
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.query_router import QueryRouter

from app.agents.research_agent import ResearchAgent
from app.agents.hotel_agent import HotelAgent
from app.agents.activity_agent import ActivityAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.supervisor import OrchestratorAgent


class GraphService:
    """Service that compiles and runs the TravelOS LangGraph."""

    def __init__(self):
        # 1. Initialize services & agents
        self.llm_service = LLMService()
        self.query_analyzer = QueryAnalyzer(self.llm_service)
        self.query_router = QueryRouter()
        self.live_query_service = LiveQueryService()
        self.rag_manager = RAGManager(llm_service=self.llm_service)
        self.rag_service = self.rag_manager.get_rag_service()

        self.research_agent = ResearchAgent(rag_service=self.rag_service)
        self.hotel_agent = HotelAgent()
        self.activity_agent = ActivityAgent(
            rag_service=self.rag_service,
            llm_service=self.llm_service,
            currency_service=self.live_query_service.currency_service,
        )
        self.itinerary_agent = ItineraryAgent(
            llm_service=self.llm_service,
            currency_service=self.live_query_service.currency_service,
        )
        self.budget_agent = BudgetAgent(
            currency_service=self.live_query_service.currency_service
        )

        self.orchestrator = OrchestratorAgent(
            research_agent=self.research_agent,
            hotel_agent=self.hotel_agent,
            activity_agent=self.activity_agent,
            itinerary_agent=self.itinerary_agent,
            budget_agent=self.budget_agent,
            currency_service=self.live_query_service.currency_service,
            flight_service=self.live_query_service.flight_service,
            weather_service=self.live_query_service.weather_service,
        )

        self.conversation_service = ConversationService(llm_service=self.llm_service)

        self.handlers = ConversationHandlers(
            session_manager=session_manager,
            live_query_service=self.live_query_service,
            activity_agent=self.activity_agent,
            hotel_agent=self.hotel_agent,
            budget_agent=self.budget_agent,
            orchestrator=self.orchestrator,
            llm_service=self.llm_service,
        )

        # 2. Initialize node functions
        self.nodes = GraphNodes(
            llm_service=self.llm_service,
            query_analyzer=self.query_analyzer,
            query_router=self.query_router,
            live_query_service=self.live_query_service,
            rag_service=self.rag_service,
            orchestrator=self.orchestrator,
            conversation_service=self.conversation_service,
            handlers=self.handlers,
            session_manager=session_manager,
        )

        # 3. Build and compile StateGraph
        self.compiled_graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentGraphState)

        # Add Nodes
        workflow.add_node("special_handlers_node", self.nodes.special_handlers_node)
        workflow.add_node("extraction_node", self.nodes.extraction_node)
        workflow.add_node("state_update_node", self.nodes.state_update_node)
        workflow.add_node("query_analyzer_node", self.nodes.query_analyzer_node)
        workflow.add_node("live_tools_node", self.nodes.live_tools_node)
        workflow.add_node("rag_knowledge_node", self.nodes.rag_knowledge_node)
        workflow.add_node("orchestrator_node", self.nodes.orchestrator_node)
        workflow.add_node("response_generator_node", self.nodes.response_generator_node)

        # Add Edges & Conditional Edges
        workflow.add_edge(START, "special_handlers_node")

        workflow.add_conditional_edges(
            "special_handlers_node",
            route_after_special_handlers,
            {
                "end": END,
                "extraction_node": "extraction_node",
            },
        )

        workflow.add_edge("extraction_node", "state_update_node")
        workflow.add_edge("state_update_node", "query_analyzer_node")

        workflow.add_conditional_edges(
            "query_analyzer_node",
            route_after_query_analysis,
            {
                "live_tools_node": "live_tools_node",
                "rag_knowledge_node": "rag_knowledge_node",
                "orchestrator_node": "orchestrator_node",
            },
        )

        workflow.add_edge("live_tools_node", "response_generator_node")
        workflow.add_edge("rag_knowledge_node", "response_generator_node")
        workflow.add_edge("orchestrator_node", "response_generator_node")
        workflow.add_edge("response_generator_node", END)

        return workflow.compile()

    def process_message(self, request: ChatRequest) -> ChatResponse:
        """Runs the LangGraph orchestration pipeline for an incoming user message."""
        session_id = request.session_id or str(uuid4())
        travel_state = session_manager.get_state(session_id)
        conversation_history = session_manager.get_history_text(session_id)

        # Add user message to session history
        session_manager.add_message(session_id, "user", request.message)

        initial_state: AgentGraphState = {
            "session_id": session_id,
            "message": request.message,
            "travel_state": travel_state,
            "conversation_history": conversation_history,
            "special_response": None,
            "final_response": None,
        }

        # Execute LangGraph
        result_state = self.compiled_graph.invoke(initial_state)

        # Return final response
        if result_state.get("special_response"):
            return result_state["special_response"]

        return result_state.get("final_response") or result_state.get("special_response")


# Singleton instance
graph_service = GraphService()
compiled_graph = graph_service.compiled_graph
