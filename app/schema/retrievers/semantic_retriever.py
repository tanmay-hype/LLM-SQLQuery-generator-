from app.core.config import settings

from app.schema.embeddings.base import EmbeddingService
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever
from app.schema.vector_store.base import BaseVectorStore


class SemanticRetriever(BaseSchemaRetriever):
    """
    Retrieves relevant schema documents using semantic similarity.
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
        """
        Retrieve the most relevant schema using embeddings.
        """

        if not question or not question.strip():
            return RetrievalResult(
                schema={},
                scores={},
            )

        # --------------------------------------------------
        # Generate query embedding
        # --------------------------------------------------

        query_embeddings = (
            self.embedding_service.create_embeddings(
                [question]
            )
        )

        if not query_embeddings:
            return RetrievalResult(
                schema={},
                scores={},
            )

        query_embedding = query_embeddings[0]

        # --------------------------------------------------
        # Search FAISS
        # --------------------------------------------------

        matches = self.vector_store.search(
            embedding=query_embedding,
            top_k=settings.schema_retrieval_top_k,
        )

        # --------------------------------------------------
        # Convert matches into RetrievalResult
        # --------------------------------------------------

        selected_schema: dict = {}
        scores: dict[str, float] = {}

        for match in matches:

            table_name = match.document.table_name

            # Ignore documents that no longer exist
            # in the current database schema.
            if table_name not in schema:
                continue

            selected_schema[table_name] = schema[
                table_name
            ]

            scores[table_name] = float(
                match.score
            )

        return RetrievalResult(
            schema=selected_schema,
            scores=scores,
        )
