from typing import List, Optional, Any, Dict

from pydantic import BaseModel, Field


# =================================================
# Request
# =================================================

class ChatRequest(BaseModel):

    message: str

    session_id: Optional[str] = None


# =================================================
# Source
# =================================================

class ChatSource(BaseModel):

    title: Optional[str] = None

    source: Optional[str] = None

    source_url: Optional[str] = None

    fallback_search_url: Optional[str] = None

    country: Optional[str] = None

    region: Optional[str] = None

    city: Optional[str] = None

    category: Optional[str] = None

    score: Optional[float] = None


# =================================================
# Agent Status
# =================================================

class AgentStatus(BaseModel):

    agent: str

    status: str  # "working" | "done" | "failed" | "skipped"

    message: Optional[str] = None


# =================================================
# Budget Breakdown
# =================================================

class BudgetItem(BaseModel):

    label: str

    amount: Optional[float] = None

    currency: Optional[str] = None

    is_live: bool = False


class BudgetBreakdown(BaseModel):

    total_budget: Optional[float] = None

    currency: Optional[str] = None

    flights: Optional[float] = None

    hotels: Optional[float] = None

    food: Optional[float] = None

    activities: Optional[float] = None

    transport: Optional[float] = None

    remaining: Optional[float] = None

    cost_per_day: Optional[float] = None

    cost_per_person: Optional[float] = None

    duration_days: Optional[int] = None

    travelers: Optional[int] = None

    items: List[BudgetItem] = Field(default_factory=list)

    note: Optional[str] = None


# =================================================
# Map Data
# =================================================

class MapMarker(BaseModel):

    id: str

    name: str

    latitude: float

    longitude: float

    marker_type: str  # "destination" | "hotel" | "activity" | "restaurant" | "airport"

    day: Optional[int] = None

    description: Optional[str] = None


class MapRoute(BaseModel):

    from_name: str

    to_name: str

    from_lat: float

    from_lng: float

    to_lat: float

    to_lng: float

    transport_type: str  # "flight" | "train" | "drive" | "walk"

    order: int


class MapData(BaseModel):

    markers: List[MapMarker] = Field(default_factory=list)

    routes: List[MapRoute] = Field(default_factory=list)

    center_lat: Optional[float] = None

    center_lng: Optional[float] = None

    zoom: Optional[int] = None


# =================================================
# Enriched Chat Response
# =================================================

class ChatResponse(BaseModel):

    session_id: str

    message: str

    missing_information: List[str] = Field(default_factory=list)

    travel_state: dict = Field(default_factory=dict)

    sources: List[ChatSource] = Field(default_factory=list)

    # Agent activity
    agent_statuses: List[AgentStatus] = Field(default_factory=list)

    # Live data results
    flights: List[Dict[str, Any]] = Field(default_factory=list)

    hotels: List[Dict[str, Any]] = Field(default_factory=list)

    weather: Optional[Dict[str, Any]] = None

    currency: Optional[Dict[str, Any]] = None

    # Generated trip content
    activities: List[Dict[str, Any]] = Field(default_factory=list)

    itinerary: List[Dict[str, Any]] = Field(default_factory=list)

    budget: Optional[BudgetBreakdown] = None

    # Map rendering data
    map_data: Optional[MapData] = None

    # CTA action signal for frontend (e.g. "generate_itinerary")
    cta_action: Optional[str] = None