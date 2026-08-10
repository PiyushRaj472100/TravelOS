from typing import Optional, List

from pydantic import BaseModel, Field


class TravelExtraction(BaseModel):
    origin: Optional[str] = Field(
        default=None,
        description="The user's starting location if explicitly mentioned."
    )

    destinations: List[str] = Field(
        default_factory=list,
        description="Countries, states, regions, or cities the user explicitly wants to visit."
    )

    duration_days: Optional[int] = Field(
        default=None,
        description="Trip duration in days if explicitly mentioned."
    )

    start_date: Optional[str] = Field(
        default=None,
        description="Trip start date if explicitly mentioned."
    )

    end_date: Optional[str] = Field(
        default=None,
        description="Trip end date if explicitly mentioned."
    )

    travelers: Optional[int] = Field(
        default=None,
        description="Number of travelers if explicitly mentioned."
    )

    traveler_type: Optional[str] = Field(
        default=None,
        description="Type of travelers such as solo, couple, family, or friends."
    )

    budget: Optional[float] = Field(
        default=None,
        description="Total trip budget if explicitly mentioned."
    )

    currency: Optional[str] = Field(
        default=None,
        description="Currency associated with the budget, such as INR, USD, or EUR."
    )

    interests: List[str] = Field(
        default_factory=list,
        description="Travel interests explicitly mentioned by the user."
    )

    pace: Optional[str] = Field(
        default=None,
        description="Travel pace if explicitly mentioned, such as relaxed, balanced, or packed."
    )

    accommodation_preference: Optional[str] = Field(
        default=None,
        description="Accommodation preference if explicitly mentioned."
    )

    transportation_preference: Optional[str] = Field(
        default=None,
        description="Preferred transportation if explicitly mentioned."
    )

    food_preferences: List[str] = Field(
        default_factory=list,
        description="Food or cuisine preferences explicitly mentioned."
    )