from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.models.travel_extraction import TravelExtraction


class LLMService:

    def __init__(self):

        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=30000
            )
        )

        self.model = "gemini-3.1-flash-lite"

    def extract_travel_information(
        self,
        user_message: str
    ) -> TravelExtraction:

        prompt = f"""
You are the information extraction component of an AI travel planning system.

Extract ONLY information that the user explicitly stated.

Do NOT guess.
Do NOT invent information.
Do NOT infer a preference that the user did not state.

For example:

If the user says:
"I want to visit Japan for 10 days"

extract:
destination = Japan
duration_days = 10

Do NOT invent:
budget
number of travelers
travel style
interests

User message:

{user_message}
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema":
                    TravelExtraction.model_json_schema(),
            },
        )

        return TravelExtraction.model_validate_json(
            response.text
        )

    def generate_response(
        self,
        prompt: str
    ) -> str:

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text