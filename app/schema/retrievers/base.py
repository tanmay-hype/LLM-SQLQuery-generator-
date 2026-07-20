from abc import ABC, abstractmethod

class BaseSchemaRetriever(ABC):
    """Base class for schema retrievers that retrieve prompt examples based on intent analysis."""
    @abstractmethod
    def retrieve(self, schema: dict, question: str) -> dict:
        """
        Retrieve the highest-scoring prompt examples based on the given analysis.
        """
        raise NotImplementedError("Subclasses must implement the retrieve method.")