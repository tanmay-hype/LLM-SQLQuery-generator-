from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    """
    Base interface for embedding providers.
    """

    @abstractmethod
    def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Create embeddings for a list of texts.
        """
        pass