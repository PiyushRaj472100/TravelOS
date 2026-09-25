"""
TravelOS Chat Route — LangGraph Endpoint

This controller delegates message processing and multi-agent orchestration
directly to the compiled LangGraph workflow.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.chat import ChatRequest, ChatResponse
from app.graph.graph import graph_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Processes user chat messages through the TravelOS LangGraph orchestration pipeline."""
    return graph_service.process_message(request)


@router.post("/stream")
def chat_stream(request: ChatRequest):
    """Streams live multi-agent execution events followed by the final ChatResponse."""
    return StreamingResponse(
        graph_service.process_message_stream(request),
        media_type="text/event-stream",
    )