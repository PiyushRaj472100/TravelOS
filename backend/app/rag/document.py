from datetime import datetime

from pydantic import BaseModel


class RAGDocument(BaseModel):

    # ---------------------------------------------
    # Main knowledge content
    # ---------------------------------------------

    text: str

    title: str | None = None


    # ---------------------------------------------
    # Geographic metadata
    # ---------------------------------------------

    country: str | None = None

    region: str | None = None

    city: str | None = None


    # ---------------------------------------------
    # Knowledge category
    # ---------------------------------------------

    category: str | None = None


    # ---------------------------------------------
    # Source / provenance
    # ---------------------------------------------

    source: str | None = None

    source_url: str | None = None

    fallback_search_url: str | None = None


    # ---------------------------------------------
    # Freshness
    # ---------------------------------------------

    last_updated: datetime | None = None


    # ---------------------------------------------
    # Optional document identifier
    # ---------------------------------------------

    document_id: str | None = None