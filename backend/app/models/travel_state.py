from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TravelState(BaseModel):
    # Basic trip information
    origin: Optional[str] = None

    destinations: List[str] = Field(default_factory=list)
    countries: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)

    # Time
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: Optional[int] = None

    # Travelers
    travelers: Optional[int] = None
    traveler_type: Optional[str] = None

    # Budget
    budget: Optional[float] = None
    currency: Optional[str] = None

    # Preferences
    interests: List[str] = Field(default_factory=list)
    travel_style: Optional[str] = None
    pace: Optional[str] = None
    accommodation_preference: Optional[str] = None
    transportation_preference: Optional[str] = None
    food_preferences: List[str] = Field(default_factory=list)

    # Generated trip information
    itinerary: List[Dict[str, Any]] = Field(default_factory=list)
    routes: List[Dict[str, Any]] = Field(default_factory=list)

    # Recommendations
    hotels: List[Dict[str, Any]] = Field(default_factory=list)
    restaurants: List[Dict[str, Any]] = Field(default_factory=list)
    activities: List[Dict[str, Any]] = Field(default_factory=list)
    transport_options: List[Dict[str, Any]] = Field(default_factory=list)

    # Additional travel information
    weather: Dict[str, Any] = Field(default_factory=dict)
    packing_list: List[str] = Field(default_factory=list)
    travel_rules: List[Dict[str, Any]] = Field(default_factory=list)

    # Current UI/trip context
    current_day: Optional[int] = None
    selected_location: Optional[Dict[str, Any]] = None
    selected_route: Optional[Dict[str, Any]] = None