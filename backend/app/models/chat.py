from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):

    message: str

    session_id: Optional[str] = None


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


class ChatResponse(BaseModel):

    session_id: str

    message: str

    missing_information: List[str]

    travel_state: dict

    sources: List[ChatSource] = []