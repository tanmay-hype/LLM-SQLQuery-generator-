from google import genai
from app.schema.embeddings.gemini_embedding_service import EmbeddingService
from app.core.config import settings

class GeminiEmbeddingService(EmbeddingService):
    
    def __init__(self):
        
        self.client = genai.Client(api_key=settings.gemini_api_key)
    
    """
    Gemini embedding implementation.
    """
    
    def embed(self, texts: list[str]) -> list[list[float]]:
    
        vectors = []
    
        for text in texts:
    
            response = self.client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
            )
    
            vectors.append(response.embeddings[0].values)

        return vectors
