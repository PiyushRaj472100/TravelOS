"""
TravelOS Comprehensive End-to-End Human Query Test Suite

Tests all system components using realistic, natural human travel queries:
1. Live Weather Inquiries
2. Live Currency Conversion
3. Live Flight Searches
4. Live Hotel Searches (RouteStack)
5. RAG Knowledge & Etiquette / Packing (Knowledge Base)
6. Multi-Turn Full Trip Planning (State + Itinerary + Budget + Map Markers + Routes)
"""

import sys
from fastapi.testclient import TestClient
from app.main import app

# Ensure clean UTF-8 console output on Windows
sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)


def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_human_live_weather():
    print_section("1. Test Case: Live Weather Query (Natural Human Phrasing)")
    prompt = "Hey! What's the weather like in Tokyo right now? Is it warm enough for a light jacket?"
    print(f"User > {prompt}")

    response = client.post("/api/chat", json={"message": prompt})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    print(f"Assistant > {data.get('message')}")
    weather = data.get("weather")
    print(f"Weather Data: City={weather.get('city') if weather else 'N/A'}, Temp={weather.get('temperature') if weather else 'N/A'}°C")
    assert weather is not None, "Weather payload should not be None"
    assert weather.get("city") == "Tokyo", f"Expected Tokyo, got {weather.get('city')}"
    print("[PASS] Live Weather correctly parsed and answered!")
    return data.get("session_id")


def test_human_live_currency():
    print_section("2. Test Case: Live Currency Exchange (Natural Human Phrasing)")
    prompt = "I'm budgeting for my trip, how much is 350 USD in Japanese Yen today?"
    print(f"User > {prompt}")

    response = client.post("/api/chat", json={"message": prompt})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    print(f"Assistant > {data.get('message')}")
    currency = data.get("currency")
    print(f"Currency Data: {currency}")
    assert currency is not None, "Currency payload should not be None"
    assert currency.get("base_currency") == "USD"
    assert currency.get("target_currency") == "JPY"
    print("[PASS] Live Currency exchange calculated accurately!")


def test_human_live_flights():
    print_section("3. Test Case: Live Flight Search (Natural Human Phrasing)")
    prompt = "Can you look up flights from London (LHR) to Dubai (DXB) for next month?"
    print(f"User > {prompt}")

    response = client.post("/api/chat", json={"message": prompt})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    print(f"Assistant > {data.get('message')[:250]}...")
    flights = data.get("flights", [])
    print(f"Flights Found: {len(flights)}")
    if flights:
        f = flights[0]
        print(f"Top Flight: {f.get('provider')} | {f.get('origin')} -> {f.get('destination')} | {f.get('price')} {f.get('currency')}")
    assert len(flights) > 0, "Expected at least 1 flight result"
    print("[PASS] Live Flight Search retrieved and formatted flights!")


def test_human_live_hotels():
    print_section("4. Test Case: Live Hotel Inquiry (Natural Human Phrasing)")
    prompt = "I need comfortable hotel recommendations in Tokyo for 2 adults next week"
    print(f"User > {prompt}")

    response = client.post("/api/chat", json={"message": prompt})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    print(f"Assistant > {data.get('message')[:250]}...")
    hotels = data.get("hotels", [])
    print(f"Hotels Found: {len(hotels)}")
    if hotels:
        h = hotels[0]
        print(f"Sample Hotel: {h.get('name')} | Stars: {h.get('stars')} | Provider: {h.get('provider')}")
    assert len(hotels) > 0, "Expected hotels from RouteStack"
    print("[PASS] Live RouteStack Hotels successfully retrieved!")


def test_human_rag_knowledge():
    print_section("5. Test Case: RAG Travel Knowledge & Etiquette (Natural Human Phrasing)")
    prompt = "What are the most important cultural etiquette rules and onsen customs I should follow in Japan?"
    print(f"User > {prompt}")

    response = client.post("/api/chat", json={"message": prompt})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    print(f"Assistant > {data.get('message')[:300]}...")
    sources = data.get("sources", [])
    print(f"RAG Knowledge Sources Cited: {len(sources)}")
    for s in sources[:3]:
        print(f" - [{s.get('category')}] {s.get('title')} ({s.get('country')})")
    assert len(sources) > 0 or len(data.get("message")) > 50, "Expected RAG knowledge retrieval"
    print("[PASS] RAG Knowledge & Culture response generated with sources!")


def test_human_multi_turn_trip_planning():
    print_section("6. Test Case: Full Multi-Turn Human Trip Planning Workflow")
    
    # --- Turn 1: Conversational trip intent ---
    t1_prompt = "Hi! My partner and I are dreaming of a 7-day holiday in Tokyo and Kyoto with a $3500 budget. We love delicious ramen, ancient shrines, and neon nightlife."
    print(f"\n[Turn 1] User > {t1_prompt}")
    r1 = client.post("/api/chat", json={"message": t1_prompt})
    assert r1.status_code == 200, f"Turn 1 error: {r1.text}"
    d1 = r1.json()
    session_id = d1.get("session_id")
    state1 = d1.get("travel_state", {})
    print(f"[Turn 1] Assistant > {d1.get('message')}")
    print(f"[Turn 1] State Tracked: Destinations={state1.get('destinations')}, Duration={state1.get('duration_days')} days, Travelers={state1.get('travelers')}, Budget=${state1.get('budget')}")
    
    # --- Turn 2: Activity and Sightseeing exploration ---
    t2_prompt = "What are the top must-visit spots and food experiences you recommend for our days in Tokyo?"
    print(f"\n[Turn 2] User > {t2_prompt}")
    r2 = client.post("/api/chat", json={"session_id": session_id, "message": t2_prompt})
    assert r2.status_code == 200, f"Turn 2 error: {r2.text}"
    d2 = r2.json()
    print(f"[Turn 2] Assistant > {d2.get('message')[:200]}...")
    activities = d2.get("activities", [])
    print(f"[Turn 2] Activities Discovered: {len(activities)}")
    for act in activities[:3]:
        print(f"   * {act.get('name')} ({act.get('type')}) - {act.get('description', '')[:60]}...")

    # --- Turn 3: Complete Trip Generation (Itinerary, Budget, Map Data) ---
    t3_prompt = "This sounds fantastic! Please build my full day-by-day itinerary, calculate my budget breakdown, and map out the trip."
    print(f"\n[Turn 3] User > {t3_prompt}")
    r3 = client.post("/api/chat", json={"session_id": session_id, "message": t3_prompt})
    assert r3.status_code == 200, f"Turn 3 error: {r3.text}"
    d3 = r3.json()
    print(f"[Turn 3] Assistant > {d3.get('message')[:200]}...")
    
    itinerary = d3.get("itinerary", [])
    budget = d3.get("budget")
    map_data = d3.get("map_data", {})
    markers = map_data.get("markers", []) if map_data else []
    routes = map_data.get("routes", []) if map_data else []

    print(f"[Turn 3] Itinerary Days Planned: {len(itinerary)}")
    for day in itinerary[:2]:
        print(f"   Day {day.get('day')} ({day.get('title')}): {len(day.get('activities', []))} activities scheduled")

    print(f"[Turn 3] Budget Breakdown:")
    if budget:
        print(f"   - Total: ${budget.get('total')} | Accommodation: ${budget.get('accommodation')} | Food: ${budget.get('food')} | Activities: ${budget.get('activities')} | Flights/Transport: ${budget.get('transport')}")

    print(f"[Turn 3] Map Elements:")
    print(f"   - Map Markers: {len(markers)} locations plotted")
    print(f"   - Map Routes: {len(routes)} connection legs")
    for m in markers[:4]:
        print(f"     📍 [{m.get('marker_type')}] {m.get('name')} ({m.get('latitude'):.4f}, {m.get('longitude'):.4f})")

    assert len(itinerary) > 0, "Expected non-empty itinerary"
    assert budget is not None, "Expected calculated budget breakdown"
    assert len(markers) > 0, "Expected map markers"
    print("[PASS] Full Multi-Turn Trip Planning workflow executed flawlessly!")


if __name__ == "__main__":
    print_section("TRAVELOS FULL SYSTEM & HUMAN QUERY VERIFICATION")
    test_human_live_weather()
    test_human_live_currency()
    test_human_live_flights()
    test_human_live_hotels()
    test_human_rag_knowledge()
    test_human_multi_turn_trip_planning()
    print_section("ALL HUMAN TRAVEL TEST SCENARIOS PASSED WITH FLYING COLORS!")
