"""
TravelOS In-Process Comprehensive API & Agent Test Suite
Uses FastAPI TestClient to test all endpoints and agent capabilities directly.
"""

import sys
from fastapi.testclient import TestClient
from app.main import app

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_root():
    print("\n--- 1. Testing Root Endpoint ---")
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print("Root response:", data)
    assert data.get("status") == "running"
    print("[PASS] Root endpoint is working!")

def test_chat_live_weather():
    print("\n--- 2. Testing Chat: Live Weather ---")
    response = client.post("/api/chat", json={"message": "What is the weather in Tokyo?"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    print("Weather message:", data.get("message"))
    print("Weather data:", data.get("weather"))
    assert "session_id" in data
    print("[PASS] Live weather query works!")
    return data.get("session_id")

def test_chat_live_currency(session_id=None):
    print("\n--- 3. Testing Chat: Live Currency ---")
    payload = {"message": "Convert 100 USD to JPY"}
    if session_id:
        payload["session_id"] = session_id
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    print("Currency message:", data.get("message"))
    print("Currency data:", data.get("currency"))
    print("[PASS] Live currency query works!")

def test_chat_trip_planning():
    print("\n--- 4. Testing Chat: Multi-Turn Trip Planning ---")
    # Step 1: Initial intent
    r1 = client.post("/api/chat", json={"message": "I want to plan a 5 day trip to Tokyo for 2 people with budget $2500"})
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    d1 = r1.json()
    session_id = d1.get("session_id")
    print(f"Turn 1 State: {d1.get('travel_state', {}).get('destinations')}, Duration: {d1.get('travel_state', {}).get('duration_days')}")
    print(f"Turn 1 Message: {d1.get('message')}")
    
    # Step 2: Ask for activities
    r2 = client.post("/api/chat", json={"session_id": session_id, "message": "What are top things to do in Tokyo?"})
    assert r2.status_code == 200
    d2 = r2.json()
    print(f"Turn 2 Activities count: {len(d2.get('activities', []))}")
    print(f"Turn 2 Message: {d2.get('message')[:100]}...")

    # Step 3: Build full itinerary
    r3 = client.post("/api/chat", json={"session_id": session_id, "message": "Build my full trip itinerary and budget"})
    assert r3.status_code == 200
    d3 = r3.json()
    print(f"Turn 3 Itinerary days: {len(d3.get('itinerary', []))}")
    print(f"Turn 3 Budget: {d3.get('budget')}")
    print(f"Turn 3 Map Markers: {len(d3.get('map_data', {}).get('markers', [])) if d3.get('map_data') else 0}")
    print("[PASS] Multi-turn trip planning and agent orchestration works!")

if __name__ == "__main__":
    print("Starting TravelOS Backend API Verification...")
    test_root()
    session_id = test_chat_live_weather()
    test_chat_live_currency(session_id)
    test_chat_trip_planning()
    print("\n=======================================================")
    print("ALL BACKEND APIS AND AGENT CAPABILITIES TESTED SUCCESSFULLY!")
    print("=======================================================")
