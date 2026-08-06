from app.schema.fusion.rrf import ReciprocalRankFusion
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever


class SchemaRetriever:
    """
    Coordinates all configured schema retrieval strategies.
    """

    def __init__(
        self,
        retrievers: list[BaseSchemaRetriever],
    ):
        self.retrievers = retrievers
        self.fusion = ReciprocalRankFusion()

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> dict:
        """
        Execute all configured retrieval strategies and
        merge their results using Reciprocal Rank Fusion (RRF).
        """

        results: list[RetrievalResult] = []

        for retriever in self.retrievers:

            result = retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )

            results.append(result)

        merged = self._merge_results(results)

        return merged.schema

    def _merge_results(
        self,
        results: list[RetrievalResult],
    ) -> RetrievalResult:
        """
        Merge retrieval results using Reciprocal Rank Fusion.
        """

        if not results:
            raise ValueError(
                "No retrieval results were produced."
            )

        return self.fusion.fuse(results)