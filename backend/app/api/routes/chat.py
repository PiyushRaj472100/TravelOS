"""
TravelOS Chat Route — LangGraph Endpoint

This controller delegates message processing and multi-agent orchestration
directly to the compiled LangGraph workflow.
"""

from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.graph.graph import graph_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Processes user chat messages through the TravelOS LangGraph orchestration pipeline."""
    return graph_service.process_message(request)