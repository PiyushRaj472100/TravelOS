"""
TravelOS Analytics -- SQL Server Repository

Low-level INSERT methods for every analytics table.
Each method is wrapped in try/except so analytics failures
NEVER crash the main TravelOS application.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.analytics.analytics_connection import get_connection, is_available

logger = logging.getLogger("travelos.analytics")

DATA_SOURCE_PRODUCTION = "production"
DATA_SOURCE_SYNTHETIC  = "synthetic"


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# Dimension helpers -- get-or-create keys
# ============================================================

def get_or_create_user(user_id: str, *, country: str = None,
                        platform: str = "web", acquisition_source: str = None,
                        account_created_at: datetime = None,
                        data_source: str = DATA_SOURCE_PRODUCTION,
                        is_demo: int = 0) -> Optional[int]:
    """Return user_key for existing user_id, or insert and return new key."""
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute(
                "SELECT user_key FROM analytics.dim_user WHERE user_id = ?",
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                """
                INSERT INTO analytics.dim_user
                    (user_id, account_created_at, country, platform,
                     acquisition_source, data_source, is_demo)
                OUTPUT INSERTED.user_key
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    account_created_at or _now(),
                    country, platform, acquisition_source,
                    data_source, is_demo
                )
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception as exc:
        logger.error(f"[Analytics] get_or_create_user error: {exc}")
        return None


def get_or_create_destination(destination_id: str, name: str, *,
                               city: str = None, country: str = None,
                               region: str = None,
                               lat: float = None, lng: float = None) -> Optional[int]:
    """Return destination_key, creating if needed."""
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute(
                "SELECT destination_key FROM analytics.dim_destination WHERE destination_id = ?",
                (destination_id,)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                """
                INSERT INTO analytics.dim_destination
                    (destination_id, destination_name, city, country, region, latitude, longitude)
                OUTPUT INSERTED.destination_key
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (destination_id, name, city, country, region, lat, lng)
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception as exc:
        logger.error(f"[Analytics] get_or_create_destination error: {exc}")
        return None


def get_agent_key(agent_name: str) -> Optional[int]:
    """Return agent_key for agent_name."""
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute(
                "SELECT agent_key FROM analytics.dim_agent WHERE agent_name = ?",
                (agent_name,)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            # Auto-register unknown agent (future-proof)
            cur.execute(
                """
                INSERT INTO analytics.dim_agent (agent_name, agent_type, agent_version, is_active)
                OUTPUT INSERTED.agent_key
                VALUES (?, 'unknown', '1.0', 1)
                """,
                (agent_name,)
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception as exc:
        logger.error(f"[Analytics] get_agent_key error: {exc}")
        return None


def get_provider_key(provider_name: str) -> Optional[int]:
    """Return provider_key for provider_name."""
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute(
                "SELECT provider_key FROM analytics.dim_provider WHERE provider_name = ?",
                (provider_name,)
            )
            row = cur.fetchone()
            return row[0] if row else None
    except Exception as exc:
        logger.error(f"[Analytics] get_provider_key error: {exc}")
        return None


# ============================================================
# Fact inserts
# ============================================================

def insert_session(user_key: Optional[int], session_id: str, *,
                   started_at: datetime = None,
                   message_count: int = 0,
                   data_source: str = DATA_SOURCE_PRODUCTION,
                   is_demo: int = 0) -> Optional[int]:
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_session
                    (user_key, session_id, started_at, message_count,
                     trip_started, itinerary_generated, session_status,
                     data_source, is_demo)
                OUTPUT INSERTED.session_event_key
                VALUES (?, ?, ?, ?, 0, 0, 'active', ?, ?)
                """,
                (user_key, session_id, started_at or _now(), message_count,
                 data_source, is_demo)
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception as exc:
        logger.error(f"[Analytics] insert_session error: {exc}")
        return None


def update_session(session_id: str, *, message_count: int = None,
                   trip_started: bool = None, itinerary_generated: bool = None,
                   ended_at: datetime = None, status: str = None):
    """Update an existing session fact row."""
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            updates = []
            params = []
            if message_count is not None:
                updates.append("message_count = ?"); params.append(message_count)
            if trip_started is not None:
                updates.append("trip_started = ?"); params.append(1 if trip_started else 0)
            if itinerary_generated is not None:
                updates.append("itinerary_generated = ?"); params.append(1 if itinerary_generated else 0)
            if ended_at is not None:
                updates.append("ended_at = ?"); params.append(ended_at)
            if status is not None:
                updates.append("session_status = ?"); params.append(status)
            if not updates:
                return
            params.append(session_id)
            cur.execute(
                f"UPDATE analytics.fact_session SET {', '.join(updates)} WHERE session_id = ?",
                params
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] update_session error: {exc}")


def insert_trip(trip_id: str, user_key: Optional[int], session_id: str, *,
                destination_key: int = None, start_date=None, end_date=None,
                duration_days: int = None, traveler_count: int = None,
                budget: float = None, currency: str = None,
                travel_style: str = None, trip_status: str = "planned",
                data_source: str = DATA_SOURCE_PRODUCTION,
                is_demo: int = 0) -> Optional[int]:
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            cur = conn.cursor()
            # Check existence
            cur.execute("SELECT trip_key FROM analytics.dim_trip WHERE trip_id = ?", (trip_id,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                """
                INSERT INTO analytics.dim_trip
                    (trip_id, user_key, session_id, destination_key, start_date, end_date,
                     duration_days, traveler_count, budget, currency, travel_style,
                     trip_status, data_source, is_demo)
                OUTPUT INSERTED.trip_key
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (trip_id, user_key, session_id, destination_key, start_date, end_date,
                 duration_days, traveler_count, budget, currency, travel_style,
                 trip_status, data_source, is_demo)
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception as exc:
        logger.error(f"[Analytics] insert_trip error: {exc}")
        return None


def insert_chat(user_key: Optional[int], session_id: str, *,
                trip_key: int = None, role: str = "user",
                intent: str = None, response_type: str = None,
                message_length: int = None, latency_ms: int = None,
                timestamp: datetime = None,
                data_source: str = DATA_SOURCE_PRODUCTION, is_demo: int = 0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_chat
                    (user_key, session_id, trip_key, timestamp, role,
                     intent, response_type, message_length, latency_ms, data_source, is_demo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_key, session_id, trip_key, timestamp or _now(),
                 role, intent, response_type, message_length, latency_ms,
                 data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_chat error: {exc}")


def insert_flight_search(user_key, session_id, *,
                          trip_key=None, origin=None, destination=None,
                          departure_date=None, return_date=None, passengers=1,
                          cabin_class="economy", results_count=None,
                          lowest_price=None, currency=None,
                          provider_key=None, success=True, latency_ms=None,
                          data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_flight_search
                    (user_key, session_id, trip_key, origin, destination,
                     departure_date, return_date, passengers, cabin_class,
                     results_count, lowest_price, currency, provider_key,
                     success, latency_ms, data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (user_key, session_id, trip_key, origin, destination,
                 departure_date, return_date, passengers, cabin_class,
                 results_count, lowest_price, currency, provider_key,
                 1 if success else 0, latency_ms, data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_flight_search error: {exc}")


def insert_hotel_search(user_key, session_id, *,
                         trip_key=None, destination=None,
                         check_in=None, check_out=None, rooms=1, travelers=2,
                         results_count=None, lowest_price=None, currency=None,
                         provider_key=None, success=True, latency_ms=None,
                         data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_hotel_search
                    (user_key, session_id, trip_key, destination, check_in, check_out,
                     rooms, travelers, results_count, lowest_price, currency,
                     provider_key, success, latency_ms, data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (user_key, session_id, trip_key, destination, check_in, check_out,
                 rooms, travelers, results_count, lowest_price, currency,
                 provider_key, 1 if success else 0, latency_ms, data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_hotel_search error: {exc}")


def insert_place_search(user_key, session_id, *,
                         trip_key=None, destination=None, category=None,
                         results_count=None, provider_key=None,
                         success=True, latency_ms=None,
                         data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_place_search
                    (user_key, session_id, trip_key, destination, category,
                     results_count, provider_key, success, latency_ms, data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (user_key, session_id, trip_key, destination, category,
                 results_count, provider_key, 1 if success else 0, latency_ms,
                 data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_place_search error: {exc}")


def insert_weather_search(user_key, session_id, *,
                           trip_key=None, destination=None,
                           request_date=None, forecast_date=None,
                           provider_key=None, success=True, latency_ms=None,
                           data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_weather_search
                    (user_key, session_id, trip_key, destination, request_date,
                     forecast_date, provider_key, success, latency_ms, data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (user_key, session_id, trip_key, destination, request_date,
                 forecast_date, provider_key, 1 if success else 0, latency_ms,
                 data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_weather_search error: {exc}")


def insert_itinerary(user_key, session_id, *,
                      trip_key=None, destination=None, duration_days=None,
                      activity_count=None, generation_time_ms=None, status="generated",
                      data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_itinerary
                    (user_key, session_id, trip_key, destination, duration_days,
                     activity_count, generation_time_ms, status, data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (user_key, session_id, trip_key, destination, duration_days,
                 activity_count, generation_time_ms, status, data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_itinerary error: {exc}")


def insert_agent_execution(user_key, session_id, agent_key, *,
                            trip_key=None, started_at=None, completed_at=None,
                            duration_ms=None, status="success", model=None,
                            input_tokens=None, output_tokens=None, error_type=None,
                            data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_agent_execution
                    (user_key, session_id, trip_key, agent_key, started_at, completed_at,
                     duration_ms, status, model, input_tokens, output_tokens, error_type,
                     data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (user_key, session_id, trip_key, agent_key,
                 started_at or _now(), completed_at,
                 duration_ms, status, model, input_tokens, output_tokens, error_type,
                 data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_agent_execution error: {exc}")


def insert_api_usage(user_key, session_id, provider_key, *,
                      trip_key=None, endpoint=None,
                      request_timestamp=None, response_timestamp=None,
                      latency_ms=None, status_code=200, success=True,
                      error_type=None, estimated_cost=None,
                      data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_api_usage
                    (user_key, session_id, trip_key, provider_key, endpoint,
                     request_timestamp, response_timestamp, latency_ms,
                     status_code, success, error_type, estimated_cost,
                     data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (user_key, session_id, trip_key, provider_key, endpoint,
                 request_timestamp or _now(), response_timestamp,
                 latency_ms, status_code, 1 if success else 0, error_type,
                 estimated_cost, data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_api_usage error: {exc}")


def insert_error(user_key, session_id, *,
                  trip_key=None, provider_key=None, agent_key=None,
                  service=None, error_type=None, status_code=None,
                  data_source=DATA_SOURCE_PRODUCTION, is_demo=0):
    try:
        with get_connection() as conn:
            if conn is None:
                return
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO analytics.fact_error
                    (user_key, session_id, trip_key, provider_key, agent_key,
                     service, error_type, status_code, resolved, data_source, is_demo)
                VALUES (?,?,?,?,?,?,?,?,0,?,?)
                """,
                (user_key, session_id, trip_key, provider_key, agent_key,
                 service, error_type, status_code, data_source, is_demo)
            )
            conn.commit()
    except Exception as exc:
        logger.error(f"[Analytics] insert_error error: {exc}")
