"""
TravelOS Analytics Data Warehouse - Synthetic Demo Data Generator
==================================================================
Populates Microsoft SQL Server with realistic, rich synthetic data
for Tableau dashboards, demonstrations, and QA validation.

Highlights:
- Purely synthetic: NEVER calls real APIs (Duffel, RouteStack, Gemini, etc.)
- Deterministic: Seed 42 for reproducible demos
- Safe: All rows tagged with is_demo = 1 and data_source = 'synthetic'
- Cleanable: Run with --clean to purge existing demo data before re-seeding

Usage:
    python scripts/seed_analytics_demo.py
    python scripts/seed_analytics_demo.py --clean
"""

import sys
import os
import random
from datetime import datetime, date, timedelta, timezone
import argparse

# Add parent directory to sys.path so app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pyodbc
except ImportError:
    print("[ERROR] pyodbc is not installed. Run: pip install pyodbc")
    sys.exit(1)

from app.analytics.analytics_config import AnalyticsConfig


RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Reference data
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
    ("Reykjavik", "Iceland", "Europe", 64.1466, -21.9426),
    ("Cairo", "Egypt", "Africa", 30.0444, 31.2357),
    ("Zurich", "Switzerland", "Europe", 47.3769, 8.5417),
    ("Rio de Janeiro", "Brazil", "South America", -22.9068, -43.1729),
    ("Vancouver", "Canada", "North America", 49.2827, -123.1207),
]

AGENTS = [
    ("OrchestratorAgent", "Supervisor agent orchestrating the multi-agent graph"),
    ("ResearchAgent", "RAG destination knowledge and research agent"),
    ("HotelAgent", "RouteStack hotel search and filtering agent"),
    ("ActivityAgent", "Activity and attractions discovery agent"),
    ("ItineraryAgent", "Day-by-day itinerary synthesizer agent"),
    ("BudgetAgent", "Trip budget analysis and feasibility agent"),
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
INTENTS = ["flight_search", "hotel_search", "activity_planning", "full_itinerary", "budget_query", "weather_inquiry"]
RESPONSE_TYPES = ["direct_answer", "flight_results", "hotel_cards", "itinerary_view", "budget_breakdown"]


def get_db_connection():
    """Connect to SQL Server using AnalyticsConfig."""
    conn_str = AnalyticsConfig.connection_string()
    print(f"Connecting to SQL Server at: {AnalyticsConfig.SQL_SERVER_HOST}:{AnalyticsConfig.SQL_SERVER_PORT} ...")
    return pyodbc.connect(conn_str, autocommit=False)


def clean_demo_data(cursor):
    """Purge existing synthetic demo rows."""
    print("Purging existing synthetic demo records (is_demo = 1)...")
    facts = [
        "analytics.fact_error",
        "analytics.fact_api_usage",
        "analytics.fact_agent_execution",
        "analytics.fact_itinerary",
        "analytics.fact_weather_search",
        "analytics.fact_place_search",
        "analytics.fact_hotel_search",
        "analytics.fact_flight_search",
        "analytics.fact_chat",
        "analytics.fact_session",
    ]
    for tbl in facts:
        cursor.execute(f"DELETE FROM {tbl} WHERE is_demo = 1")

    # Purge demo dimensions
    cursor.execute("DELETE FROM analytics.dim_trip WHERE is_demo = 1")
    cursor.execute("DELETE FROM analytics.dim_user WHERE is_demo = 1")
    print("Clean completed.")


def seed_date_dimension(cursor, start_year=2024, end_year=2026):
    """Seed date dimension table if empty."""
    cursor.execute("SELECT COUNT(*) FROM analytics.dim_date")
    cnt = cursor.fetchone()[0]
    if cnt > 500:
        print(f"dim_date already populated ({cnt} rows). Skipping.")
        return

    print("Populating analytics.dim_date ...")
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    curr = start_date

    batch = []
    while curr <= end_date:
        date_key = curr.year * 10000 + curr.month * 100 + curr.day
        year = curr.year
        quarter = (curr.month - 1) // 3 + 1
        month = curr.month
        month_name = curr.strftime("%B")
        week = int(curr.strftime("%W")) + 1
        day = curr.day
        day_name = curr.strftime("%A")
        is_weekend = 1 if curr.weekday() in (5, 6) else 0

        batch.append((date_key, curr, year, quarter, month, month_name, week, day, day_name, is_weekend))
        curr += timedelta(days=1)

    cursor.executemany(
        """
        INSERT INTO analytics.dim_date 
        (date_key, full_date, year, quarter, month, month_name, week, day, day_name, is_weekend)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        batch
    )
    print(f"Inserted {len(batch)} rows into analytics.dim_date.")


def seed_core_dimensions(cursor):
    """Ensure dim_destination, dim_agent, dim_provider are populated."""
    print("Populating core dimensions (agents, providers, destinations)...")

    # Agents
    for name, desc in AGENTS:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM analytics.dim_agent WHERE agent_name = ?)
                INSERT INTO analytics.dim_agent (agent_name, agent_role) VALUES (?, ?)
        """, (name, name, desc))

    # Providers
    for name, ptype, desc in PROVIDERS:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM analytics.dim_provider WHERE provider_name = ?)
                INSERT INTO analytics.dim_provider (provider_name, provider_type, description) VALUES (?, ?, ?)
        """, (name, name, ptype, desc))

    # Destinations
    for name, country, region, lat, lon in DESTINATIONS:
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM analytics.dim_destination WHERE destination_name = ?)
                INSERT INTO analytics.dim_destination 
                (destination_name, country, region, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
        """, (name, name, country, region, lat, lon))


def generate_synthetic_data(cursor):
    """Generates cohesive, realistic synthetic records."""
    print("Generating synthetic demo dataset...")

    # Load lookup keys
    cursor.execute("SELECT agent_name, agent_key FROM analytics.dim_agent")
    agent_map = dict(cursor.fetchall())

    cursor.execute("SELECT provider_name, provider_key FROM analytics.dim_provider")
    provider_map = dict(cursor.fetchall())

    cursor.execute("SELECT destination_name, destination_key FROM analytics.dim_destination")
    dest_map = dict(cursor.fetchall())
    dest_names = list(dest_map.keys())

    # 1. Create ~45 Demo Users
    print("Creating demo users...")
    user_keys = []
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    for i in range(1, 46):
        user_id = f"demo_user_{i:03d}"
        created_at = base_time + timedelta(days=random.randint(0, 400), hours=random.randint(0, 23))
        country = random.choice(COUNTRIES)
        platform = random.choice(PLATFORMS)
        source = random.choice(ACQUISITIONS)

        cursor.execute("""
            INSERT INTO analytics.dim_user 
            (user_id, account_created_at, country, platform, acquisition_source, data_source, is_demo)
            OUTPUT INSERTED.user_key
            VALUES (?, ?, ?, ?, ?, 'synthetic', 1)
        """, (user_id, created_at, country, platform, source))
        user_key = cursor.fetchone()[0]
        user_keys.append((user_key, user_id, created_at))

    # 2. Create ~160 Sessions & Associated Trips
    print("Creating sessions, trips, searches, and agent executions...")
    session_count = 0
    trip_count = 0
    chat_count = 0
    search_count = 0
    agent_exec_count = 0
    api_call_count = 0
    error_count = 0

    for user_key, user_id, user_created in user_keys:
        num_sessions = random.choices([1, 2, 3, 5, 8], weights=[30, 35, 20, 10, 5])[0]

        for s_idx in range(num_sessions):
            session_count += 1
            session_id = f"demo_sess_{user_id}_{s_idx+1}_{random.randint(1000, 9999)}"
            sess_time = user_created + timedelta(days=random.randint(1, 60), hours=random.randint(1, 12))
            date_key = sess_time.year * 10000 + sess_time.month * 100 + sess_time.day

            msg_count = random.randint(3, 18)
            duration_sec = random.randint(45, 900)
            itinerary_gen = 1 if (msg_count > 6 and random.random() < 0.70) else 0

            # Insert Fact Session
            cursor.execute("""
                INSERT INTO analytics.fact_session
                (session_id, user_key, date_key, started_at, ended_at, duration_seconds, 
                 message_count, itinerary_generated, data_source, is_demo)
                OUTPUT INSERTED.session_key
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'synthetic', 1)
            """, (
                session_id, user_key, date_key, sess_time, 
                sess_time + timedelta(seconds=duration_sec),
                duration_sec, msg_count, itinerary_gen
            ))
            session_key = cursor.fetchone()[0]

            # Trip planning
            chosen_dest = random.choice(dest_names)
            dest_key = dest_map[chosen_dest]
            trip_status = random.choices(["completed", "planned", "abandoned"], weights=[55, 30, 15])[0]
            trip_duration = random.randint(3, 14)
            budget = random.randint(800, 7500)

            cursor.execute("""
                INSERT INTO analytics.dim_trip
                (user_key, session_id, destination_key, destination_name, start_date, 
                 duration_days, budget, currency, travelers, trip_status, created_at, data_source, is_demo)
                OUTPUT INSERTED.trip_key
                VALUES (?, ?, ?, ?, ?, ?, ?, 'USD', ?, ?, ?, 'synthetic', 1)
            """, (
                user_key, session_id, dest_key, chosen_dest, 
                (sess_time + timedelta(days=random.randint(14, 90))).date(),
                trip_duration, budget, random.randint(1, 4), trip_status, sess_time
            ))
            trip_key = cursor.fetchone()[0]
            trip_count += 1

            # 3. Create Fact Chats
            for m in range(msg_count):
                chat_count += 1
                role = "user" if m % 2 == 0 else "assistant"
                intent = random.choice(INTENTS) if role == "user" else None
                resp_type = random.choice(RESPONSE_TYPES) if role == "assistant" else None
                m_len = random.randint(15, 120) if role == "user" else random.randint(80, 450)
                latency = random.randint(400, 2800) if role == "assistant" else None

                cursor.execute("""
                    INSERT INTO analytics.fact_chat
                    (session_key, user_key, trip_key, session_id, message_timestamp, role, 
                     intent, response_type, message_length, latency_ms, data_source, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'synthetic', 1)
                """, (
                    session_key, user_key, trip_key, session_id,
                    sess_time + timedelta(seconds=m * 25), role, intent, resp_type, m_len, latency
                ))

            # 4. Create Flight and Hotel searches
            if random.random() < 0.85:
                search_count += 1
                cursor.execute("""
                    INSERT INTO analytics.fact_flight_search
                    (session_key, user_key, trip_key, session_id, date_key, search_timestamp,
                     origin_airport, destination_airport, destination_key, departure_date,
                     passengers, cabin_class, results_count, lowest_price, currency,
                     provider_key, success, latency_ms, data_source, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, 'JFK', ?, ?, ?, ?, 'economy', ?, ?, 'USD', ?, 1, ?, 'synthetic', 1)
                """, (
                    session_key, user_key, trip_key, session_id, date_key, sess_time,
                    chosen_dest[:3].upper(), dest_key, (sess_time + timedelta(days=30)).date(),
                    random.randint(1, 3), random.randint(5, 30), random.randint(280, 1400),
                    provider_map["Duffel"], random.randint(350, 1800)
                ))

            if random.random() < 0.85:
                search_count += 1
                cursor.execute("""
                    INSERT INTO analytics.fact_hotel_search
                    (session_key, user_key, trip_key, session_id, date_key, search_timestamp,
                     destination_name, destination_key, check_in_date, check_out_date,
                     rooms, travelers, results_count, lowest_price, currency,
                     provider_key, success, latency_ms, data_source, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 'USD', ?, 1, ?, 'synthetic', 1)
                """, (
                    session_key, user_key, trip_key, session_id, date_key, sess_time,
                    chosen_dest, dest_key, (sess_time + timedelta(days=30)).date(),
                    (sess_time + timedelta(days=30 + trip_duration)).date(),
                    random.randint(1, 3), random.randint(10, 45), random.randint(85, 450),
                    provider_map["RouteStack"], random.randint(250, 1200)
                ))

            # 5. Itinerary fact
            if itinerary_gen:
                cursor.execute("""
                    INSERT INTO analytics.fact_itinerary
                    (session_key, user_key, trip_key, session_id, date_key, generated_at,
                     destination_name, destination_key, duration_days, activity_count,
                     generation_time_ms, data_source, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'synthetic', 1)
                """, (
                    session_key, user_key, trip_key, session_id, date_key, sess_time,
                    chosen_dest, dest_key, trip_duration, random.randint(8, 25),
                    random.randint(1200, 4500)
                ))

            # 6. Agent Executions
            agents_to_run = ["OrchestratorAgent", "ResearchAgent", "HotelAgent", "ActivityAgent"]
            if itinerary_gen:
                agents_to_run.extend(["ItineraryAgent", "BudgetAgent"])

            for ag_name in agents_to_run:
                agent_exec_count += 1
                ag_key = agent_map[ag_name]
                exec_dur = random.randint(250, 2200)
                is_success = "success" if random.random() > 0.04 else "failed"

                cursor.execute("""
                    INSERT INTO analytics.fact_agent_execution
                    (session_key, user_key, trip_key, session_id, agent_key, date_key,
                     started_at, completed_at, duration_ms, status, model,
                     input_tokens, output_tokens, error_type, data_source, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'gemini-flash-latest', ?, ?, ?, 'synthetic', 1)
                """, (
                    session_key, user_key, trip_key, session_id, ag_key, date_key,
                    sess_time, sess_time + timedelta(milliseconds=exec_dur), exec_dur,
                    is_success, random.randint(400, 1800), random.randint(200, 900),
                    None if is_success == "success" else "AgentTimeoutException"
                ))

                if is_success == "failed":
                    error_count += 1
                    cursor.execute("""
                        INSERT INTO analytics.fact_error
                        (session_key, user_key, trip_key, session_id, date_key, occurred_at,
                         service, error_type, agent_key, status_code, data_source, is_demo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'ExecutionTimeout', ?, 504, 'synthetic', 1)
                    """, (session_key, user_key, trip_key, session_id, date_key, sess_time, ag_name, ag_key))

            # 7. External API calls
            for prov_name, prov_key in provider_map.items():
                if random.random() < 0.65:
                    api_call_count += 1
                    api_success = 1 if random.random() > 0.03 else 0
                    api_lat = random.randint(80, 850)
                    cost = round(random.uniform(0.001, 0.025), 4)

                    cursor.execute("""
                        INSERT INTO analytics.fact_api_usage
                        (session_key, user_key, trip_key, session_id, provider_key, date_key,
                         request_timestamp, endpoint, latency_ms, status_code, success,
                         error_type, estimated_cost, data_source, is_demo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, '/api/v1/search', ?, ?, ?, ?, ?, 'synthetic', 1)
                    """, (
                        session_key, user_key, trip_key, session_id, prov_key, date_key,
                        sess_time, api_lat, 200 if api_success else 429, api_success,
                        None if api_success else "RateLimitExceeded", cost
                    ))

                    if not api_success:
                        error_count += 1
                        cursor.execute("""
                            INSERT INTO analytics.fact_error
                            (session_key, user_key, trip_key, session_id, date_key, occurred_at,
                             service, error_type, provider_key, status_code, data_source, is_demo)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'HTTP_429_RateLimit', ?, 429, 'synthetic', 1)
                        """, (session_key, user_key, trip_key, session_id, date_key, sess_time, prov_name, prov_key))

    print("\n-------------------------------------------------------------")
    print(f"Synthetic demo generation complete!")
    print(f"Users generated:           {len(user_keys)}")
    print(f"Sessions created:          {session_count}")
    print(f"Trips created:             {trip_count}")
    print(f"Chat messages tracked:     {chat_count}")
    print(f"Search events tracked:     {search_count}")
    print(f"Agent executions:          {agent_exec_count}")
    print(f"External API calls:        {api_call_count}")
    print(f"Simulated error events:    {error_count}")
    print("-------------------------------------------------------------\n")


def main():
    parser = argparse.ArgumentParser(description="TravelOS SQL Server Analytics Demo Data Seeder")
    parser.add_argument("--clean", action="store_true", help="Clean prior synthetic demo data before seeding")
    args = parser.parse_args()

    try:
        conn = get_db_connection()
    except Exception as exc:
        print(f"\n[FATAL] Unable to connect to Microsoft SQL Server: {exc}")
        print("Please ensure SQL Server is running and connection details in .env are correct.")
        sys.exit(1)

    try:
        cursor = conn.cursor()
        if args.clean:
            clean_demo_data(cursor)

        seed_date_dimension(cursor)
        seed_core_dimensions(cursor)
        generate_synthetic_data(cursor)

        conn.commit()
        print("[SUCCESS] All demo data committed successfully to Microsoft SQL Server.")
    except Exception as exc:
        conn.rollback()
        print(f"\n[ERROR] Transaction failed, rolled back: {exc}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
