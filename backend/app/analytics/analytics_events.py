"""
TravelOS Analytics -- Event Tracking API

Clean public interface for all analytics tracking.
Called from graph nodes, services, etc.

IMPORTANT:
- All tracking calls are wrapped in try/except
- Analytics failures NEVER crash TravelOS
- All production records: is_demo=0, data_source='production'
"""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from app.analytics import analytics_repository as repo

logger = logging.getLogger("travelos.analytics")

_DATA_SOURCE = "production"
_IS_DEMO = 0


# ============================================================
# Session tracking
# ============================================================

# In-memory cache: session_id -> user_key (avoids DB roundtrips per message)
_session_user_map: dict[str, Optional[int]] = {}


def track_session(session_id: str) -> Optional[int]:
    """
    Called once per new session. Creates dim_user record if needed,
    inserts fact_session. Returns user_key.
    """
    try:
        if session_id in _session_user_map:
            return _session_user_map[session_id]

        user_key = repo.get_or_create_user(
            user_id=session_id,
            platform="web",
            data_source=_DATA_SOURCE,
            is_demo=_IS_DEMO
        )
        _session_user_map[session_id] = user_key

        repo.insert_session(
            user_key=user_key,
            session_id=session_id,
            started_at=datetime.now(timezone.utc),
            data_source=_DATA_SOURCE,
            is_demo=_IS_DEMO
        )
        return user_key
    except Exception as exc:
        logger.error(f"[Analytics] track_session error: {exc}")
        return None


def get_user_key(session_id: str) -> Optional[int]:
    """Retrieve cached user_key for session, or look up from DB."""
    if session_id in _session_user_map:
        return _session_user_map[session_id]
    return repo.get_or_create_user(
        user_id=session_id,
        platform="web",
        data_source=_DATA_SOURCE,
        is_demo=_IS_DEMO
    )


# ============================================================
# Trip tracking
# ============================================================

def track_trip(session_id: str, trip_id: str, *,
               destination_name: str = None,
               duration_days: int = None,
               traveler_count: int = None,
               budget: float = None,
               currency: str = None,
               travel_style: str = None,
               trip_status: str = "planned") -> Optional[int]:
    """
    Create or retrieve a trip record.
    Returns trip_key.
    """
    try:
        user_key = get_user_key(session_id)

        destination_key = None
        if destination_name:
            dest_id = destination_name.lower().replace(" ", "_")
            destination_key = repo.get_or_create_destination(
                destination_id=dest_id,
                name=destination_name
            )

        return repo.insert_trip(
            trip_id=trip_id,
            user_key=user_key,
            session_id=session_id,
            destination_key=destination_key,
            duration_days=duration_days,
            traveler_count=traveler_count,
            budget=budget,
            currency=currency,
            travel_style=travel_style,
            trip_status=trip_status,
            data_source=_DATA_SOURCE,
            is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_trip error: {exc}")
        return None


# ============================================================
# Chat tracking
# ============================================================

def track_chat(session_id: str, role: str, message_length: int, *,
               trip_key: int = None, intent: str = None,
               response_type: str = None, latency_ms: int = None):
    """Track one chat message (no content stored)."""
    try:
        user_key = get_user_key(session_id)
        repo.insert_chat(
            user_key=user_key,
            session_id=session_id,
            trip_key=trip_key,
            role=role,
            intent=intent,
            response_type=response_type,
            message_length=message_length,
            latency_ms=latency_ms,
            data_source=_DATA_SOURCE,
            is_demo=_IS_DEMO
        )
        repo.update_session(session_id, message_count=1)
    except Exception as exc:
        logger.error(f"[Analytics] track_chat error: {exc}")


# ============================================================
# Search tracking
# ============================================================

def track_flight_search(session_id: str, *, trip_key=None,
                         origin=None, destination=None, departure_date=None,
                         passengers=1, cabin_class="economy",
                         results_count=None, lowest_price=None, currency=None,
                         success=True, latency_ms=None):
    try:
        user_key = get_user_key(session_id)
        provider_key = repo.get_provider_key("Duffel")
        repo.insert_flight_search(
            user_key, session_id,
            trip_key=trip_key, origin=origin, destination=destination,
            departure_date=departure_date, passengers=passengers,
            cabin_class=cabin_class, results_count=results_count,
            lowest_price=lowest_price, currency=currency,
            provider_key=provider_key, success=success, latency_ms=latency_ms,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_flight_search error: {exc}")


def track_hotel_search(session_id: str, *, trip_key=None,
                        destination=None, check_in=None, check_out=None,
                        rooms=1, travelers=2, results_count=None,
                        lowest_price=None, currency=None,
                        success=True, latency_ms=None):
    try:
        user_key = get_user_key(session_id)
        provider_key = repo.get_provider_key("RouteStack")
        repo.insert_hotel_search(
            user_key, session_id,
            trip_key=trip_key, destination=destination,
            check_in=check_in, check_out=check_out,
            rooms=rooms, travelers=travelers,
            results_count=results_count, lowest_price=lowest_price,
            currency=currency, provider_key=provider_key,
            success=success, latency_ms=latency_ms,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_hotel_search error: {exc}")


def track_place_search(session_id: str, *, trip_key=None,
                        destination=None, category=None, results_count=None,
                        success=True, latency_ms=None):
    try:
        user_key = get_user_key(session_id)
        provider_key = repo.get_provider_key("Geoapify")
        repo.insert_place_search(
            user_key, session_id,
            trip_key=trip_key, destination=destination,
            category=category, results_count=results_count,
            provider_key=provider_key, success=success, latency_ms=latency_ms,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_place_search error: {exc}")


def track_weather_search(session_id: str, *, trip_key=None,
                          destination=None, success=True, latency_ms=None):
    try:
        user_key = get_user_key(session_id)
        provider_key = repo.get_provider_key("Open-Meteo")
        repo.insert_weather_search(
            user_key, session_id,
            trip_key=trip_key, destination=destination,
            request_date=datetime.now(timezone.utc).date(),
            provider_key=provider_key, success=success, latency_ms=latency_ms,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_weather_search error: {exc}")


def track_itinerary(session_id: str, *, trip_key=None,
                     destination=None, duration_days=None, activity_count=None,
                     generation_time_ms=None):
    try:
        user_key = get_user_key(session_id)
        repo.insert_itinerary(
            user_key, session_id,
            trip_key=trip_key, destination=destination,
            duration_days=duration_days, activity_count=activity_count,
            generation_time_ms=generation_time_ms,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
        repo.update_session(session_id, itinerary_generated=True)
    except Exception as exc:
        logger.error(f"[Analytics] track_itinerary error: {exc}")


def track_agent_execution(session_id: str, agent_name: str, *,
                           trip_key=None, started_at: datetime = None,
                           duration_ms: int = None, status: str = "success",
                           model: str = None, input_tokens: int = None,
                           output_tokens: int = None, error_type: str = None):
    try:
        user_key = get_user_key(session_id)
        agent_key = repo.get_agent_key(agent_name)
        completed_at = datetime.now(timezone.utc)
        repo.insert_agent_execution(
            user_key, session_id, agent_key,
            trip_key=trip_key,
            started_at=started_at or completed_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            status=status, model=model,
            input_tokens=input_tokens, output_tokens=output_tokens,
            error_type=error_type,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_agent_execution error: {exc}")


def track_api_usage(session_id: str, provider_name: str, *,
                     trip_key=None, endpoint=None, latency_ms=None,
                     status_code=200, success=True, error_type=None,
                     estimated_cost=None):
    try:
        user_key = get_user_key(session_id)
        provider_key = repo.get_provider_key(provider_name)
        repo.insert_api_usage(
            user_key, session_id, provider_key,
            trip_key=trip_key, endpoint=endpoint,
            latency_ms=latency_ms, status_code=status_code,
            success=success, error_type=error_type,
            estimated_cost=estimated_cost,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_api_usage error: {exc}")


def track_error(session_id: str, service: str, error_type: str, *,
                trip_key=None, provider_name: str = None,
                agent_name: str = None, status_code: int = None):
    try:
        user_key = get_user_key(session_id)
        provider_key = repo.get_provider_key(provider_name) if provider_name else None
        agent_key = repo.get_agent_key(agent_name) if agent_name else None
        repo.insert_error(
            user_key, session_id,
            trip_key=trip_key, provider_key=provider_key, agent_key=agent_key,
            service=service, error_type=error_type, status_code=status_code,
            data_source=_DATA_SOURCE, is_demo=_IS_DEMO
        )
    except Exception as exc:
        logger.error(f"[Analytics] track_error error: {exc}")
