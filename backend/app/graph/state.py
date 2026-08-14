"""
TravelOS LangGraph State Definition
"""

from typing import TypedDict, Optional, List, Dict, Any
from app.models.travel_state import TravelState
from app.models.travel_extraction import TravelExtraction
from app.models.chat import AgentStatus, ChatResponse, ChatSource


class AgentGraphState(TypedDict, total=False):
    # Session and message context
    session_id: str
    message: str
    travel_state: TravelState
    conversation_history: str
    state_summary: str

    # Questionnaire and context-aware flow
    current_field: Optional[str]
    missing_information: List[str]
    is_info_query: bool
    is_cta_click: bool
    itinerary_ready: bool

    # Short-circuit special response (currency switch, swap, etc.)
    special_response: Optional[ChatResponse]

    # Extraction and Query Routing
    extraction: Optional[TravelExtraction]
    query: Optional[Any]
    route: Optional[str]

    # Tool & Agent outputs
    live_result: Optional[Dict[str, Any]]
    raw_answer: Optional[str]
    enrichment: Optional[Dict[str, Any]]
    flights: List[Dict[str, Any]]
    weather: Optional[Dict[str, Any]]
    currency_data: Optional[Dict[str, Any]]
    agent_statuses: List[AgentStatus]
    sources: List[ChatSource]
    map_data: Optional[Dict[str, Any]]
    cta_action: Optional[str]

    # Final response
    final_message: Optional[str]
    final_response: Optional[ChatResponse]
