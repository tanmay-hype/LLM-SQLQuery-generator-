from abc import ABC, abstractmethod
from app.schema.models.schema_document import SchemaDocument
from app.schema.models.retrieval_result import RetrievalResult

class BaseSchemaRetriever(ABC):
    """Base class for schema retrievers that retrieve prompt examples based on intent analysis."""
    @abstractmethod
    def retrieve(self, schema: dict, documents: list[SchemaDocument], question: str) -> RetrievalResult:
        """
        Retrieve the highest-scoring prompt examples based on the given analysis.
        """
        raise NotImplementedError("Subclasses must implement the retrieve method.")