from app.core.config import settings

from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.models.retrieval_strategy import RetrievalStrategy

from app.schema.retrievers.keywords_retriever import KeywordRetriever
from app.schema.retrievers.semantic_retriever import SemanticRetriever

from app.schema.fusion.rrf import ReciprocalRankFusion


class SchemaRetriever:
    """
    Coordinates keyword, semantic, and hybrid schema retrieval.
    """

    def __init__(
        self,
        embedding_service,
        vector_store,
    ):
        self.strategy = RetrievalStrategy(
            settings.schema_retrieval_strategy
        )

        self.fusion = ReciprocalRankFusion()

        self.embedding_service = embedding_service
        self.vector_store = vector_store

        self.retrievers = self._build_retrievers()

    def _build_retrievers(self):
        """
        Build retrievers according to the configured strategy.
        """

        keyword_retriever = KeywordRetriever()

        semantic_retriever = SemanticRetriever(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )

        if self.strategy == RetrievalStrategy.KEYWORD:
            return [
                keyword_retriever,
            ]

        if self.strategy == RetrievalStrategy.SEMANTIC:
            return [
                semantic_retriever,
            ]

        if self.strategy == RetrievalStrategy.HYBRID:
            return [
                keyword_retriever,
                semantic_retriever,
            ]

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
        Execute the configured retrieval strategies
        and combine their results.
        """

        results: list[RetrievalResult] = []

        for retriever in self.retrievers:

            result = retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )

            results.append(result)

        if not results:
            return {}

        merged = self.fusion.fuse(results)

        top_k = settings.schema_retrieval_top_k

        selected_tables = list(
            merged.schema.keys()
        )[:top_k]

        return {
            table_name: merged.schema[table_name]
            for table_name in selected_tables
        }

