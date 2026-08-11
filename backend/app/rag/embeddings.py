from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY


class EmbeddingService:

    def __init__(self):

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        self.model = "gemini-embedding-001"

    def embed_document(
        self,
        text: str
    ) -> list[float]:

        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            )
        )

        return response.embeddings[0].values

    def embed_query(
        self,
        text: str
    ) -> list[float]:

        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )

        return response.embeddings[0].values