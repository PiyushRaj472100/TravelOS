import json

from app.services.llm_service import LLMService
from app.rag.query import RAGQuery


class QueryAnalyzer:

    def __init__(self, llm_service: LLMService):

        self.llm_service = llm_service

    def analyze(
        self,
        question: str
    ) -> RAGQuery:

        prompt = f"""
You are the query analysis component of a global
AI travel planning system.

Analyze the user's question.

Determine the most appropriate category.

Allowed categories:

- entry_requirements
- visa
- regulations
- transportation
- accommodation
- restaurants
- activities
- culture
- safety
- packing
- weather
- currency
- destination_information
- general

Also determine whether the question requires
current or live information.

Use:

needs_live_data = true

for information that can change over time, such as:

- exchange rates
- weather
- flight availability
- hotel prices
- current travel rules
- current visa requirements
- current transportation schedules

Do NOT invent destinations.

Only extract destinations explicitly mentioned
in the user's question.

Return ONLY valid JSON.

User question:

{question}

JSON format:

{{
    "question": "{question}",
    "category": "...",
    "countries": [],
    "regions": [],
    "cities": [],
    "needs_live_data": false
}}
"""

        response = self.llm_service.generate_response(
            prompt
        )

        data = json.loads(response)

        return RAGQuery.model_validate(data)