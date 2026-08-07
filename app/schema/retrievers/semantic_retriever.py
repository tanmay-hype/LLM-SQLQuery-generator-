from app.core.config import settings

from app.schema.embeddings.base import EmbeddingService
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.models.semantic_match import SemanticMatch
from app.schema.retrievers.base import BaseSchemaRetriever
from app.schema.vector_store.base import BaseVectorStore


class SemanticRetriever(BaseSchemaRetriever):
    """
    Retrieves relevant schema using semantic similarity.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> RetrievalResult:

        embedding = self.embedding_service.create_embeddings(
            [question]
        )[0]

        matches = self.vector_store.search(
            embedding,
            settings.schema_retrieval_top_k,
        )

        selected_schema = {}

        scores = {}

        for match in matches:

            table = match.document.table_name

            if table not in schema:
                continue

            selected_schema[table] = schema[table]

            scores[table] = match.score

        return RetrievalResult(
            schema=selected_schema,
            scores=scores,
        )