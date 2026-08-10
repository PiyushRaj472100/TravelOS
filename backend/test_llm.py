from app.services.llm_service import LLMService


llm = LLMService()


message = """
I want to go to Patna for 10 days.
My budget is 3000 INR.
I choose train.
I love photography and local food.
"""


result = llm.extract_travel_information(message)


print("\n===== EXTRACTED TRAVEL INFORMATION =====\n")

print(result)

print("\n===== INDIVIDUAL VALUES =====\n")

print("Destinations:", result.destinations)
print("Duration:", result.duration_days)
print("Budget:", result.budget)
print("Currency:", result.currency)
print("Transportation:", result.transportation_preference)
print("Interests:", result.interests)