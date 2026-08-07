from abc import ABC, abstractmethod

from app.schema.models.schema_document import SchemaDocument
from app.schema.models.semantic_match import SemanticMatch


class BaseVectorStore(ABC):
    """
    Abstract interface for vector stores.
    """

    @abstractmethod
    def add(
        self,
        documents: list[SchemaDocument],
        embeddings: list[list[float]],
    ) -> None:
        """
        Add documents and their embeddings to the vector store.
        """
        pass

    @abstractmethod
    def search(
        self,
        embedding: list[float],
        top_k: int,
    ) -> list[SemanticMatch]:
        """
        Retrieve the most similar documents.
        """
        pass

    @abstractmethod
    def save(
        self,
        index_path: str,
        metadata_path: str,
    ) -> None:
        """
        Persist the vector index and metadata.
        """
        pass

    @abstractmethod
    def load(
        self,
        index_path: str,
        metadata_path: str,
    ) -> None:
        """
        Load the vector index and metadata.
        """
        pass

    @abstractmethod
    def exists(
        self,
        index_path: str,
        metadata_path: str,
    ) -> bool:
        """
        Return True if both the vector index and metadata exist.
        """
        pass