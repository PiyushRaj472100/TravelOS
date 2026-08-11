from pydantic import BaseModel


class RAGDocument(BaseModel):
    text: str

    country: str | None = None
    region: str | None = None
    city: str | None = None

    category: str | None = None

    source: str | None = None
    title: str | None = None