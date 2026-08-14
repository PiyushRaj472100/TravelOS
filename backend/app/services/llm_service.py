import time
from typing import Optional
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.models.travel_extraction import TravelExtraction


class LLMService:

    MODELS = [
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
        "gemini-3.7-flash",
    ]

    def __init__(self):

        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=15000
            )
        )

        self.model = "gemini-flash-latest"

    def _call_with_fallback(self, **kwargs):
        """Try primary model, then fall back to backup models on transient errors."""
        last_error = None
        for model_name in self.MODELS:
            try:
                call_kwargs = dict(kwargs)
                call_kwargs["model"] = model_name
                return self.client.models.generate_content(**call_kwargs)
            except Exception as e:
                err_str = str(e)
                print(f"[LLMService] Model {model_name} failed: {err_str[:120]}, trying fallback...")
                last_error = e
                time.sleep(0.3)

        raise last_error

    def extract_travel_information(
        self,
        user_message: str,
        current_field: Optional[str] = None,
        conversation_context: Optional[str] = None,
    ) -> TravelExtraction:
        """
        Extract travel information from a user message.

        When `current_field` is provided, the LLM knows which question
        was just asked so it can correctly classify the user's answer
        (e.g. "Mumbai" as origin, not destination).

        Args:
            user_message: The raw user message.
            current_field: The questionnaire field currently being collected
                           (e.g. "origin", "destination", "duration", "budget").
            conversation_context: A one-sentence summary of the last AI question
                                  asked, for additional context.
        """

        # --- Build context injection ---
        context_block = ""
        if current_field and conversation_context:
            context_block = f"""
IMPORTANT CONTEXT:
The AI just asked the user: "{conversation_context}"
The field currently being collected is: "{current_field}"
Therefore interpret the user's answer in relation to that question.

Field meaning guide (use ONLY for the current field, do not invent others):
  - "origin"        → the user's departure city / starting location
  - "destination"   → the city/country the user wants to visit
  - "duration"      → the number of days for the trip (NOT days from now)
  - "budget"        → the total budget amount and currency
  - "travelers"     → the number of people travelling
  - "traveler_type" → solo / couple / family / friends / business
  - "transit"       → preferred transport (flight / train / bus)
  - "accommodation" → budget / mid-range / luxury preference
  - "interests"     → what the user wants to do (adventure, culture, food, etc.)

Examples for the current field "{current_field}":
"""
            examples = {
                "origin": (
                    '  User: "Mumbai"            → origin = "Mumbai"\n'
                    '  User: "I am from Delhi"   → origin = "Delhi"\n'
                    '  User: "Leaving from NYC"  → origin = "New York"\n'
                    '  User: "My city is London" → origin = "London"\n'
                    '  DO NOT set destination from these answers.\n'
                ),
                "destination": (
                    '  User: "London"            → destinations = ["London"]\n'
                    '  User: "I want to go to Paris" → destinations = ["Paris"]\n'
                    '  User: "Japan and Korea"   → destinations = ["Japan", "Korea"]\n'
                ),
                "duration": (
                    '  User: "5 days"            → duration_days = 5\n'
                    '  User: "a week"            → duration_days = 7\n'
                    '  User: "10 nights"         → duration_days = 10\n'
                    '  IMPORTANT: "4 days" means the TRIP is 4 days long, NOT 4 days from now.\n'
                ),
                "budget": (
                    '  User: "80000 rupees"      → budget = 80000, currency = "INR"\n'
                    '  User: "$2000"             → budget = 2000, currency = "USD"\n'
                    '  User: "2 lakh"            → budget = 200000, currency = "INR"\n'
                ),
                "travelers": (
                    '  User: "2"                 → travelers = 2\n'
                    '  User: "just me"           → travelers = 1\n'
                    '  User: "family of 4"       → travelers = 4\n'
                ),
            }
            context_block += examples.get(current_field, "")

        elif current_field:
            # current_field without conversation_context — minimal hint
            context_block = f"""
IMPORTANT CONTEXT:
The field currently being collected is: "{current_field}"
Interpret the user's short answer as a value for this field.
If the user just says a city name and the field is "origin", set origin to that city — do NOT set destination.
If the field is "duration", interpret numbers as trip length in days, not days from now.
"""

        prompt = f"""You are the information extraction component of an AI travel planning system.

Extract ONLY information that the user explicitly stated.
Do NOT guess.
Do NOT invent information that the user did not provide.
Do NOT infer a preference the user did not state.
{context_block}
Multi-field extraction examples:
  "I want to go to London next week for 4 days"
  → destinations = ["London"], start_date = "next week", duration_days = 4

  "I'm leaving from Mumbai and going to Paris next month for 7 days"
  → origin = "Mumbai", destinations = ["Paris"], start_date = "next month", duration_days = 7

  "2 people, budget $3000"
  → travelers = 2, budget = 3000, currency = "USD"

IMPORTANT: "for X days" always means trip duration (duration_days = X), not a future date.
IMPORTANT: "next week / next month / in December" always means start_date, not duration.

User message:

{user_message}
"""

        try:
            response = self._call_with_fallback(
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
        except Exception as e:
            print(f"[LLMService] Extraction LLM failed ({e}), using baseline extraction")
            return TravelExtraction()

    def generate_response(
        self,
        prompt: str
    ) -> str:

        response = self._call_with_fallback(
            contents=prompt
        )

        return response.text