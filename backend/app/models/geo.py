from pydantic import BaseModel
from typing import Optional


class GeoLocation(BaseModel):
    name: str
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    location_type: str = "unknown"
    
    
class RoutePoint(BaseModel):
    location: GeoLocation
    order: int



class TravelLeg(BaseModel):
    from_location: GeoLocation
    to_location: GeoLocation

    order: int

    distance_km: float | None = None
    estimated_duration_minutes: int | None = None

    transportation: str | None = None

class TravelRoute(BaseModel):
    points: list[RoutePoint] = []    