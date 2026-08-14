import requests
import httpx
import json
import sys
import io

# Ensure UTF-8 output on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("==================================================")
print("TravelOS -- Comprehensive Verification Suite")
print("==================================================")

# 1. Test Live APIs
print("\n--- 1. Testing Live APIs ---")

# Weather API (Open-Meteo)
try:
    geo_res = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": "London", "count": 1, "language": "en", "format": "json"},
        timeout=10
    )
    geo_res.raise_for_status()
    loc = geo_res.json()["results"][0]
    wx_res = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
            "timezone": "auto"
        },
        timeout=10
    )
    wx_res.raise_for_status()
    cur = wx_res.json()["current"]
    print(f"✅ Weather API: London -> {cur['temperature_2m']}°C, Humidity {cur['relative_humidity_2m']}%")
except Exception as e:
    print(f"❌ Weather API failed: {e}")

# Currency API (FX Provider)
try:
    fx_res = httpx.get("https://fxapi.app/api/USD/INR.json", timeout=15, follow_redirects=True)
    fx_res.raise_for_status()
    data = fx_res.json()
    rate = data.get("rate")
    print(f"✅ FX / Currency API: 1 USD = {rate} INR")
except Exception as e:
    print(f"❌ FX API failed: {e}")

# Gemini LLM API
try:
    from app.services.llm_service import LLMService
    llm = LLMService()
    resp = llm.generate_response("Respond with: TRAVELOS_ONLINE")
    print(f"✅ Gemini LLM Service: {resp.strip()}")
except Exception as e:
    print(f"❌ Gemini LLM failed: {e}")

# 2. Test Conversation Extraction Logic
print("\n--- 2. Testing Natural Language & Context-Aware Extractions ---")

from app.models.travel_state import TravelState
from app.services.state_manager import StateManager
from app.services.missing_information import MissingInformationDetector

# Test 2.1: Departure handling when AI asked origin question
departure_inputs = [
    "Mumbai",
    "I will depart from Mumbai",
    "I'm leaving from Mumbai",
    "My departure is Mumbai",
    "I am travelling from Mumbai",
    "I'll start my journey from Mumbai",
]

print("\nTesting Departure Handling (User answering departure question):")
for inp in departure_inputs:
    # State has destination set, asking for origin
    state = TravelState(destinations=["London"], duration_days=5, travelers=2, traveler_type="Couple", budget=2000.0, currency="USD")
    missing_before = MissingInformationDetector.detect(state)
    current_field = missing_before[0] if missing_before else None
    
    ext = llm.extract_travel_information(
        user_message=inp,
        current_field=current_field,
        conversation_context="Where will you be departing from?"
    )
    state = StateManager.update_state(state, ext)
    state = MissingInformationDetector.fill_missing_from_context(state, inp, ext)
    
    status = "✅ PASS" if state.origin and "mumbai" in state.origin.lower() else "❌ FAIL"
    print(f"  [{status}] Input: \"{inp}\" -> origin = {state.origin} (destinations = {state.destinations})")

# Test 2.2: Destination + Duration + Travel Date in one message
print("\nTesting Multi-Field Extraction:")
multi_inputs = [
    ("I want to go to London next week for 4 days.", "London", 4),
    ("I want to visit Paris for 7 days next month.", "Paris", 7),
    ("I'm from Delhi, going to Paris next month for 7 days.", "Paris", 7),
]

for inp, expected_dest, expected_days in multi_inputs:
    ext = llm.extract_travel_information(user_message=inp)
    has_dest = any(expected_dest.lower() in d.lower() for d in ext.destinations)
    has_dur = ext.duration_days == expected_days
    status = "✅ PASS" if (has_dest and has_dur) else "❌ FAIL"
    print(f"  [{status}] Input: \"{inp}\"")
    print(f"          -> destinations: {ext.destinations}, duration_days: {ext.duration_days}, start_date: {ext.start_date}, origin: {ext.origin}")

# Test 2.3: Natural short answers
print("\nTesting Natural Short Answers:")
short_tests = [
    ("Where would you like to travel?", "destination", "Tokyo", lambda s: "tokyo" in [d.lower() for d in s.destinations]),
    ("How many people will be traveling?", "travelers", "2 people", lambda s: s.travelers == 2),
    ("How many days are you planning for this trip?", "duration", "4 days", lambda s: s.duration_days == 4),
    ("What's your total budget for this trip?", "budget", "₹80,000", lambda s: s.budget == 80000.0 and s.currency == "INR"),
    ("Where will you be departing from?", "origin", "Mumbai", lambda s: s.origin and "mumbai" in s.origin.lower()),
]

for q_text, field, user_ans, validator in short_tests:
    state = TravelState()
    ext = llm.extract_travel_information(
        user_message=user_ans,
        current_field=field,
        conversation_context=q_text
    )
    state = StateManager.update_state(state, ext)
    state = MissingInformationDetector.fill_missing_from_context(state, user_ans, ext)
    status = "✅ PASS" if validator(state) else "❌ FAIL"
    print(f"  [{status}] Question ({field}): \"{q_text}\" | Answer: \"{user_ans}\" -> State updated: {state.model_dump(exclude_unset=True)}")

# 3. Test Full Chat Endpoint via FastAPI TestClient
print("\n--- 3. Testing Chat Endpoint via FastAPI TestClient ---")
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Session flow test:
# 1. Ask "Plan a trip to London"
res1 = client.post("/api/chat", json={"message": "I want to go to London for 5 days next month"})
data1 = res1.json()
session_id = data1["session_id"]
print(f"\nStep 1 Response (Session {session_id[:8]}...):")
print(f"AI: {data1['message']}")
print(f"Missing info: {data1['missing_information']}")

# 2. Answer travelers: "Just me and my wife"
res2 = client.post("/api/chat", json={"session_id": session_id, "message": "Just me and my wife"})
data2 = res2.json()
print(f"\nStep 2 Response:")
print(f"AI: {data2['message']}")
print(f"Missing info: {data2['missing_information']}")

# 3. Answer traveler type: "Couple"
res3 = client.post("/api/chat", json={"session_id": session_id, "message": "Couple"})
data3 = res3.json()
print(f"\nStep 3 Response:")
print(f"AI: {data3['message']}")
print(f"Missing info: {data3['missing_information']}")

# 4. Answer budget: "$3000"
res4 = client.post("/api/chat", json={"session_id": session_id, "message": "$3000"})
data4 = res4.json()
print(f"\nStep 4 Response:")
print(f"AI: {data4['message']}")
print(f"Missing info: {data4['missing_information']}")

# 5. Answer origin: "Mumbai"
res5 = client.post("/api/chat", json={"session_id": session_id, "message": "Mumbai"})
data5 = res5.json()
print(f"\nStep 5 Response (Departure answered as Mumbai):")
print(f"AI: {data5['message']}")
print(f"TravelState origin: {data5['travel_state'].get('origin')}")
print(f"Missing info: {data5['missing_information']}")

# Verify that Mumbai was saved as origin and did not trigger a city overview of Mumbai
if data5['travel_state'].get('origin') == "Mumbai" and "Here is information about Mumbai" not in data5['message']:
    print("\n🎉 SUCCESS: Mumbai correctly recorded as origin and questionnaire progressed to next step!")
else:
    print("\n❌ Issue in departure handling step.")

print("\n==================================================")
print("Verification Suite Finished.")
print("==================================================")
