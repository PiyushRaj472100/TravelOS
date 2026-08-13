from datetime import datetime

from pydantic import BaseModel


class TransportationOption(BaseModel):
    """
    Common model for transportation options.

    Used by:
    - Flights
    - Trains
    - Buses
    - Other transportation providers
    """

    # ---------------------------------------------
    # Basic information
    # ---------------------------------------------

    type: str
    provider: str | None = None

    # ---------------------------------------------
    # Route
    # ---------------------------------------------

    origin: str
    destination: str

    # ---------------------------------------------
    # Timing
    # ---------------------------------------------

    departure: datetime | None = None
    arrival: datetime | None = None

    duration_minutes: int | None = None

    # ---------------------------------------------
    # Stops / connections
    # ---------------------------------------------

    stops: int = 0

    # ---------------------------------------------
    # Price
    # ---------------------------------------------

    price: float | None = None
    currency: str | None = None

    # ---------------------------------------------
    # Booking / provider information
    # ---------------------------------------------

    booking_url: str | None = None
    option_id: str | None = None