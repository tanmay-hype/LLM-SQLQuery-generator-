from app.schema.models.retrieval_result import RetrievalResult


class ReciprocalRankFusion:
    """
    Combines results from multiple retrieval strategies
    using Reciprocal Rank Fusion (RRF).

    Only positively scored retrieval candidates contribute
    to the fused ranking.

    Tables added merely for relationship expansion with a
    score of zero are not treated as retrieval evidence.
    """

    def __init__(
        self,
        k: int = 60,
    ):
        if k <= 0:
            raise ValueError(
                "RRF k must be greater than zero."
            )

        self.k = k

    def fuse(
        self,
        results: list[RetrievalResult],
    ) -> RetrievalResult:
        """
        Combine ranked retrieval results using RRF.

        Each retrieval strategy contributes:

            1 / (k + rank)

        to the final score of a positively scored table.

        Tables occurring in multiple retrieval strategies
        therefore receive stronger fused scores.
        """

        if not results:
            raise ValueError(
                "No retrieval results were provided."
            )

        fused_scores: dict[str, float] = {}
        schema_by_table: dict[str, dict] = {}

        for result in results:

            # --------------------------------------------------
            # Only genuine retrieval matches participate.
            #
            # Some retrievers add FK-related tables with a
            # score of zero. Those tables are useful later for
            # relationship expansion but should not influence
            # relevance ranking.
            # --------------------------------------------------

            positive_scores = {
                table_name: score
                for table_name, score in result.scores.items()
                if score > 0
            }

            ranked_tables = sorted(
                positive_scores.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )

            for rank, (
                table_name,
                _,
            ) in enumerate(
                ranked_tables,
                start=1,
            ):

                contribution = (
                    1.0
                    / (
                        self.k
                        + rank
                    )
                )

                fused_scores[
                    table_name
                ] = (
                    fused_scores.get(
                        table_name,
                        0.0,
                    )
                    + contribution
                )

                if table_name in result.schema:
                    schema_by_table[
                        table_name
                    ] = result.schema[
                        table_name
                    ]

        if not fused_scores:
            return RetrievalResult(
                schema={},
                scores={},
            )

        ranked_tables = sorted(
            fused_scores.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )

        merged_schema = {
            table_name: schema_by_table[
                table_name
            ]
            for table_name, _ in ranked_tables
            if table_name in schema_by_table
        }

        ranked_scores = {
            table_name: score
            for table_name, score in ranked_tables
        }

        return RetrievalResult(
            schema=merged_schema,
            scores=ranked_scores,
        )