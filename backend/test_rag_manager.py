from app.services.llm_service import LLMService

from app.rag.rag_manager import RAGManager


llm_service = LLMService()

rag_manager = RAGManager(
    llm_service=llm_service
)

rag_service = (
    rag_manager.get_rag_service()
)


result = rag_service.answer(
    question="What are the entry requirements?",
    country="Country-A",
    category="entry_requirements",
    top_k=3
)


print("\n==============================")
print("RAG MANAGER TEST")
print("==============================")

print("\nANSWER:")
print(result["answer"])

print("\nSOURCES:")

for source in result["sources"]:

    print(source)