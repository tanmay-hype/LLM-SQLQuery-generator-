from google import genai

from app.core.config import settings
from app.schema.embeddings.base import EmbeddingService


class GeminiEmbeddingService(EmbeddingService):
    """
    Gemini embedding implementation.
    """

    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key,
        )

    def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for the supplied texts.
        """

        if not texts:
            return []

        embeddings = []

        for text in texts:

            response = self.client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
            )

            embeddings.append(
                response.embeddings[0].values
            )

        return embeddings