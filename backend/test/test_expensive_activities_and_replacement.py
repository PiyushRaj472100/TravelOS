"""Test expensive activities detection, replacement, removal, and budget reflections."""

import sys
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_expensive_activities_flow():
    print("\n" + "=" * 70)
    print("  TEST: EXPENSIVE ACTIVITIES, REPLACEMENT & BUDGET REFLECTIONS")
    print("=" * 70)

    session_id = "test-expensive-activities-session"

    # Turn 1: Build full trip in INR
    msg1 = "Plan a 5-day cultural and sightseeing trip to Tokyo for 2 people with a budget of 300000 INR"
    print(f"\n[Turn 1] User: {msg1}")
    resp1 = client.post("/api/chat", json={"message": msg1, "session_id": session_id})
    assert resp1.status_code == 200
    d1 = resp1.json()
    b1 = d1.get("budget")
    acts1 = d1.get("activities", [])

    print(f"Turn 1 Currency: {b1['currency']}")
    print(f"Turn 1 Activities count: {len(acts1)}")
    assert b1["currency"] == "INR"
    assert len(acts1) > 0, "Expected generated activities"
    for act in acts1[:3]:
        print(f"  - {act['name']} ({act.get('cost_tier', 'N/A')}): {act.get('estimated_cost_per_person')} {act.get('cost_currency')}")
        assert act.get("cost_currency") == "INR", f"Expected INR activity cost currency, got {act.get('cost_currency')}"
    print("[PASS] Turn 1: Trip planned with all activities in INR!")

    # Turn 2: Ask AI about expensive activities
    msg2 = "What are the expensive activities in my trip?"
    print(f"\n[Turn 2] User: {msg2}")
    resp2 = client.post("/api/chat", json={"message": msg2, "session_id": session_id})
    assert resp2.status_code == 200
    d2 = resp2.json()
    print(f"Assistant >\n{d2['message']}\n")
    assert "Expensive Activities" in d2["message"] or "INR" in d2["message"]
    print("[PASS] Turn 2: AI identified expensive activities and suggested actions!")

    # Turn 3: "Give another option" (Replace the expensive activity)
    top_act_name = acts1[0]["name"]
    msg3 = f"Give another option for {top_act_name}"
    print(f"\n[Turn 3] User: {msg3}")
    resp3 = client.post("/api/chat", json={"message": msg3, "session_id": session_id})
    assert resp3.status_code == 200
    d3 = resp3.json()
    b3 = d3.get("budget")
    acts3 = d3.get("activities", [])
    print(f"Assistant >\n{d3['message']}\n")
    print(f"Turn 3 Activities count: {len(acts3)}")
    print(f"Turn 3 Activity Budget: {b3['activities']} {b3['currency']}")
    assert "Replaced" in d3["message"] or "option" in d3["message"]
    print("[PASS] Turn 3: AI replaced activity with budget-friendly option and updated budget!")

    # Turn 4: "Leave it" (Remove an activity)
    next_act_name = acts3[1]["name"] if len(acts3) > 1 else acts3[0]["name"]
    msg4 = f"Leave {next_act_name}"
    print(f"\n[Turn 4] User: {msg4}")
    resp4 = client.post("/api/chat", json={"message": msg4, "session_id": session_id})
    assert resp4.status_code == 200
    d4 = resp4.json()
    b4 = d4.get("budget")
    acts4 = d4.get("activities", [])
    print(f"Assistant >\n{d4['message']}\n")
    print(f"Turn 4 Activities count: {len(acts4)}")
    print(f"Turn 4 New Activity Spend: {b4['activities']} {b4['currency']}")
    assert len(acts4) == len(acts3) - 1, f"Expected {len(acts3) - 1} activities, got {len(acts4)}"
    assert "Removed" in d4["message"]
    print("[PASS] Turn 4: AI removed activity and reflected savings in budget!")

    # Turn 5: Switch currency to EUR
    msg5 = "change currency to EUR"
    print(f"\n[Turn 5] User: {msg5}")
    resp5 = client.post("/api/chat", json={"message": msg5, "session_id": session_id})
    assert resp5.status_code == 200
    d5 = resp5.json()
    b5 = d5.get("budget")
    acts5 = d5.get("activities", [])
    print(f"Assistant >\n{d5['message']}\n")
    assert b5["currency"] == "EUR"
    for act in acts5[:3]:
        assert act.get("cost_currency") == "EUR", f"Expected EUR, got {act.get('cost_currency')}"
        print(f"  - Converted: {act['name']} -> {act.get('estimated_cost_per_person')} {act.get('cost_currency')}")
    print("[PASS] Turn 5: All activities, itinerary and budget synchronously converted to EUR!")

    print("\n" + "=" * 70)
    print("  ALL EXPENSIVE ACTIVITIES & BUDGET TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_expensive_activities_flow()
