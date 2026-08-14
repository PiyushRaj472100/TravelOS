"""Test realistic budgeting and conversational currency switching across TravelOS."""

import sys
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_realistic_budget_and_currency_switch():
    print("\n" + "=" * 70)
    print("  TEST: REALISTIC BUDGETING & CONVERSATIONAL CURRENCY SWITCHING")
    print("=" * 70)

    # 1. Start session with trip details in INR
    session_id = "test-budget-currency-session"
    msg1 = "Plan a 10-day trip to Tokyo and Kyoto for 2 adults with a budget of 400000 INR"
    print(f"\n[Turn 1] User: {msg1}")

    resp1 = client.post("/api/chat", json={"message": msg1, "session_id": session_id})
    assert resp1.status_code == 200, f"Error: {resp1.text}"
    data1 = resp1.json()

    print(f"Assistant > {data1['message'][:150]}...")
    b1 = data1.get("budget")
    assert b1 is not None, "Expected budget in turn 1"
    print(f"Turn 1 Budget Currency: {b1['currency']}")
    print(f"Turn 1 Total User Budget: {b1['total_budget']} {b1['currency']}")
    print(f"Turn 1 Flight Estimate: {b1['flights']} {b1['currency']}")
    print(f"Turn 1 Hotel Estimate: {b1['hotels']} {b1['currency']}")
    print(f"Turn 1 Food Estimate: {b1['food']} {b1['currency']}")
    print(f"Turn 1 Activities Estimate: {b1['activities']} {b1['currency']}")
    print(f"Turn 1 Transport Estimate: {b1['transport']} {b1['currency']}")

    assert b1["currency"] == "INR"
    assert b1["total_budget"] == 400000.0
    assert b1["flights"] > 50000, f"Flight cost in INR should be realistic for Japan, got {b1['flights']}"
    assert b1["hotels"] > 50000, f"Hotel cost in INR should be realistic for Japan, got {b1['hotels']}"
    print("[PASS] Turn 1: Realistic destination-aware budgeting in INR verified!")

    # 2. Switch currency from INR to Japanese Yen
    msg2 = "change the currecy tfriom inr tov jappanese currency"
    print(f"\n[Turn 2] User: {msg2}")

    resp2 = client.post("/api/chat", json={"message": msg2, "session_id": session_id})
    assert resp2.status_code == 200, f"Error: {resp2.text}"
    data2 = resp2.json()

    print(f"Assistant >\n{data2['message']}")
    b2 = data2.get("budget")
    state2 = data2.get("travel_state")

    assert state2["currency"] == "JPY", f"State currency should be JPY, got {state2['currency']}"
    assert b2 is not None, "Expected budget in turn 2"
    assert b2["currency"] == "JPY", f"Budget currency should be JPY, got {b2['currency']}"
    assert b2["total_budget"] > 500000, f"Budget in JPY should be ~667,000, got {b2['total_budget']}"
    assert b2["flights"] > 100000, f"Flight in JPY should be > 100,000, got {b2['flights']}"
    print(f"Turn 2 Converted Budget in JPY: {b2['total_budget']} JPY")
    print(f"Turn 2 Converted Flights: {b2['flights']} JPY")
    print(f"Turn 2 Converted Hotels: {b2['hotels']} JPY")
    print(f"Turn 2 Converted Food: {b2['food']} JPY")
    print("[PASS] Turn 2: Conversational currency switch to JPY verified!")

    # 3. Switch currency to USD
    msg3 = "convert my budget to USD"
    print(f"\n[Turn 3] User: {msg3}")

    resp3 = client.post("/api/chat", json={"message": msg3, "session_id": session_id})
    assert resp3.status_code == 200, f"Error: {resp3.text}"
    data3 = resp3.json()

    b3 = data3.get("budget")
    state3 = data3.get("travel_state")

    assert state3["currency"] == "USD", f"State currency should be USD, got {state3['currency']}"
    assert b3["currency"] == "USD", f"Budget currency should be USD, got {b3['currency']}"
    assert 2000 < b3["total_budget"] < 8000, f"Budget in USD should be ~$4,000-$5,000, got {b3['total_budget']}"
    print(f"Turn 3 Converted Budget in USD: ${b3['total_budget']}")
    print(f"Turn 3 Converted Flights: ${b3['flights']}")
    print(f"Turn 3 Converted Hotels: ${b3['hotels']}")
    print("[PASS] Turn 3: Conversational currency switch to USD verified!")

    print("\n" + "=" * 70)
    print("  ALL REALISTIC BUDGETING & CURRENCY SWITCHING TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_realistic_budget_and_currency_switch()
