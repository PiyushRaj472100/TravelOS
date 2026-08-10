from uuid import uuid4

from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.models.travel_state import TravelState


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):

    session_id = request.session_id or str(uuid4())

    travel_state = TravelState()

    return ChatResponse(
        session_id=session_id,
        message="I received your travel request.",
        missing_information=[],
        travel_state=travel_state.model_dump()
    )