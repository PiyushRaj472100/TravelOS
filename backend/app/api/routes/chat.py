from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService
from app.services.state_manager import StateManager
from app.services.missing_information import MissingInformationDetector
from app.services.session_manager import session_manager


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


llm_service = LLMService()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):

    # ---------------------------------
    # 1. Get or create session ID
    # ---------------------------------

    session_id = request.session_id or str(uuid4())


    # ---------------------------------
    # 2. Get existing TravelState
    # ---------------------------------

    state = session_manager.get_state(session_id)


    # ---------------------------------
    # 3. Extract information from
    #    the user's latest message
    # ---------------------------------

    try:
        print("1. Received request")
        print("2. Sending message to Gemini...")

        extraction = llm_service.extract_travel_information(
            request.message
        )
        print("3. Gemini response received")
        print("4. Extraction:", extraction)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"LLM extraction failed: {str(e)}"
        )


    # ---------------------------------
    # 4. Merge new information into
    #    existing TravelState
    # ---------------------------------

    state = StateManager.update_state(
        state,
        extraction
    )


    # ---------------------------------
    # 5. Save updated state
    # ---------------------------------

    session_manager.save_state(
        session_id,
        state
    )


    # ---------------------------------
    # 6. Find missing information
    # ---------------------------------

    missing = MissingInformationDetector.detect(
        state
    )


    # ---------------------------------
    # 7. Decide what the AI should say
    # ---------------------------------

    if missing:

        next_question = (
            MissingInformationDetector.next_question(
                state
            )
        )

    else:

        next_question = (
            "Great! I have enough basic information "
            "to start planning your trip."
        )


    # ---------------------------------
    # 8. Return response
    # ---------------------------------

    return ChatResponse(
        session_id=session_id,
        message=next_question,
        missing_information=missing,
        travel_state=state.model_dump()
    )