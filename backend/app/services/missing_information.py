from app.models.travel_state import TravelState


# ============================================================
# Country → cities mapping (used for domestic trip detection)
# ============================================================

_COUNTRY_CITIES: dict[str, list[str]] = {
    "india": [
        "delhi", "new delhi", "mumbai", "bombay", "goa", "bangalore", "bengaluru",
        "jaipur", "chennai", "kolkata", "calcutta", "hyderabad", "pune",
        "kochi", "cochin", "ahmedabad", "surat", "lucknow", "agra", "varanasi",
        "rishikesh", "shimla", "manali", "leh", "ladakh", "amritsar", "chandigarh",
        "bhubaneswar", "bhopal", "indore", "nagpur", "mysuru", "mysore",
        "thiruvananthapuram", "trivandrum", "patna", "ranchi", "dehradun",
        "haridwar", "darjeeling", "gangtok", "shillong", "guwahati",
    ],
    "japan": [
        "tokyo", "kyoto", "osaka", "hiroshima", "fukuoka", "sapporo", "hokkaido",
        "nagoya", "kobe", "nara", "yokohama", "sendai", "kanazawa", "matsuyama",
        "kagoshima", "okinawa",
    ],
    "usa": [
        "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
        "san antonio", "san diego", "dallas", "san jose", "austin", "jacksonville",
        "san francisco", "seattle", "denver", "nashville", "boston", "miami",
        "atlanta", "las vegas", "portland", "memphis", "louisville", "baltimore",
        "honolulu", "washington dc", "washington d.c.",
    ],
    "uk": [
        "london", "manchester", "birmingham", "leeds", "glasgow", "liverpool",
        "edinburgh", "bristol", "sheffield", "cardiff", "belfast", "newcastle",
        "nottingham", "leicester", "coventry", "bradford",
    ],
    "australia": [
        "sydney", "melbourne", "brisbane", "perth", "adelaide", "gold coast",
        "canberra", "hobart", "darwin", "cairns", "geelong",
    ],
    "germany": [
        "berlin", "munich", "hamburg", "frankfurt", "cologne", "düsseldorf",
        "stuttgart", "leipzig", "dresden", "nuremberg",
    ],
    "france": [
        "paris", "marseille", "lyon", "toulouse", "nice", "nantes", "strasbourg",
        "bordeaux", "lille", "rennes", "reims",
    ],
    "italy": [
        "rome", "milan", "naples", "turin", "palermo", "genoa", "bologna",
        "florence", "bari", "venice", "verona", "catania",
    ],
    "china": [
        "beijing", "shanghai", "guangzhou", "shenzhen", "chengdu", "chongqing",
        "xi'an", "xian", "hangzhou", "wuhan", "nanjing", "tianjin",
    ],
    "thailand": [
        "bangkok", "phuket", "chiang mai", "pattaya", "koh samui", "krabi",
        "hua hin", "ayutthaya",
    ],
    "indonesia": [
        "bali", "jakarta", "lombok", "yogyakarta", "surabaya", "bandung",
        "medan", "makassar",
    ],
    "spain": [
        "madrid", "barcelona", "seville", "valencia", "malaga", "bilbao",
        "granada", "palma", "ibiza", "tenerife",
    ],
    "uae": [
        "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah",
    ],
}


def _get_country_for_city(city: str) -> str | None:
    """Return the country key for a city name, or None if unknown."""
    city_lower = city.lower().strip()
    for country, cities in _COUNTRY_CITIES.items():
        if any(city_lower == c or c in city_lower or city_lower in c for c in cities):
            return country
    return None


def _is_domestic_trip(origin: str, destination: str) -> bool:
    """Return True when origin and destination are in the same country."""
    orig_country = _get_country_for_city(origin)
    dest_country = _get_country_for_city(destination)
    if orig_country and dest_country:
        return orig_country == dest_country
    return False


# ============================================================
# Budget feasibility check keywords
# ============================================================

_FEASIBILITY_TRIGGERS = [
    "can i get", "is it possible to get", "can i afford", "will i get",
    "can we get", "can i have", "is it feasible", "fit in my budget",
    "fit in the budget", "fit in budget", "within my budget", "within budget",
    "is business class possible", "is business class in budget",
    "is luxury", "is a luxury", "can i book luxury", "luxury hotel in budget",
    "luxury hotel within", "can i stay in luxury", "can i include",
    "can i still", "will it fit", "does it fit", "does this fit",
    "would that fit", "would this fit", "possible within", "possible in my",
    "doable in", "is that doable", "is this doable", "is that possible",
    "is this possible", "can this be done",
]


class MissingInformationDetector:
    """
    Strict 8-step sequential questionnaire.

    Order:
      1. destination
      2. travelers
      3. duration
      4. budget
      5. origin
      6. transit  (only for city-to-city / domestic trips)
      7. accommodation
      8. interests

    start_date is OPTIONAL — extracted if the user provides it,
    but NEVER asked as a required question.

    The full itinerary is only generated after ALL steps are complete
    AND the user clicks the CTA button.
    """

    # Strict order — start_date is NOT in here
    REQUIRED_FIELDS = {
        "destination":    1,
        "travelers":      2,
        "traveler_type":  3,
        "duration":       4,
        "budget":         5,
        "origin":         6,
        "transit":        7,
        "accommodation":  8,
        "interests":      9,
    }

    @staticmethod
    def _is_domestic(state: TravelState) -> bool:
        """Return True when origin and destination resolve to the same country."""
        if not state.origin or not (state.destinations or state.cities):
            return False
        dest_name = (
            state.destinations[0] if state.destinations else state.cities[0]
        )
        return _is_domestic_trip(state.origin, dest_name)

    @staticmethod
    def detect(state: TravelState) -> list[str]:
        """
        Return list of missing required fields, sorted by REQUIRED_FIELDS order.
        Only ONE question should be shown at a time (the first in the list).
        """
        missing = []

        # 1. Destination
        if not state.destinations and not state.cities:
            missing.append("destination")

        # 2. Travelers count
        if state.travelers is None:
            missing.append("travelers")

        # 3. Traveler type (solo, couple, family, friends, etc.)
        if not state.traveler_type:
            missing.append("traveler_type")

        # 4. Duration
        if state.duration_days is None:
            missing.append("duration")

        # 5. Budget
        if state.budget is None:
            missing.append("budget")

        # 6. Origin
        if not state.origin:
            missing.append("origin")

        # 7. Transit — only for same-country (city-to-city) trips
        #    International trips skip this entirely
        is_domestic = MissingInformationDetector._is_domestic(state)
        if is_domestic and not state.transportation_preference:
            missing.append("transit")

        # 8. Accommodation
        if not state.accommodation_preference:
            missing.append("accommodation")

        # 9. Interests / Requirements
        if not state.interests:
            missing.append("interests")

        # Sort by required order
        missing.sort(
            key=lambda field: MissingInformationDetector.REQUIRED_FIELDS[field]
        )

        return missing

    @staticmethod
    def is_ready_for_itinerary(state: TravelState) -> bool:
        """
        Return True ONLY when every required questionnaire step is complete.
        This is the hard gate — the CTA button only shows when this is True,
        and the itinerary is never generated until the user clicks the button.
        """
        return len(MissingInformationDetector.detect(state)) == 0

    @staticmethod
    def next_question(state: TravelState) -> str | None:
        """
        Return the next question to ask, or None when all steps complete.
        Questions are designed to be clear, friendly, and option-rich.
        """
        missing = MissingInformationDetector.detect(state)

        if not missing:
            return None

        questions: dict[str, str] = {
            "destination": (
                "🌍 **Where would you like to travel?**\n\n"
                "Tell me the city, country, or region you have in mind!"
            ),
            "travelers": (
                "👥 **How many people will be traveling?**\n\n"
                "*(e.g. just me, 2 adults, family of 4)*"
            ),
            "traveler_type": (
                "🎟️ **What best describes your travel group?**\n\n"
                "• 🧔 **Solo** — travelling alone\n"
                "• 👫 **Couple** — romantic getaway\n"
                "• 👨‍👩‍👧‍👦 **Family** — with kids or elderly\n"
                "• 👯 **Friends** — group trip\n"
                "• 💼 **Business** — work or conference travel\n\n"
                "*(Type your answer or pick one above!)*"
            ),
            "duration": (
                "⏳ **How many days are you planning for this trip?**\n\n"
                "*(e.g. 5 days, a week, 10 nights)*"
            ),
            "budget": (
                "💰 **What's your total budget for this trip?**\n\n"
                "Please mention the amount and currency — e.g. *₹80,000*, *$2,000*, *€1,500*"
            ),
            "origin": (
                "🛫 **Where will you be departing from?**\n\n"
                "*(e.g. Delhi, Mumbai, New York, London)*"
            ),
            "transit": (
                "🚆 **How would you like to get there?**\n\n"
                "Since this is a domestic trip, I can help with either:\n\n"
                "• ✈️ **Flight** — faster, good if time is short or distance is long\n"
                "• 🚆 **Train / Express Bus** — scenic, budget-friendly, comfortable\n\n"
                "Which do you prefer?"
            ),
            "accommodation": (
                "🏨 **What type of accommodation do you prefer?**\n\n"
                "• 🛏️ **Budget / Hostels** — shared dorms, guesthouses, cheapest option\n"
                "• 🏩 **Mid-Range Hotels** — comfortable 3–4 star, great value\n"
                "• 🌟 **Luxury Resorts** — 5-star, spa, premium amenities\n\n"
                "*(Or describe what you’re looking for!)*"
            ),
            "interests": (
                "🗺️ **What kinds of experiences excite you most?**\n\n"
                "• 🧗 **Adventure** — hiking, rafting, trekking, extreme sports\n"
                "• 🏛️ **Culture** — temples, museums, heritage, local life\n"
                "• 🍜 **Food & Dining** — street food, fine dining, cooking classes\n"
                "• 🏖️ **Beach & Relaxation** — sun, sea, wellness, slow travel\n"
                "• 🎶 **Nightlife** — bars, clubs, live music, entertainment\n\n"
                "*(Pick one or more, or describe in your own words!)*"
            ),
        }

        return questions[missing[0]]

    @staticmethod
    def is_budget_feasibility_check(user_message: str) -> bool:
        """
        Return True when the user is asking mid-flow whether a specific
        feature (luxury hotel, business class, etc.) fits their budget.
        """
        msg = user_message.lower().strip()
        return any(trigger in msg for trigger in _FEASIBILITY_TRIGGERS)

    @staticmethod
    def is_informational_or_place_query(user_message: str) -> bool:
        msg_lower = user_message.lower().strip()

        # If user is providing multi-parameter trip requirements or asking to build trip, it is NOT an info query
        planning_signals = [
            "want to go", "want to visit", "planning to", "plan a trip", "plan my",
            "build my", "create itinerary", "build itinerary", "full itinerary",
            "depart from", "departing from", "budget is", "budget of", "budget for",
            "trip to", "travel to", "going to", "build my full itinerary now"
        ]
        if any(sig in msg_lower for sig in planning_signals):
            return False

        if any(w in msg_lower for w in ["day", "days", "night", "nights"]) and any(w in msg_lower for w in ["budget", "inr", "usd", "eur", "gbp", "₹", "$", "€"]):
            return False

        info_keywords = [
            "tell me about", "tell me more about", "tell me more", "what is", "what are", "where is", "where are",
            "details about", "info on", "information about", "how is", "how are", "how do",
            "show me", "explain", "ask travelos about", "history of", "famous for", "guide for",
            "safety", "saftey", "safe", "danger", "scam", "emergency", "police",
            "regulation", "regulations", "rule", "rules", "law", "laws",
            "visa", "visas", "entry requirement", "entry requirements", "passport",
            "culture", "custom", "customs", "etiquette", "packing", "what to pack",
            "is it safe", "can i visit", "best time to visit", "things to know",
        ]

        if any(kw in msg_lower for kw in info_keywords):
            return True

        return False

    @staticmethod
    def fill_missing_from_context(
        state: TravelState,
        user_message: str,
        extraction,
        current_field: str | None = None,
    ) -> TravelState:
        """
        If a specific questionnaire question was asked and LLM extraction didn't populate it
        (or misclassified origin as destination), use the question context to set the field accurately.
        """
        if current_field is None:
            missing = MissingInformationDetector.detect(state)
            if not missing:
                return state
            current_field = missing[0]

        msg = user_message.strip()
        msg_lower = msg.lower()

        # 1. Destination
        if current_field == "destination":
            if not state.destinations and not state.cities:
                if extraction.destinations:
                    state.destinations = list(extraction.destinations)
                elif extraction.origin:
                    state.destinations = [extraction.origin]
                else:
                    clean_dest = msg.replace("to ", "").replace("visiting ", "").replace("i want to go to ", "").strip()
                    if clean_dest and not clean_dest.isdigit() and len(clean_dest) > 1:
                        state.destinations = [clean_dest.title()]

        # 2. Travelers count
        elif current_field == "travelers":
            if state.travelers is None:
                if extraction.travelers is not None:
                    state.travelers = extraction.travelers
                else:
                    import re
                    # Look for number specifically associated with people / travelers or standalone digits
                    # Reject numbers followed by days/nights/weeks/months/years/dollars/rupees
                    digit_match = re.search(r'\b(\d+)\s*(?:people|person|adult|adults|traveler|travelers|passengers|pax)?\b', msg_lower)
                    unit_check = re.search(r'\b\d+\s*(?:day|night|week|month|year|usd|inr|dollar|euro|pound|rs|₹|\$|€|£)', msg_lower)
                    if any(w in msg_lower for w in ["just me", "solo", "myself", "alone", "1 adult", "single", "me alone"]):
                        state.travelers = 1
                    elif any(w in msg_lower for w in ["couple", "two", "2 adults", "me and my wife", "me and my husband", "me and my partner"]):
                        state.travelers = 2
                    elif digit_match and not unit_check:
                        state.travelers = int(digit_match.group(1))

        # 3. Traveler type
        elif current_field == "traveler_type":
            if not state.traveler_type:
                if extraction.traveler_type:
                    state.traveler_type = extraction.traveler_type
                elif "solo" in msg_lower or "alone" in msg_lower:
                    state.traveler_type = "Solo"
                elif any(w in msg_lower for w in ["couple", "romantic", "partner", "husband", "wife"]):
                    state.traveler_type = "Couple"
                elif any(w in msg_lower for w in ["family", "kids", "child", "children", "elderly"]):
                    state.traveler_type = "Family"
                elif any(w in msg_lower for w in ["friend", "friends", "group"]):
                    state.traveler_type = "Friends"
                elif any(w in msg_lower for w in ["business", "work", "conference"]):
                    state.traveler_type = "Business"
                else:
                    state.traveler_type = msg.title()

        # 4. Duration
        elif current_field == "duration":
            if state.duration_days is None:
                if extraction.duration_days is not None:
                    state.duration_days = extraction.duration_days
                else:
                    import re
                    match = re.search(r'(\d+)\s*(?:day|night|d|n)', msg_lower)
                    if match:
                        state.duration_days = int(match.group(1))
                    elif "week" in msg_lower:
                        state.duration_days = 7
                    else:
                        digits = re.findall(r'\b\d+\b', msg_lower)
                        if digits:
                            state.duration_days = int(digits[0])

        # 5. Budget
        elif current_field == "budget":
            if state.budget is None:
                if extraction.budget is not None:
                    state.budget = extraction.budget
                if extraction.currency is not None:
                    state.currency = extraction.currency
                import re
                if state.budget is None:
                    digits = re.findall(r'[\d,]+', msg)
                    for d in digits:
                        clean_num = d.replace(",", "")
                        if clean_num.isdigit() and int(clean_num) > 10:
                            state.budget = float(clean_num)
                            break
                if not state.currency:
                    if any(c in msg_lower for c in ["₹", "inr", "rupee", "rupees", "rs"]):
                        state.currency = "INR"
                    elif any(c in msg_lower for c in ["$", "usd", "dollar", "dollars"]):
                        state.currency = "USD"
                    elif any(c in msg_lower for c in ["€", "eur", "euro", "euros"]):
                        state.currency = "EUR"
                    elif any(c in msg_lower for c in ["£", "gbp", "pound", "pounds"]):
                        state.currency = "GBP"
                    elif any(c in msg_lower for c in ["¥", "jpy", "yen"]):
                        state.currency = "JPY"

        # 6. Origin
        elif current_field == "origin":
            if not state.origin:
                if extraction.origin:
                    state.origin = extraction.origin
                elif extraction.destinations and state.destinations:
                    # LLM misextracted origin as destination (e.g. user said "Mumbai")
                    # Use the first extracted destination as the origin candidate
                    cand = extraction.destinations[0]
                    state.origin = cand
                    # Remove it from destinations if it was erroneously added
                    if cand in state.destinations and len(state.destinations) > 1:
                        state.destinations.remove(cand)
                else:
                    # Fallback: strip common departure prefixes and use the rest as origin
                    import re as _re
                    _ORIGIN_PATTERNS = [
                        r"(?:i(?:'m| am| will be| am going to be) (?:departing|leaving|travelling|traveling|flying|starting) from )([\w\s]+)",
                        r"(?:i(?:'ll| will) (?:depart|leave|fly|travel|start)(?: from| my journey from)? )([\w\s]+)",
                        r"(?:my (?:departure|starting point|origin|base|home city) is )([\w\s]+)",
                        r"(?:departing from |departure from |leaving from |from |travelling from |traveling from |starting from |starting at )([\w\s]+)",
                    ]
                    extracted_city = None
                    for pattern in _ORIGIN_PATTERNS:
                        m = _re.search(pattern, msg_lower)
                        if m:
                            extracted_city = m.group(1).strip().title()
                            break

                    if not extracted_city:
                        # Plain answer (just a city name or short phrase)
                        clean_orig = (
                            msg
                            .replace("from ", "")
                            .replace("departing from ", "")
                            .replace("departure from ", "")
                            .replace("leaving from ", "")
                            .replace("travelling from ", "")
                            .replace("traveling from ", "")
                            .replace("I am ", "")
                            .replace("i am ", "")
                            .replace("my city is ", "")
                            .replace("my home is ", "")
                            .strip()
                        )
                        extracted_city = clean_orig.title() if clean_orig else None

                    if extracted_city and len(extracted_city) >= 2:
                        state.origin = extracted_city

        # 7. Transit
        elif current_field == "transit":
            if not state.transportation_preference:
                if extraction.transportation_preference:
                    state.transportation_preference = extraction.transportation_preference
                elif any(w in msg_lower for w in ["flight", "plane", "air", "fly"]):
                    state.transportation_preference = "Flight"
                elif any(w in msg_lower for w in ["train", "rail", "express"]):
                    state.transportation_preference = "Train"
                elif any(w in msg_lower for w in ["bus", "coach"]):
                    state.transportation_preference = "Bus"

        # 8. Accommodation
        elif current_field == "accommodation":
            if not state.accommodation_preference:
                if extraction.accommodation_preference:
                    state.accommodation_preference = extraction.accommodation_preference
                elif any(w in msg_lower for w in ["luxury", "5 star", "resort", "premium", "5-star"]):
                    state.accommodation_preference = "Luxury Resorts"
                elif any(w in msg_lower for w in ["mid", "3 star", "4 star", "hotel", "comfortable", "3-star", "4-star"]):
                    state.accommodation_preference = "Mid-Range Hotels"
                elif any(w in msg_lower for w in ["budget", "hostel", "dorm", "guesthouse", "cheap"]):
                    state.accommodation_preference = "Budget / Hostels"

        # 9. Interests
        elif current_field == "interests":
            if not state.interests:
                if extraction.interests:
                    state.interests = extraction.interests
                else:
                    found = []
                    if any(w in msg_lower for w in ["adventure", "hiking", "trekking", "rafting"]):
                        found.append("Adventure")
                    if any(w in msg_lower for w in ["culture", "temple", "museum", "heritage", "history"]):
                        found.append("Culture")
                    if any(w in msg_lower for w in ["food", "dining", "cuisine", "restaurant", "eating"]):
                        found.append("Food & Dining")
                    if any(w in msg_lower for w in ["beach", "sea", "sun", "relax", "relaxation", "wellness"]):
                        found.append("Beach & Relaxation")
                    if any(w in msg_lower for w in ["nightlife", "bar", "club", "party"]):
                        found.append("Nightlife")
                    if found:
                        state.interests = found
                    else:
                        state.interests = [msg.title()]

        return state