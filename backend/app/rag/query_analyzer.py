import json

from app.services.llm_service import LLMService
from app.rag.query import RAGQuery


class QueryAnalyzer:

    def __init__(
        self,
        llm_service: LLMService
    ):

        self.llm_service = llm_service

    def analyze(
        self,
        question: str
    ) -> RAGQuery:

        prompt = f"""
You are the query analysis component of a global
AI travel planning system.

Analyze the user's question and determine:

1. What the user is trying to do.
2. The most appropriate travel category.
3. Whether live/current information is required.
4. Any explicitly mentioned countries, regions,
   or cities.


# QUERY TYPE
=============

Determine the user's intent.

Use:

query_type = "planning"

when the user is providing trip information,
requesting trip planning, or continuing a
travel-planning conversation.

Examples:

"I want to visit Japan for 10 days."
→ planning

"I am going to Paris next month."
→ planning

"I have a budget of 2000 euros."
→ planning

"I want a relaxing trip to Italy."
→ planning

"I will travel with my family."
→ planning


Use:

query_type = "knowledge"

when the user is asking for travel knowledge,
facts, explanations, recommendations, or
guidance that should be answered using the
travel knowledge base.

Examples:

"What should I know about Japanese culture?"
→ knowledge

"What should I know about Paris?"
→ knowledge

"What should I pack for Japan?"
→ knowledge

"How does public transportation work in Italy?"
→ knowledge

"What are the entry requirements?"
→ knowledge

"What are Japanese customs?"
→ knowledge


IMPORTANT:

A simple statement about the user's trip is
PLANNING, not knowledge retrieval.

For example:

"I want to visit Japan for 10 days."

must produce:

query_type = "planning"

NOT:

query_type = "knowledge"


# ALLOWED CATEGORIES
=====================

Use only one of these categories:

- entry_requirements
- visa
- regulations
- transportation
- flight
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


# LIVE DATA RULE
=================

Set:

needs_live_data = true

ONLY when the user explicitly asks for
CURRENT or LIVE information.

Examples:

"What is the weather in Tokyo tomorrow?"
→ true

"What is the current exchange rate from INR to EUR?"
→ true

"What are the current visa requirements for Japan?"
→ true

"Are flights available tomorrow?"
→ true

"What are the current hotel prices?"
→ true

"What are the transportation schedules today?"
→ true


Set:

needs_live_data = false

when the user asks for general, educational,
or stable travel knowledge.

Examples:

"What are the entry requirements?"
→ false

"What should I know about Japanese culture?"
→ false

"How does public transportation work in Japan?"
→ false

"What should I pack for Japan?"
→ false

"What are Japanese customs?"
→ false




FLIGHT LIVE DATA RULE
=====================

For flight search queries:

needs_live_data = true

because flight availability, schedules,
and prices must be obtained from the
live flight provider.

Examples:

"Find flights from London to Dubai."
→ needs_live_data = true

"Find cheap flights from Delhi to Tokyo."
→ needs_live_data = true

"Are there flights from Paris to Rome?"
→ needs_live_data = true


IMPORTANT:

Do NOT mark a question as live merely because
the information could change over time.

For example:

"What are the entry requirements?"
→ false

"What are the current entry requirements?"
→ true


# DESTINATION EXTRACTION
=========================

Extract countries, regions, and cities ONLY when
they are explicitly mentioned in the question.

Do NOT guess destinations.

Do NOT infer a destination from general knowledge.

Examples:

"I want to visit Japan."
→ countries: ["Japan"]

"What should I know about Tokyo?"
→ cities: ["Tokyo"]

"Tell me about Kansai."
→ regions: ["Kansai"]

"What is the weather in Tokyo?"
→ cities: ["Tokyo"]


# CATEGORY RULES
=================

Use "currency" for questions about:

- exchange rates
- currency conversion
- money conversion

Use "weather" for:

- current weather
- weather forecasts
- tomorrow's weather

Use "entry_requirements" for general questions
about entering a country.

Use "visa" for visa-related questions.

Use "transportation" for general transportation
knowledge.

Use "accommodation" for hotels and lodging.

Use "culture" for cultural customs and traditions.

Use "packing" for packing recommendations.

Use "safety" for general travel safety.

Use "destination_information" for general
destination knowledge.

Use "general" when no other category is appropriate.
Use "flight" for:

- flight search
- airline tickets
- air tickets
- flights between destinations
- finding available flights
- comparing flight options
- cheap flights
- direct flights
- connecting flights

Use "flight" for questions specifically asking
to search, find, compare, or check flights or
air tickets.

Examples:

"Find flights from London to Dubai."
→ category: "flight"

"Are there flights from Delhi to Tokyo?"
→ category: "flight"

"Find cheap flights from Paris to Rome."
→ category: "flight"

"Show me flights from London to Dubai tomorrow."
→ category: "flight"


# FLIGHT DATA EXTRACTION
=========================

When the category is "flight", extract the following
information when explicitly available:

origin:
The departure airport or city.

destination:
The arrival airport or city.

departure_date:
The requested departure date.

passengers:
Number of travelers if explicitly mentioned.
Otherwise use 1.

cabin_class:
Use one of:
- economy
- premium_economy
- business
- first

If not specified, use:
economy

max_connections:
Maximum number of connections if explicitly
specified.

If not specified, use:
1

# IMPORTANT INTERACTION RULE
=============================

The query_type determines the user's primary intent.

If the user is giving information about their own
trip, use:

query_type = "planning"

even if the message contains a destination,
duration, budget, travelers, or other trip details.

Examples:

"I want to visit Japan for 10 days."
→ query_type = "planning"

"My budget is 2000 euros."
→ query_type = "planning"

"I am traveling to France with my family."
→ query_type = "planning"

"I prefer hotels."
→ query_type = "planning"


If the user asks a knowledge question, use:

query_type = "knowledge"

Examples:

"What are Japanese customs?"
→ query_type = "knowledge"

"What should I pack for Japan?"
→ query_type = "knowledge"

"What are the entry requirements?"
→ query_type = "knowledge"


If the user explicitly asks for current/live
information:

needs_live_data = true

This takes priority for routing to the live
information system.





# OUTPUT
=========

Return ONLY valid JSON.

Do not include markdown.

Do not include explanations.

User question:

{question}

JSON format:

{{
     "question": "{question}",
    "category": "...",
    "countries": [],
    "regions": [],
    "cities": [],
    "needs_live_data": false,
    "query_type": "planning",

    "origin": null,
    "destination": null,
    "departure_date": null,
    "passengers": 1,
    "cabin_class": "economy",
    "max_connections": 1
}}
"""

        response = self.llm_service.generate_response(
            prompt
        )

        data = json.loads(response)

        return RAGQuery.model_validate(
            data
        )