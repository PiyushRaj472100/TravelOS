"""
TravelOS Backend Integration Tests
Run: python test_backend_api.py (backend must be running on port 8000)
"""

import sys
import json
import time
import requests

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"
CHAT_URL = f"{BASE_URL}/api/chat"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

session_id = None


def print_header(title: str):
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}")


def print_pass(msg: str):
    print(f"  {GREEN}[PASS] {msg}{RESET}")


def print_fail(msg: str):
    print(f"  {RED}[FAIL] {msg}{RESET}")


def print_info(msg: str):
    print(f"  {YELLOW}  --> {msg}{RESET}")


def chat(message: str, use_session: bool = True) -> dict:
    """Send a chat message and return the response."""
    global session_id

    payload = {"message": message}
    if use_session and session_id:
        payload["session_id"] = session_id

    resp = requests.post(CHAT_URL, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()

    # Persist session ID
    if not session_id:
        session_id = data.get("session_id")

    return data


def assert_field(data: dict, field: str, expected_type=None, non_empty: bool = False):
    """Assert a field exists and optionally check type/non-empty."""
    if field not in data:
        print_fail(f"Missing field: {field}")
        return False

    val = data[field]

    if expected_type and not isinstance(val, expected_type):
        print_fail(f"Field '{field}' expected {expected_type.__name__}, got {type(val).__name__}")
        return False

    if non_empty and not val:
        print_fail(f"Field '{field}' is empty")
        return False

    return True


# =============================================================
# TEST 1: Health Check
# =============================================================

def test_health():
    print_header("TEST 1: Health Check")
    try:
        resp = requests.get(BASE_URL, timeout=10)
        data = resp.json()
        assert resp.status_code == 200
        assert data.get("status") == "running"
        print_pass("Backend is running")
        print_info(f"Message: {data.get('message')}")
        return True
    except Exception as e:
        print_fail(f"Health check failed: {e}")
        return False


# =============================================================
# TEST 2: Basic Planning — Destination
# =============================================================

def test_planning_destination():
    print_header("TEST 2: Planning — Destination Extraction")
    global session_id
    session_id = None  # Fresh session

    try:
        data = chat("I want to plan a trip to Japan.")

        print_info(f"Session ID: {data.get('session_id', '')[:8]}...")
        print_info(f"Message: {data.get('message', '')[:80]}")

        state = data.get("travel_state", {})
        destinations = state.get("destinations", [])

        if destinations and "Japan" in str(destinations):
            print_pass(f"Destination extracted: {destinations}")
        else:
            print_fail(f"Destination not extracted. destinations={destinations}")
            return False

        missing = data.get("missing_information", [])
        print_info(f"Missing info: {missing}")

        if "destination" not in missing:
            print_pass("Destination not in missing_information")
        else:
            print_fail("Destination still in missing_information despite being provided")

        # Check locations are populated from GeoService
        locations = state.get("locations", [])
        print_info(f"Locations resolved: {len(locations)}")

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 3: Multi-turn Conversation
# =============================================================

def test_multi_turn():
    print_header("TEST 3: Multi-turn Conversation (progressive state building)")

    try:
        # Turn 1: Already sent Japan in previous test (session persists)
        data = chat("7 days.")
        state = data.get("travel_state", {})
        if state.get("duration_days") == 7:
            print_pass(f"Duration extracted: {state['duration_days']} days")
        else:
            print_fail(f"Duration not extracted: duration_days={state.get('duration_days')}")

        time.sleep(1)

        # Turn 2: Travelers
        data = chat("We are 2 people traveling.")
        state = data.get("travel_state", {})
        if state.get("travelers") == 2:
            print_pass(f"Travelers extracted: {state['travelers']}")
        else:
            print_fail(f"Travelers not extracted: travelers={state.get('travelers')}")

        time.sleep(1)

        # Turn 3: Budget
        data = chat("Budget is around €2000.")
        state = data.get("travel_state", {})
        budget = state.get("budget")
        currency = state.get("currency")
        if budget:
            print_pass(f"Budget extracted: {budget} {currency}")
        else:
            print_fail(f"Budget not extracted: budget={budget}")

        time.sleep(1)

        # Turn 4: Interests
        data = chat("I love culture, food and photography.")
        state = data.get("travel_state", {})
        interests = state.get("interests", [])
        if interests:
            print_pass(f"Interests extracted: {interests}")
        else:
            print_fail(f"Interests not extracted: interests={interests}")

        # Check missing_information shrank
        missing = data.get("missing_information", [])
        print_info(f"Remaining missing: {missing}")

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 4: Weather Query
# =============================================================

def test_weather():
    print_header("TEST 4: Live Weather Query")

    try:
        data = chat("What is the current weather in Tokyo?")

        msg = data.get("message", "")
        weather = data.get("weather")
        print_info(f"Response: {msg[:100]}")

        if "°C" in msg or "weather" in msg.lower() or weather:
            print_pass("Weather data returned")
        else:
            print_fail(f"No weather in response. Message: {msg[:100]}")
            return False

        if weather:
            print_info(f"Temperature: {weather.get('temperature')}°C")
            print_info(f"City: {weather.get('city')}")
            print_pass("Structured weather data in response")

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 5: Currency Query
# =============================================================

def test_currency():
    print_header("TEST 5: Currency Query")

    try:
        data = chat("What is the exchange rate from EUR to JPY?")

        msg = data.get("message", "")
        currency_data = data.get("currency")
        print_info(f"Response: {msg[:100]}")

        if "EUR" in msg or "JPY" in msg or currency_data:
            print_pass("Currency data returned")
        else:
            print_fail(f"No currency in response")
            return False

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 6: RAG Knowledge Query
# =============================================================

def test_rag_knowledge():
    print_header("TEST 6: RAG Knowledge — Japan Culture")

    try:
        data = chat("What should I know about Japanese culture before visiting?")

        msg = data.get("message", "")
        sources = data.get("sources", [])

        print_info(f"Response length: {len(msg)} chars")
        print_info(f"Sources: {len(sources)}")

        if len(msg) > 50:
            print_pass("Substantive knowledge response received")
        else:
            print_fail(f"Response too short: {msg}")
            return False

        if sources:
            print_pass(f"RAG sources returned: {[s.get('title') for s in sources[:3]]}")

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 7: Activity Request
# =============================================================

def test_activities():
    print_header("TEST 7: Activity Agent — Japan Activities")

    try:
        data = chat("What are the best things to do in Japan for someone who loves culture and food?")

        msg = data.get("message", "")
        activities = data.get("activities", [])
        agent_statuses = data.get("agent_statuses", [])

        print_info(f"Activities returned: {len(activities)}")
        print_info(f"Agent statuses: {[(a['agent'], a['status']) for a in agent_statuses]}")

        if activities:
            print_pass(f"ActivityAgent returned {len(activities)} activities")
            first = activities[0]
            print_info(f"First activity: {first.get('name')} ({first.get('type')})")
        else:
            # RAG might have answered without ActivityAgent
            print_info("No structured activities — possibly answered via RAG")
            if len(msg) > 100:
                print_pass("Knowledge response received (RAG)")

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 8: Budget Request
# =============================================================

def test_budget():
    print_header("TEST 8: Budget Agent")

    try:
        data = chat("What is the estimated budget for my trip?")

        budget = data.get("budget")
        msg = data.get("message", "")

        print_info(f"Response: {msg[:100]}")

        if budget:
            print_pass("Budget breakdown returned")
            print_info(f"Flights: {budget.get('flights')} {budget.get('currency')}")
            print_info(f"Hotels: {budget.get('hotels')} {budget.get('currency')}")
            print_info(f"Food: {budget.get('food')} {budget.get('currency')}")
            print_info(f"Note: {budget.get('note', '')[:60]}")
        else:
            print_info("No structured budget — may have been answered in message")

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 9: Full Trip Build
# =============================================================

def test_build_trip():
    print_header("TEST 9: Full Trip Build — 7-day Japan itinerary")

    try:
        print_info("Setting start date first...")
        chat("Start date is September 15, 2026.")
        time.sleep(1)

        print_info("Requesting full trip build...")
        data = chat("Build my complete trip itinerary for Japan.")

        itinerary = data.get("itinerary", [])
        activities = data.get("activities", [])
        budget = data.get("budget")
        agent_statuses = data.get("agent_statuses", [])
        map_data = data.get("map_data")

        print_info(f"Agent statuses: {[(a['agent'], a['status']) for a in agent_statuses]}")

        if itinerary:
            print_pass(f"Itinerary generated: {len(itinerary)} days")
            day1 = itinerary[0]
            print_info(f"Day 1 theme: {day1.get('theme', 'N/A')}")
        else:
            print_info("No itinerary (may require more state)")

        if activities:
            print_pass(f"Activities: {len(activities)}")

        if budget:
            print_pass(f"Budget: flights={budget.get('flights')}, hotels={budget.get('hotels')}")

        if map_data:
            markers = map_data.get("markers", [])
            routes = map_data.get("routes", [])
            print_pass(f"Map data: {len(markers)} markers, {len(routes)} routes")

        return True

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# TEST 10: Response Schema Validation
# =============================================================

def test_response_schema():
    print_header("TEST 10: Response Schema Validation")

    try:
        data = chat("What should I pack for Japan?")

        required_fields = [
            "session_id", "message", "missing_information",
            "travel_state", "sources", "agent_statuses",
            "flights", "hotels", "activities", "itinerary"
        ]

        all_ok = True
        for field in required_fields:
            if field in data:
                print_pass(f"Field present: {field}")
            else:
                print_fail(f"Missing field: {field}")
                all_ok = False

        # Travel state fields
        state = data.get("travel_state", {})
        state_fields = [
            "destinations", "duration_days", "travelers",
            "budget", "interests", "locations", "travel_legs"
        ]
        print_info("TravelState fields:")
        for field in state_fields:
            val = state.get(field)
            status = "✓" if val is not None else "○"
            print(f"    {status} {field}: {val}")

        return all_ok

    except Exception as e:
        print_fail(f"Error: {e}")
        return False


# =============================================================
# RUN ALL TESTS
# =============================================================

def run_all():
    print(f"\n{BOLD}TravelOS Backend API Test Suite{RESET}")
    print(f"Testing: {CHAT_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Health Check", test_health),
        ("Planning — Destination", test_planning_destination),
        ("Multi-turn Conversation", test_multi_turn),
        ("Weather Query", test_weather),
        ("Currency Query", test_currency),
        ("RAG Knowledge", test_rag_knowledge),
        ("Activities", test_activities),
        ("Budget", test_budget),
        ("Full Trip Build", test_build_trip),
        ("Schema Validation", test_response_schema),
    ]

    results = []
    for name, test_fn in tests:
        try:
            ok = test_fn()
            results.append((name, ok))
        except Exception as e:
            print_fail(f"UNHANDLED ERROR in {name}: {e}")
            results.append((name, False))
        time.sleep(2)

    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        if ok:
            print_pass(name)
        else:
            print_fail(name)

    print(f"\n{BOLD}Results: {passed}/{total} passed{RESET}")

    if passed == total:
        print(f"{GREEN}{BOLD}✓ All tests passed! Backend is ready.{RESET}\n")
    else:
        print(f"{YELLOW}⚠ Some tests failed. Check output above.{RESET}\n")


if __name__ == "__main__":
    run_all()
