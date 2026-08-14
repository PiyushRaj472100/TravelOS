from app.models.travel_state import TravelState

from app.services.llm_service import LLMService

from app.rag.rag_manager import RAGManager

from app.agents.research_agent import ResearchAgent


# =================================================
# TEST RESEARCH AGENT
# =================================================

print("=" * 70)
print("TRAVELOS RESEARCH AGENT TEST")
print("=" * 70)


# =================================================
# 1. Create LLM Service
# =================================================

print()
print("Initializing LLM Service...")

llm_service = LLMService()

print("LLM Service: OK")


# =================================================
# 2. Create RAG Manager
# =================================================

print()
print("Initializing RAG Manager...")

rag_manager = RAGManager(
    llm_service=llm_service
)

print("RAG Manager: OK")


# =================================================
# 3. Get RAG Service
# =================================================

rag_service = (
    rag_manager.get_rag_service()
)

print()
print("RAG Service: OK")


# =================================================
# 4. Create Research Agent
# =================================================

research_agent = ResearchAgent(
    rag_service=rag_service
)

print()
print("Research Agent: OK")


# =================================================
# 5. Create Travel State
# =================================================

state = TravelState(

    destinations=[
        "Japan"
    ],

    countries=[
        "Japan"
    ],

    cities=[
        "Tokyo"
    ],

    duration_days=10,

    travelers=2,

    budget=3000,

    budget_currency="EUR",

    travel_style="relaxed",

    interests=[
        "culture",
        "food"
    ]
)


# =================================================
# 6. Display Travel State
# =================================================

print()
print("=" * 70)
print("TRAVEL STATE")
print("=" * 70)

print()

print(
    state.model_dump_json(
        indent=2
    )
)


# =================================================
# 7. Run Research Agent
# =================================================

print()
print("=" * 70)
print("RUNNING RESEARCH AGENT")
print("=" * 70)

print()

try:

    result = research_agent.research(
        state=state
    )

except Exception as e:

    print()
    print("=" * 70)
    print("RESEARCH AGENT FAILED")
    print("=" * 70)

    print()
    print(
        "Error:",
        str(e)
    )

    raise


# =================================================
# 8. Display Research Question
# =================================================

print()
print("=" * 70)
print("RESEARCH QUESTION")
print("=" * 70)

print()

print(
    result.get(
        "question"
    )
)


# =================================================
# 9. Display Research Answer
# =================================================

print()
print("=" * 70)
print("RESEARCH ANSWER")
print("=" * 70)

print()

print(
    result.get(
        "answer"
    )
)


# =================================================
# 10. Display Sources
# =================================================

sources = result.get(
    "sources",
    []
)


print()
print("=" * 70)
print("SOURCES")
print("=" * 70)

print()

print(
    f"Sources returned: {len(sources)}"
)


for index, source in enumerate(
    sources,
    start=1
):

    print()

    print(
        f"--- SOURCE {index} ---"
    )

    print(
        "Title:",
        source.get(
            "title"
        )
    )

    print(
        "Source:",
        source.get(
            "source"
        )
    )

    print(
        "Country:",
        source.get(
            "country"
        )
    )

    print(
        "Region:",
        source.get(
            "region"
        )
    )

    print(
        "City:",
        source.get(
            "city"
        )
    )

    print(
        "Category:",
        source.get(
            "category"
        )
    )

    print(
        "Score:",
        source.get(
            "score"
        )
    )


# =================================================
# 11. Final Validation
# =================================================

print()
print("=" * 70)

if result.get("answer"):

    print(
        "RESEARCH AGENT TEST: SUCCESS"
    )

else:

    print(
        "RESEARCH AGENT TEST: FAILED"
    )


print("=" * 70)