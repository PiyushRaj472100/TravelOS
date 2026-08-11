from app.models.travel_state import TravelState
from app.rag.context_builder import RAGContextBuilder


state = TravelState(
    destinations=["Paris"],
    countries=["France"],
    regions=["Île-de-France"],
    cities=["Paris"],
    duration_days=7,
    travelers=2,
    budget=150000,
    currency="INR",
    interests=["photography"],
    travel_style="leisure"
)


builder = RAGContextBuilder()


context = builder.build(
    state,
    "What should I know before travelling?"
)


print("\n===== RAG CONTEXT =====")

for key, value in context.items():

    print(f"{key}: {value}")