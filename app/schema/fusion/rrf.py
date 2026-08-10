from app.schema.models.retrieval_result import RetrievalResult


class ReciprocalRankFusion:
    """
    Combines results from multiple retrieval strategies
    using Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        results: list[RetrievalResult],
    ) -> RetrievalResult:

        if not results:
            raise ValueError(
                "No retrieval results were provided."
            )

        if len(results) == 1:
            return results[0]

        fused_scores: dict[str, float] = {}
        schema_by_table: dict[str, dict] = {}

        for result in results:

            ranked_tables = sorted(
                result.scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            for rank, (table_name, _) in enumerate(
                ranked_tables,
                start=1,
            ):

                rrf_score = 1.0 / (
                    self.k + rank
                )

                fused_scores[table_name] = (
                    fused_scores.get(table_name, 0.0)
                    + rrf_score
                )

                if table_name in result.schema:
                    schema_by_table[table_name] = (
                        result.schema[table_name]
                    )

        ranked_tables = sorted(
            fused_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        merged_schema = {
            table_name: schema_by_table[table_name]
            for table_name, _ in ranked_tables
            if table_name in schema_by_table
        }

        return RetrievalResult(
            schema=merged_schema,
            scores=fused_scores,
        )