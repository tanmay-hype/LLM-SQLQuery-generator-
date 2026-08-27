from app.core.config import settings

from app.schema.embeddings.base import EmbeddingService
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever
from app.schema.vector_store.base import BaseVectorStore


class SemanticRetriever(BaseSchemaRetriever):
    """
    Retrieves relevant schema documents using semantic similarity.

    Semantic candidates are filtered using:

        1. An absolute minimum similarity score.
        2. A maximum score gap from the strongest match.

    This prevents weak semantic matches from entering the
    hybrid retrieval pipeline simply because they happen to
    be inside the vector-search Top-K.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: BaseVectorStore,
    ):
        self.embedding_service = (
            embedding_service
        )

        self.vector_store = (
            vector_store
        )

    # ======================================================
    # PUBLIC API
    # ======================================================

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> RetrievalResult:
        """
        Retrieve the most relevant schema using embeddings.

        Process:

            Question
                ↓
            Query Embedding
                ↓
            FAISS Search
                ↓
            Absolute Score Filtering
                ↓
            Best-Score Gap Filtering
                ↓
            RetrievalResult
        """

        if not schema:
            return RetrievalResult(
                schema={},
                scores={},
            )

        if not question or not question.strip():
            return RetrievalResult(
                schema={},
                scores={},
            )

        # ==================================================
        # 1. GENERATE QUERY EMBEDDING
        # ==================================================

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

        query_embedding = (
            query_embeddings[0]
        )

        # ==================================================
        # 2. SEARCH FAISS
        # ==================================================

        matches = self.vector_store.search(
            embedding=query_embedding,
            top_k=settings.schema_retrieval_top_k,
        )

        if not matches:
            return RetrievalResult(
                schema={},
                scores={},
            )

        # ==================================================
        # 3. BUILD VALID CANDIDATES
        # ==================================================

        candidates: list[
            tuple[str, float]
        ] = []

        for match in matches:

            table_name = (
                match.document.table_name
            )

            # Ignore stale documents whose physical table
            # no longer exists in the live schema.
            if table_name not in schema:
                continue

            score = float(
                match.score
            )

            candidates.append(
                (
                    table_name,
                    score,
                )
            )

        if not candidates:
            return RetrievalResult(
                schema={},
                scores={},
            )

        # ==================================================
        # 4. SORT BY SEMANTIC SIMILARITY
        # ==================================================

        candidates.sort(
            key=lambda item: (
                -item[1],
                item[0],
            )
        )

        best_score = (
            candidates[0][1]
        )

        # ==================================================
        # 5. FILTER CANDIDATES
        # ==================================================

        selected_schema: dict = {}

        scores: dict[str, float] = {}

        for (
            table_name,
            score,
        ) in candidates:

            # ----------------------------------------------
            # Absolute similarity threshold
            # ----------------------------------------------

            if (
                score
                < settings.schema_semantic_min_score
            ):
                continue

            # ----------------------------------------------
            # Relative-to-best score-gap threshold
            #
            # Example:
            #
            # products      = 0.74
            # order_items   = 0.61
            #
            # Gap = 0.13
            #
            # With max gap 0.10, order_items is rejected.
            # ----------------------------------------------

            score_gap = (
                best_score
                - score
            )

            if (
                score_gap
                > settings.schema_semantic_max_score_gap
            ):
                continue

            selected_schema[
                table_name
            ] = schema[
                table_name
            ]

            scores[
                table_name
            ] = score

        # ==================================================
        # 6. SAFETY FALLBACK
        # ==================================================

        # If filtering removed every candidate but FAISS
        # returned a valid physical table, preserve the best
        # candidate only.
        #
        # This avoids semantic retrieval disappearing entirely
        # because of an unusually low-score question.
        if (
            not selected_schema
            and candidates
        ):

            (
                best_table,
                best_table_score,
            ) = candidates[0]

            if best_table in schema:

                selected_schema[
                    best_table
                ] = schema[
                    best_table
                ]

                scores[
                    best_table
                ] = best_table_score

        return RetrievalResult(
            schema=selected_schema,
            scores=scores,
        )