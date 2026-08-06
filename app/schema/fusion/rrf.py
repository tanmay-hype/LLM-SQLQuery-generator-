from collections import defaultdict

from app.schema.models.retrieval_result import RetrievalResult


class ReciprocalRankFusion:
    """
    Merge multiple retrieval results using Reciprocal Rank Fusion.
    """

    DEFAULT_K = 60

    def fuse(
        self,
        results: list[RetrievalResult],
        k: int = DEFAULT_K,
    ) -> RetrievalResult:

        fused_scores = defaultdict(float)
        merged_schema = {}

        for result in results:

            ranked_tables = sorted(
                result.scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            for rank, (table_name, _) in enumerate(ranked_tables, start=1):

                fused_scores[table_name] += 1 / (k + rank)

                if table_name in result.schema:
                    merged_schema[table_name] = result.schema[table_name]

        return RetrievalResult(
            schema=merged_schema,
            scores=dict(fused_scores),
        )