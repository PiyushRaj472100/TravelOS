"""
TravelOS Analytics Data Warehouse - BigQuery Synthetic Demo Seeder
==================================================================
Seeds realistic, rich synthetic travel telemetry directly into Google BigQuery.

Features:
- Purely synthetic (zero third-party API calls)
- Fully driverless (uses google-cloud-bigquery REST API, no ODBC needed)
- Deterministic seed 42
- Tagged with is_demo = TRUE and data_source = 'synthetic'

Usage:
    python scripts/seed_bigquery_demo.py
    python scripts/seed_bigquery_demo.py --clean
"""

import sys
import os
import random
from datetime import datetime, date, timedelta, timezone
import argparse
from dotenv import load_dotenv

# Add parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

try:
    from google.cloud import bigquery
    from google.api_core.exceptions import NotFound
except ImportError:
    print("[ERROR] google-cloud-bigquery not installed. Run: pip install google-cloud-bigquery db-dtypes")
    sys.exit(1)

PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "")
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "travelos_analytics")
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

DESTINATIONS = [
    ("Paris", "France", "Europe", 48.8566, 2.3522),
    ("Tokyo", "Japan", "Asia", 35.6762, 139.6503),
    ("New York", "United States", "North America", 40.7128, -74.0060),
    ("Rome", "Italy", "Europe", 41.9028, 12.4964),
    ("London", "United Kingdom", "Europe", 51.5074, -0.1278),
    ("Barcelona", "Spain", "Europe", 41.3851, 2.1734),
    ("Bali", "Indonesia", "Asia", -8.4095, 115.1889),
    ("Dubai", "United Arab Emirates", "Middle East", 25.2048, 55.2708),
    ("Bangkok", "Thailand", "Asia", 13.7563, 100.5018),
    ("Sydney", "Australia", "Oceania", -33.8688, 151.2093),
    ("Cape Town", "South Africa", "Africa", -33.9249, 18.4241),
    ("Amsterdam", "Netherlands", "Europe", 52.3676, 4.9041),
    ("Singapore", "Singapore", "Asia", 1.3521, 103.8198),
    ("Kyoto", "Japan", "Asia", 35.0116, 135.7681),
    ("San Francisco", "United States", "North America", 37.7749, -122.4194),
]

AGENTS = [
    ("OrchestratorAgent", "Supervisor agent orchestrating the multi-agent graph", "LangGraph supervisor"),
    ("ResearchAgent", "RAG destination knowledge agent", "FAISS vector search"),
    ("HotelAgent", "RouteStack hotel search agent", "Live hotel inventory"),
    ("ActivityAgent", "Activity and attractions discovery agent", "Points of interest"),
    ("ItineraryAgent", "Day-by-day itinerary synthesizer", "Scheduling agent"),
    ("BudgetAgent", "Trip budget analysis agent", "Financial feasibility"),
]

PROVIDERS = [
    ("Duffel", "Flights", "Live flight search and pricing API"),
    ("RouteStack", "Hotels", "Live hotel inventory and booking API"),
    ("Geoapify", "Places", "Places, points of interest, and geocoding"),
    ("MapTiler", "Maps", "Map tile rendering and map graphics"),
    ("Open-Meteo", "Weather", "Forecast and historical climate API"),
    ("Google Gemini", "LLM", "Foundation model for multi-agent reasoning"),
]

COUNTRIES = ["United States", "United Kingdom", "Germany", "France", "Canada", "Australia", "India", "Japan", "Singapore"]
PLATFORMS = ["web", "mobile-ios", "mobile-android", "tablet"]
ACQUISITIONS = ["organic_search", "direct", "referral", "social_media", "newsletter"]
INTENTS = ["flight_search", "hotel_search", "activity_planning", "full_itinerary", "budget_query"]
RESPONSE_TYPES = ["direct_answer", "flight_results", "hotel_cards", "itinerary_view", "budget_breakdown"]


def get_client():
    if not PROJECT_ID or PROJECT_ID == "your-gcp-project-id":
        print("[ERROR] Please set BIGQUERY_PROJECT_ID in backend/.env")
        sys.exit(1)
    if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        return bigquery.Client(project=PROJECT_ID, credentials=creds)
    return bigquery.Client(project=PROJECT_ID)


def ensure_schema(client):
    """Executes schema.sql if tables do not exist."""
    print("Checking / creating BigQuery tables...")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "analytics", "bigquery", "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_text = f.read()
        # Replace dataset name with configured dataset id
        sql_text = sql_text.replace("travelos_analytics", f"{PROJECT_ID}.{DATASET_ID}")
        job = client.query(sql_text)
        job.result()
        print("Schema verified in BigQuery.")


def clean_demo(client):
    print("Purging existing synthetic demo records (is_demo = TRUE)...")
    tables = [
        "fact_error", "fact_api_usage", "fact_agent_execution", "fact_itinerary",
        "fact_weather_search", "fact_place_search", "fact_hotel_search",
        "fact_flight_search", "fact_chat", "fact_session", "dim_trip", "dim_user"
    ]
    for tbl in tables:
        try:
            client.query(f"DELETE FROM `{PROJECT_ID}.{DATASET_ID}.{tbl}` WHERE is_demo = TRUE").result()
        except Exception:
            pass
    print("Clean completed.")


def insert_batch(client, table_name, rows):
    if not rows:
        return
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    job = client.load_table_from_json(rows, table_ref)
    job.result()


def seed_data(client):
    print("Generating and streaming synthetic records into BigQuery (Free Tier / Sandbox compatible)...")

    # 1. Dim Date
    date_rows = []
    curr = date(2025, 1, 1)
    end = date(2026, 12, 31)
    while curr <= end:
        date_rows.append({
            "date_key": curr.year * 10000 + curr.month * 100 + curr.day,
            "full_date": curr.isoformat(),
            "year": curr.year,
            "quarter": (curr.month - 1) // 3 + 1,
            "month": curr.month,
            "month_name": curr.strftime("%B"),
            "week": int(curr.strftime("%W")) + 1,
            "day": curr.day,
            "day_name": curr.strftime("%A"),
            "is_weekend": curr.weekday() in (5, 6),
        })
        curr += timedelta(days=1)
    insert_batch(client, "dim_date", date_rows)
    print(f"Inserted {len(date_rows)} dates.")

    # 2. Dim Agent & Provider & Destination
    ag_rows = [{"agent_key": i+1, "agent_name": a[0], "agent_role": a[1], "description": a[2]} for i, a in enumerate(AGENTS)]
    insert_batch(client, "dim_agent", ag_rows)

    prov_rows = [{"provider_key": i+1, "provider_name": p[0], "provider_type": p[1], "description": p[2]} for i, p in enumerate(PROVIDERS)]
    insert_batch(client, "dim_provider", prov_rows)

    dest_rows = [{"destination_key": i+1, "destination_name": d[0], "country": d[1], "region": d[2], "latitude": d[3], "longitude": d[4]} for i, d in enumerate(DESTINATIONS)]
    insert_batch(client, "dim_destination", dest_rows)
    print("Core dimensions seeded.")

    # 3. Users, Sessions, Facts
    user_rows = []
    session_rows = []
    trip_rows = []
    chat_rows = []
    flight_rows = []
    hotel_rows = []
    agent_exec_rows = []
    api_rows = []

    # Use recent dates so BigQuery free tier doesn't drop expired partitions
    base_time = datetime.now(timezone.utc) - timedelta(days=45)
    # Weights to make some destinations more popular than others
    # Paris, Tokyo, NY, Rome, London are highly weighted
    dest_weights = [25, 20, 15, 12, 10, 8, 5, 5, 4, 3, 2, 2, 1, 1, 1]
    
    for u_idx in range(1, 501):
        u_key = u_idx
        u_created = base_time + timedelta(days=random.randint(0, 300))
        user_rows.append({
            "user_key": u_key,
            "user_id": f"demo_usr_{u_idx:03d}",
            "account_created_at": u_created.isoformat(),
            "country": random.choice(COUNTRIES),
            "platform": random.choice(PLATFORMS),
            "acquisition_source": random.choice(ACQUISITIONS),
            "data_source": "synthetic",
            "is_demo": True,
        })

        for s_idx in range(random.randint(1, 4)):
            s_key = len(session_rows) + 1
            sess_id = f"demo_sess_{u_idx}_{s_idx+1}_{random.randint(100, 999)}"
            s_time = u_created + timedelta(days=random.randint(1, 30), hours=random.randint(1, 12))
            dur_sec = random.randint(60, 600)
            msg_cnt = random.randint(4, 14)
            itin_gen = random.random() < 0.70

            session_rows.append({
                "session_key": s_key,
                "session_id": sess_id,
                "user_key": u_key,
                "date_key": s_time.year * 10000 + s_time.month * 100 + s_time.day,
                "started_at": s_time.isoformat(),
                "ended_at": (s_time + timedelta(seconds=dur_sec)).isoformat(),
                "duration_seconds": dur_sec,
                "message_count": msg_cnt,
                "itinerary_generated": itin_gen,
                "data_source": "synthetic",
                "is_demo": True,
            })
            d_idx = random.choices(range(len(DESTINATIONS)), weights=dest_weights)[0]
            dest = DESTINATIONS[d_idx]
            t_key = len(trip_rows) + 1
            trip_rows.append({
                "trip_key": t_key,
                "user_key": u_key,
                "session_id": sess_id,
                "destination_key": d_idx + 1,
                "destination_name": dest[0],
                "start_date": (s_time + timedelta(days=30)).date().isoformat(),
                "duration_days": random.randint(3, 10),
                "budget": float(random.randint(1000, 5000)),
                "currency": "USD",
                "travelers": random.randint(1, 4),
                "trip_status": random.choice(["completed", "planned", "abandoned"]),
                "created_at": s_time.isoformat(),
                "data_source": "synthetic",
                "is_demo": True,
            })

            # Flight search
            flight_rows.append({
                "search_key": len(flight_rows) + 1,
                "session_key": s_key,
                "user_key": u_key,
                "trip_key": t_key,
                "session_id": sess_id,
                "date_key": s_time.year * 10000 + s_time.month * 100 + s_time.day,
                "search_timestamp": s_time.isoformat(),
                "origin_airport": "JFK",
                "destination_airport": dest[0][:3].upper(),
                "destination_key": d_idx + 1,
                "departure_date": (s_time + timedelta(days=30)).date().isoformat(),
                "passengers": 2,
                "cabin_class": "economy",
                "results_count": random.randint(5, 25),
                "lowest_price": float(random.randint(350, 1100)),
                "currency": "USD",
                "provider_key": 1,
                "success": True,
                "latency_ms": random.randint(400, 1500),
                "data_source": "synthetic",
                "is_demo": True,
            })

            # Hotel search
            hotel_rows.append({
                "search_key": len(hotel_rows) + 1,
                "session_key": s_key,
                "user_key": u_key,
                "trip_key": t_key,
                "session_id": sess_id,
                "date_key": s_time.year * 10000 + s_time.month * 100 + s_time.day,
                "search_timestamp": s_time.isoformat(),
                "destination_name": dest[0],
                "destination_key": d_idx + 1,
                "check_in_date": (s_time + timedelta(days=30)).date().isoformat(),
                "check_out_date": (s_time + timedelta(days=37)).date().isoformat(),
                "rooms": 1,
                "travelers": 2,
                "results_count": random.randint(10, 40),
                "lowest_price": float(random.randint(120, 450)),
                "currency": "USD",
                "provider_key": 2,
                "success": True,
                "latency_ms": random.randint(300, 1200),
                "data_source": "synthetic",
                "is_demo": True,
            })

            # Agent executions
            for ag_idx in range(1, 5):
                agent_exec_rows.append({
                    "execution_key": len(agent_exec_rows) + 1,
                    "session_key": s_key,
                    "user_key": u_key,
                    "trip_key": t_key,
                    "session_id": sess_id,
                    "agent_key": ag_idx,
                    "date_key": s_time.year * 10000 + s_time.month * 100 + s_time.day,
                    "started_at": s_time.isoformat(),
                    "completed_at": (s_time + timedelta(milliseconds=800)).isoformat(),
                    "duration_ms": random.randint(250, 1400),
                    "status": "success",
                    "model": "gemini-flash-latest",
                    "input_tokens": random.randint(500, 1500),
                    "output_tokens": random.randint(200, 600),
                    "error_type": None,
                    "data_source": "synthetic",
                    "is_demo": True,
                })

    insert_batch(client, "dim_user", user_rows)
    insert_batch(client, "fact_session", session_rows)
    insert_batch(client, "dim_trip", trip_rows)
    insert_batch(client, "fact_flight_search", flight_rows)
    insert_batch(client, "fact_hotel_search", hotel_rows)
    insert_batch(client, "fact_agent_execution", agent_exec_rows)

    print("\n-------------------------------------------------------------")
    print(f"BigQuery Demo Seeding Successful!")
    print(f"Users inserted:          {len(user_rows)}")
    print(f"Sessions inserted:       {len(session_rows)}")
    print(f"Trips inserted:          {len(trip_rows)}")
    print(f"Flight searches:         {len(flight_rows)}")
    print(f"Hotel searches:          {len(hotel_rows)}")
    print(f"Agent executions:        {len(agent_exec_rows)}")
    print("-------------------------------------------------------------\n")


def main():
    parser = argparse.ArgumentParser(description="TravelOS BigQuery Synthetic Demo Seeder")
    parser.add_argument("--clean", action="store_true", help="Purge prior demo rows")
    args = parser.parse_args()

    client = get_client()
    if args.clean:
        clean_demo(client)
    ensure_schema(client)
    seed_data(client)


if __name__ == "__main__":
    main()
