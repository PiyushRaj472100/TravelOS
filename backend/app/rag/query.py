from pydantic import BaseModel, Field


class RAGQuery(BaseModel):

    question: str

    category: str | None = None

    countries: list[str] = Field(
        default_factory=list
    )

    regions: list[str] = Field(
        default_factory=list
    )

    cities: list[str] = Field(
        default_factory=list
    )

    # =================================================
    # Flight information
    # =================================================

    origin: str | None = None

    destination: str | None = None

    departure_date: str | None = None

    passengers: int = 1

    cabin_class: str = "economy"

    max_connections: int = 1

    # =================================================
    # Routing
    # =================================================

    needs_live_data: bool = False

    query_type: str = "planning"