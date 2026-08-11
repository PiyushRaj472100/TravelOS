from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.rag.rag_manager import RAGManager
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.query_router import QueryRouter

from app.models.chat import (
    ChatRequest,
    ChatResponse
)

from app.services.llm_service import LLMService
from app.services.state_manager import StateManager
from app.services.missing_information import (
    MissingInformationDetector
)
from app.services.session_manager import session_manager
from app.services.live_query_service import (
    LiveQueryService
)


# =================================================
# Router
# =================================================

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


# =================================================
# Services
# =================================================

llm_service = LLMService()

query_analyzer = QueryAnalyzer(
    llm_service
)

query_router = QueryRouter()

live_query_service = LiveQueryService()

rag_manager = RAGManager(
    llm_service=llm_service
)

rag_service = rag_manager.get_rag_service()


# =================================================
# Chat Endpoint
# =================================================

@router.post(
    "",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest
):

    # ---------------------------------------------
    # 1. Get or create session ID
    # ---------------------------------------------

    session_id = (
        request.session_id
        or str(uuid4())
    )


    # ---------------------------------------------
    # 2. Get existing TravelState
    # ---------------------------------------------

    state = session_manager.get_state(
        session_id
    )


    # ---------------------------------------------
    # 3. Extract travel information
    #    from the user's latest message
    # ---------------------------------------------

    try:

        print(
            "1. Received request"
        )

        print(
            "2. Sending message to Gemini..."
        )

        extraction = (
            llm_service
            .extract_travel_information(
                request.message
            )
        )

        print(
            "3. Gemini response received"
        )

        print(
            "4. Extraction:",
            extraction
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "LLM extraction failed: "
                f"{str(e)}"
            )
        )


    # ---------------------------------------------
    # 4. Merge extracted information
    #    into TravelState
    # ---------------------------------------------

    state = StateManager.update_state(
        state,
        extraction
    )


    # ---------------------------------------------
    # 5. Save updated TravelState
    # ---------------------------------------------

    session_manager.save_state(
        session_id,
        state
    )


    # ---------------------------------------------
    # 6. Analyze the user's query
    # ---------------------------------------------

    try:

        query = query_analyzer.analyze(
            request.message
        )

        print(
            "5. Query analysis:",
            query
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Query analysis failed: "
                f"{str(e)}"
            )
        )


    # ---------------------------------------------
    # 7. Determine route
    # ---------------------------------------------

    route = query_router.route(
        query
    )

    print(
        "6. Query route:",
        route
    )


    # =================================================
    # 8. LIVE ROUTE
    # =================================================

    if route == "live":

        try:

            result = live_query_service.handle(
                query
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Live data request failed: "
                    f"{str(e)}"
                )
            )


        # -----------------------------------------
        # Currency response
        # -----------------------------------------

        if query.category == "currency":

            answer = (
                "The current reference exchange "
                "rate is approximately "
                f"1 {result['base_currency']} = "
                f"{result['rate']} "
                f"{result['target_currency']}."
            )

        else:

            answer = str(result)


        return ChatResponse(
            session_id=session_id,
            message=answer,
            missing_information=[],
            travel_state=state.model_dump()
        )


    # =================================================
    # 9. RAG ROUTE
    # =================================================

    elif route == "rag":

        try:

            rag_result = (
                rag_service.answer_with_state(
                    question=request.message,
                    state=state,
                    top_k=5
                )
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=(
                    "RAG request failed: "
                    f"{str(e)}"
                )
            )


        return ChatResponse(
            session_id=session_id,
            message=rag_result["answer"],
            missing_information=[],
            travel_state=state.model_dump()
        )


    # =================================================
    # 10. PLANNING ROUTE
    # =================================================

    elif route == "planning":

        # -----------------------------------------
        # Find missing travel information
        # -----------------------------------------

        missing = (
            MissingInformationDetector.detect(
                state
            )
        )


        # -----------------------------------------
        # Decide what the AI should ask/say
        # -----------------------------------------

        if missing:

            next_question = (
                MissingInformationDetector
                .next_question(
                    state
                )
            )

        else:

            next_question = (
                "Great! I have enough basic "
                "information to start planning "
                "your trip."
            )


        # -----------------------------------------
        # Return planning response
        # -----------------------------------------

        return ChatResponse(
            session_id=session_id,
            message=next_question,
            missing_information=missing,
            travel_state=state.model_dump()
        )


    # =================================================
    # 11. Unknown route
    # =================================================

    else:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unknown query route: {route}"
            )
        )