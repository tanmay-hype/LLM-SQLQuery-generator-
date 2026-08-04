from app.core.config import settings

from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.models.retrieval_strategy import RetrievalStrategy

from app.schema.retrievers.keywords_retriever import KeywordRetriever


class SchemaRetriever:
    """
    Coordinates all schema retrieval strategies.
    """

    def __init__(self):

        self.strategy = RetrievalStrategy(
            settings.schema_retrieval_strategy
        )

        self.retrievers = self._build_retrievers()

    def _build_retrievers(self):
        """
        Build the retriever pipeline based on the configured strategy.
        """

        if self.strategy == RetrievalStrategy.KEYWORD:
            return [
                KeywordRetriever(),
            ]

        elif self.strategy == RetrievalStrategy.SEMANTIC:
            # Will be implemented later
            raise NotImplementedError(
                "Semantic retrieval is not implemented yet."
            )

        elif self.strategy == RetrievalStrategy.HYBRID:
            # Will be implemented later
            raise NotImplementedError(
                "Hybrid retrieval is not implemented yet."
            )

        raise ValueError(
            f"Unknown retrieval strategy: {self.strategy}"
        )

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> dict:
        """
        Execute all configured retrieval strategies.
        """

        results = []

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
        Merge retrieval results.

        Currently returns the first result.
        Later this will implement Reciprocal Rank Fusion (RRF)
        or weighted score fusion.
        """

        if not results:
            raise ValueError(
                "No retrieval results were produced."
            )

        return results[0]