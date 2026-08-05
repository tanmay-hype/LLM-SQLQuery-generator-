from abc import ABC, abstractmethod
from app.schema.models.schema_document import SchemaDocument
from app.schema.models.semantic_match import SemanticMatch

class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def index(self, documents: list[SchemaDocument], embeddings: list[list[float]]):
        """
        Add documents to the vector store.
        """
        pass

    @abstractmethod
    def search(self, embedding: list[float], top_k: int) -> list[SemanticMatch]:
        """
        Query the vector store for the top_k most similar documents to the given query vector.
        """
        pass