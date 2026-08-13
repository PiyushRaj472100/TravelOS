from datetime import datetime

from pydantic import BaseModel


class TransportationOption(BaseModel):
    """
    Standard representation of a travel transportation option.

    This model is provider-independent.
    Flights, trains, buses, etc. can all eventually
    be converted into this same structure.
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
    # Schedule
    # ---------------------------------------------

    departure: datetime | None = None
    arrival: datetime | None = None

    duration_minutes: int | None = None

    # ---------------------------------------------
    # Connections
    # ---------------------------------------------

    stops: int = 0

    # ---------------------------------------------
    # Price
    # ---------------------------------------------

    price: float | None = None
    currency: str | None = None

    # ---------------------------------------------
    # External reference
    # ---------------------------------------------

    booking_url: str | None = None

    # ---------------------------------------------
    # Provider-specific identifier
    # ---------------------------------------------

    option_id: str | None = None