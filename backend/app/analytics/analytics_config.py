"""
TravelOS Analytics -- SQL Server Configuration

Reads connection details from environment variables.
Never stores credentials in code.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class AnalyticsConfig:
    """SQL Server analytics database connection configuration."""

    # ----------------------------------------------------------------
    # Connection parameters -- all from environment variables
    # ----------------------------------------------------------------

    SQL_SERVER_HOST: str     = os.getenv("SQL_SERVER_HOST", "localhost")
    SQL_SERVER_PORT: int     = int(os.getenv("SQL_SERVER_PORT", "1433"))
    SQL_SERVER_DATABASE: str = os.getenv("SQL_SERVER_DATABASE", "TravelOS_Analytics")
    SQL_SERVER_USER: str     = os.getenv("SQL_SERVER_USER", "")
    SQL_SERVER_PASSWORD: str = os.getenv("SQL_SERVER_PASSWORD", "")

    # Optionally use a full connection string instead of individual parts
    ANALYTICS_CONNECTION_STRING: str = os.getenv(
        "ANALYTICS_SQLSERVER_CONNECTION_STRING", ""
    )

    # Driver -- installed on the system with ODBC Driver for SQL Server
    ODBC_DRIVER: str = os.getenv("SQL_SERVER_ODBC_DRIVER", "ODBC Driver 17 for SQL Server")

    # Whether analytics tracking is enabled at all
    # Set ANALYTICS_ENABLED=false to disable without removing code
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"

    @classmethod
    def connection_string(cls) -> str:
        """Build pyodbc connection string from config."""
        if cls.ANALYTICS_CONNECTION_STRING:
            return cls.ANALYTICS_CONNECTION_STRING

        parts = [
            f"DRIVER={{{cls.ODBC_DRIVER}}}",
            f"SERVER={cls.SQL_SERVER_HOST},{cls.SQL_SERVER_PORT}",
            f"DATABASE={cls.SQL_SERVER_DATABASE}",
        ]

        if cls.SQL_SERVER_USER and cls.SQL_SERVER_PASSWORD:
            parts += [
                f"UID={cls.SQL_SERVER_USER}",
                f"PWD={cls.SQL_SERVER_PASSWORD}",
            ]
        else:
            # Windows Integrated Security (for local dev)
            parts.append("Trusted_Connection=yes")

        parts.append("TrustServerCertificate=yes")
        return ";".join(parts)

    @classmethod
    def is_configured(cls) -> bool:
        """Return True if analytics DB credentials are present."""
        has_full_conn = bool(cls.ANALYTICS_CONNECTION_STRING)
        has_parts = bool(cls.SQL_SERVER_HOST and cls.SQL_SERVER_DATABASE)
        return has_full_conn or has_parts
