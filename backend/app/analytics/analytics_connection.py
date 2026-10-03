"""
TravelOS Analytics -- SQL Server Connection Manager

Thread-safe connection pool for analytics writes.
If pyodbc is not installed or SQL Server is unreachable,
the connection manager degrades gracefully without crashing TravelOS.
"""
import logging
import threading
from contextlib import contextmanager
from typing import Optional

from app.analytics.analytics_config import AnalyticsConfig

logger = logging.getLogger("travelos.analytics")

_lock = threading.Lock()
_available = False
_pyodbc = None


def _try_import_pyodbc():
    """Try to import pyodbc -- optional dependency."""
    global _pyodbc
    if _pyodbc is not None:
        return _pyodbc
    try:
        import pyodbc
        _pyodbc = pyodbc
        return pyodbc
    except ImportError:
        logger.warning(
            "[Analytics] pyodbc not installed. "
            "Analytics tracking disabled. Install with: pip install pyodbc"
        )
        return None


def _check_availability() -> bool:
    """Check once at startup if analytics DB is reachable."""
    global _available
    pyodbc = _try_import_pyodbc()
    if pyodbc is None:
        return False
    if not AnalyticsConfig.is_configured():
        logger.warning("[Analytics] SQL Server not configured. Analytics disabled.")
        return False
    if not AnalyticsConfig.ANALYTICS_ENABLED:
        logger.info("[Analytics] Analytics tracking is disabled via ANALYTICS_ENABLED=false.")
        return False
    try:
        conn = pyodbc.connect(AnalyticsConfig.connection_string(), timeout=5)
        conn.close()
        logger.info("[Analytics] SQL Server analytics connection: OK")
        return True
    except Exception as exc:
        logger.warning(f"[Analytics] Cannot connect to SQL Server analytics DB: {exc}")
        return False


# Check availability once on module import
_available = _check_availability()


def is_available() -> bool:
    """Return True if analytics DB connection is working."""
    return _available


@contextmanager
def get_connection():
    """
    Context manager that yields a pyodbc connection.
    If analytics is unavailable, yields None so callers can skip gracefully.

    Usage:
        with get_connection() as conn:
            if conn is None:
                return
            cursor = conn.cursor()
            ...
    """
    if not _available:
        yield None
        return

    pyodbc = _try_import_pyodbc()
    if pyodbc is None:
        yield None
        return

    conn = None
    try:
        conn = pyodbc.connect(AnalyticsConfig.connection_string(), timeout=10)
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception as exc:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"[Analytics] DB error: {exc}")
        yield None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
