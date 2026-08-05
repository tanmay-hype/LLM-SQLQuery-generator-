from app.core.config import settings
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever
from app.schema.indexing.schema_index_service import SchemaIndexService


class SemanticRetriever(BaseSchemaRetriever):
    """
    Implements semantic retrieval strategy for schema documents.
    """
    def __init__(self, index_service: SchemaIndexService):
        self.index_service = index_service

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
        top_k: int = settings.schema_retriever_top_k
    ) -> RetrievalResult:
        """
        Retrieve the highest-scoring prompt examples based on semantic analysis.
        """
        matches = self.index_service.search(question=question, top_k=top_k)
        
        selected_schema = {}
        scores = {}
        
        for match in matches:
            table_name = match.document.table_name
            if table_name in schema:
                selected_schema[table_name] = schema[table_name]
                scores[table_name] = match.score
        
        return RetrievalResult(
            schema=selected_schema,
            scores=scores
        )
      