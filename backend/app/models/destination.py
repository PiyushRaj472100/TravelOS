from pydantic import BaseModel, Field


class DestinationPlace(BaseModel):

    # =================================================
    # Basic Information
    # =================================================

    name: str

    place_type: str = "attraction"

    description: str | None = None


    # =================================================
    # Location
    # =================================================

    city: str | None = None

    country: str | None = None

    latitude: float | None = None

    longitude: float | None = None


    # =================================================
    # Visual Information
    # =================================================

    image_url: str | None = None


    # =================================================
    # External Links
    # =================================================

    website_url: str | None = None

    map_url: str | None = None


    # =================================================
    # Ratings
    # =================================================

    rating: float | None = None

    review_count: int | None = None


    # =================================================
    # Practical Information
    # =================================================

    opening_hours: list[str] = Field(
        default_factory=list
    )

    price_level: str | None = None


    # =================================================
    # Categories
    # =================================================

    categories: list[str] = Field(
        default_factory=list
    )


    # =================================================
    # Source
    # =================================================

    source: str | None = None

    source_id: str | None = None