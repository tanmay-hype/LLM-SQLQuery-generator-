from app.schema.embeddings.gemini_embedding_service import EmbeddingService

class GeminiEmbeddingService(EmbeddingService):
    """
    Gemini embedding implementation.
    """
    def embed(self, text: list[str]) -> list[list[float]]:
        raise NotImplementedError("Gemini embedding service is not implemented yet.")
    
