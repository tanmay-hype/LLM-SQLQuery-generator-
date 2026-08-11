from app.core.config import settings

from app.schema.fusion.rrf import ReciprocalRankFusion
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever


class SchemaRetriever:
    """
    Coordinates the configured schema retrieval strategies.

    Concrete retrievers are injected into this class.
    """

    def __init__(
        self,
        retrievers: list[BaseSchemaRetriever],
    ):
        if not retrievers:
            raise ValueError(
                "At least one schema retriever is required."
            )

        self.retrievers = retrievers
        self.fusion = ReciprocalRankFusion()

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> dict:
        """
        Execute configured retrieval strategies
        and combine their results using RRF.
        """

        results: list[RetrievalResult] = []

        for retriever in self.retrievers:

            result = retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )

            if result.schema:
                results.append(result)

        if not results:
            return {}

        # --------------------------------------------------
        # Fuse retrieval results
        # --------------------------------------------------

        merged = self.fusion.fuse(results)

        # --------------------------------------------------
        # Limit final schema
        # --------------------------------------------------

        top_k = settings.schema_retrieval_top_k

        selected_tables = list(
            merged.schema.keys()
        )[:top_k]

        return {
            table_name: merged.schema[table_name]
            for table_name in selected_tables
        }