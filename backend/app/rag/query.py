from pydantic import BaseModel, Field


class RAGQuery(BaseModel):

    question: str

    category: str | None = None

    countries: list[str] = Field(default_factory=list)

    regions: list[str] = Field(default_factory=list)

    cities: list[str] = Field(default_factory=list)

    needs_live_data: bool = False