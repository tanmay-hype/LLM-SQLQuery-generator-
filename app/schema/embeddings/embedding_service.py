from abc import ABC, abstractmethod

class EmbeddingService(ABC):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    def embed(self, text: list[str]) -> list[list[float]]:
        """
        convert text into embeddings.
        """
        pass