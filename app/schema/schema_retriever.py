from collections import deque

from app.core.config import settings

from app.schema.fusion.rrf import ReciprocalRankFusion
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever
from app.schema.query_expander import RetrievalQueryExpander


class SchemaRetriever:
    """
    Coordinates configured schema retrieval strategies.

    Pipeline:

        Original User Question
                ↓
        Retrieval Query Expansion
                ↓
        Individual Retrievers
                ↓
        Strong Anchor Detection
                ↓
        Reciprocal Rank Fusion
                ↓
        Anchor-Aware Seed Selection
                ↓
        Relationship-Aware Bridge Expansion
                ↓
        Final Relevant Schema

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

        self.query_expander = (
            RetrievalQueryExpander()
        )

    # ======================================================
    # PUBLIC API
    # ======================================================

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
    ) -> dict:
        """
        Execute all configured retrieval strategies.

        Retrieval process:

        1. Expand the natural-language question with retrieval
           concepts.
        2. Run every configured retrieval strategy.
        3. Detect strong deterministic / lexical anchors.
        4. Fuse retriever rankings using RRF.
        5. Preserve strong anchors as seed tables.
        6. Fill remaining Top-K capacity from the fused ranking.
        7. Add relationship bridge tables required to connect
           the selected seeds.
        8. Return the final relevant schema.

        Strong anchors are allowed to exceed the normal Top-K
        limit because explicitly relevant endpoint tables must
        not be discarded simply because another retriever ranks
        an intermediate relationship table more highly.
        """

        if not schema:
            return {}

        if not question or not question.strip():
            return {}

        retrieval_question = (
            self.query_expander.expand(
                question
            )
        )

        # --------------------------------------------------
        # Run individual retrievers
        # --------------------------------------------------

        results: list[RetrievalResult] = []

        # Strong anchors represent tables that receive a
        # deterministic relevance score at or above the
        # configured keyword retrieval threshold.
        #
        # Semantic similarity scores are normally in the
        # 0-1 range, while the deterministic keyword threshold
        # is considerably higher. This prevents ordinary
        # semantic similarity scores from being treated as
        # strong lexical anchors.
        strong_anchor_scores: dict[
            str,
            float,
        ] = {}

        for retriever in self.retrievers:

            result = retriever.retrieve(
                schema=schema,
                question=retrieval_question,
                documents=documents,
            )

            if not result.schema:
                continue

            results.append(
                result
            )

            # ----------------------------------------------
            # Detect strong anchor tables
            # ----------------------------------------------

            for (
                table_name,
                score,
            ) in result.scores.items():

                if (
                    table_name not in schema
                ):
                    continue

                if (
                    score
                    < settings.schema_retrieval_min_score
                ):
                    continue

                previous_score = (
                    strong_anchor_scores.get(
                        table_name
                    )
                )

                if (
                    previous_score is None
                    or score > previous_score
                ):
                    strong_anchor_scores[
                        table_name
                    ] = score

        if not results:
            return {}

        # --------------------------------------------------
        # Fuse retrieval rankings
        # --------------------------------------------------

        merged = self.fusion.fuse(
            results
        )

        if not merged.schema:
            return {}

        # --------------------------------------------------
        # Select seed tables
        # --------------------------------------------------

        seed_tables = (
            self._select_seed_tables(
                schema=schema,
                merged=merged,
                strong_anchor_scores=(
                    strong_anchor_scores
                ),
                top_k=(
                    settings.schema_retrieval_top_k
                ),
            )
        )

        if not seed_tables:
            return {}

        # --------------------------------------------------
        # Preserve required relationship bridge tables
        # --------------------------------------------------

        bridge_tables = (
            self._expand_bridge_tables(
                schema=schema,
                seed_tables=seed_tables,
            )
        )

        # --------------------------------------------------
        # Build final schema.
        #
        # Seed ranking order is preserved first.
        # Bridge tables are appended afterward.
        # --------------------------------------------------

        final_tables: list[str] = []

        for table_name in seed_tables:

            if (
                table_name in schema
                and table_name
                not in final_tables
            ):
                final_tables.append(
                    table_name
                )

        for table_name in bridge_tables:

            if (
                table_name in schema
                and table_name
                not in final_tables
            ):
                final_tables.append(
                    table_name
                )

        return {
            table_name: schema[
                table_name
            ]
            for table_name in final_tables
        }

    # ======================================================
    # SEED-TABLE SELECTION
    # ======================================================

    @staticmethod
    def _select_seed_tables(
        schema: dict,
        merged: RetrievalResult,
        strong_anchor_scores: dict[str, float],
        top_k: int,
    ) -> list[str]:
        """
        Select seed tables for the final schema.

        Selection policy:

        1. Preserve strong anchor tables first.
        2. Rank strong anchors by their direct relevance score.
        3. Fill remaining Top-K capacity using the fused RRF
           ranking.
        4. If the number of strong anchors itself exceeds
           Top-K, preserve all strong anchors.

        Example:

            Question:

                "Show customers and the products
                 they purchased"

            Strong anchors:

                orders      -> 19
                customers   -> 12
                products    -> 12

            Fused ranking might be:

                orders
                customers
                order_items
                products

            With Top-K = 3, ordinary truncation would remove
            products.

            Anchor-aware selection instead preserves:

                orders
                customers
                products

            Relationship expansion can then discover:

                order_items

            producing the complete path:

                customers
                    ↕
                orders
                    ↕
                order_items
                    ↕
                products
        """

        if top_k <= 0:
            return []

        # --------------------------------------------------
        # Rank strong anchors.
        #
        # Higher direct relevance scores come first.
        # Table name provides deterministic tie-breaking.
        # --------------------------------------------------

        ranked_anchors = sorted(
            strong_anchor_scores.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )

        seed_tables: list[str] = []

        for (
            table_name,
            _,
        ) in ranked_anchors:

            if table_name not in schema:
                continue

            if table_name in seed_tables:
                continue

            seed_tables.append(
                table_name
            )

        # --------------------------------------------------
        # Strong anchors are deliberately not truncated.
        #
        # If the user strongly references more tables than
        # the configured Top-K, preserving those endpoint
        # tables is safer than silently dropping one.
        # --------------------------------------------------

        remaining_capacity = max(
            0,
            top_k - len(seed_tables),
        )

        if remaining_capacity == 0:
            return seed_tables

        # --------------------------------------------------
        # Fill remaining capacity using RRF ranking.
        # --------------------------------------------------

        for table_name in (
            merged.schema.keys()
        ):

            if table_name not in schema:
                continue

            if table_name in seed_tables:
                continue

            seed_tables.append(
                table_name
            )

            remaining_capacity -= 1

            if remaining_capacity <= 0:
                break

        return seed_tables

    # ======================================================
    # BRIDGE-TABLE EXPANSION
    # ======================================================

    @classmethod
    def _expand_bridge_tables(
        cls,
        schema: dict,
        seed_tables: list[str],
    ) -> list[str]:
        """
        Add tables required to connect retrieved seed tables
        through known foreign-key relationships.

        Example:

            seed tables:

                customers
                orders
                products

            schema graph:

                customers
                    ↓
                orders
                    ↓
                order_items
                    ↓
                products

            order_items is added because it is required
            to connect orders and products.

        Directly related seed tables do not cause additional
        tables to be added.
        """

        if len(seed_tables) < 2:
            return []

        graph = (
            cls._build_relationship_graph(
                schema
            )
        )

        bridge_tables: list[str] = []

        # --------------------------------------------------
        # Examine every pair of selected seed tables.
        # --------------------------------------------------

        for (
            index,
            start_table,
        ) in enumerate(
            seed_tables
        ):

            for end_table in seed_tables[
                index + 1:
            ]:

                path = (
                    cls._find_shortest_path(
                        graph=graph,
                        start=start_table,
                        end=end_table,
                    )
                )

                if not path:
                    continue

                # ------------------------------------------
                # Only intermediate path nodes are bridges.
                #
                # Example:
                #
                # orders
                #   ↓
                # order_items
                #   ↓
                # products
                #
                # path[1:-1] -> order_items
                # ------------------------------------------

                for table_name in path[
                    1:-1
                ]:

                    if (
                        table_name
                        not in seed_tables
                        and table_name
                        not in bridge_tables
                    ):
                        bridge_tables.append(
                            table_name
                        )

        return bridge_tables

    # ======================================================
    # RELATIONSHIP GRAPH
    # ======================================================

    @staticmethod
    def _build_relationship_graph(
        schema: dict,
    ) -> dict[str, set[str]]:
        """
        Build an undirected table relationship graph
        from foreign-key metadata.

        Foreign keys are directional in PostgreSQL, but for
        schema connectivity we need to traverse relationships
        in either direction.

        Example:

            orders.customer_id -> customers.id

        becomes:

            orders <-> customers
        """

        graph: dict[
            str,
            set[str],
        ] = {
            table_name: set()
            for table_name in schema
        }

        for (
            table_name,
            table_info,
        ) in schema.items():

            foreign_keys = (
                table_info.get(
                    "foreign_keys",
                    [],
                )
            )

            for foreign_key in (
                foreign_keys
            ):

                referred_table = (
                    foreign_key.get(
                        "referred_table"
                    )
                )

                if not referred_table:
                    continue

                if (
                    referred_table
                    not in schema
                ):
                    continue

                graph[
                    table_name
                ].add(
                    referred_table
                )

                graph[
                    referred_table
                ].add(
                    table_name
                )

        return graph

    # ======================================================
    # SHORTEST PATH
    # ======================================================

    @staticmethod
    def _find_shortest_path(
        graph: dict[str, set[str]],
        start: str,
        end: str,
    ) -> list[str]:
        """
        Find the shortest relationship path between two
        database tables using breadth-first search.

        Returns an empty list when no relationship path exists.
        """

        if start not in graph:
            return []

        if end not in graph:
            return []

        if start == end:
            return [
                start
            ]

        queue = deque(
            [
                (
                    start,
                    [start],
                )
            ]
        )

        visited = {
            start
        }

        while queue:

            (
                current_table,
                path,
            ) = queue.popleft()

            for neighbor in sorted(
                graph.get(
                    current_table,
                    set(),
                )
            ):

                if neighbor in visited:
                    continue

                new_path = (
                    path
                    + [neighbor]
                )

                if neighbor == end:
                    return new_path

                visited.add(
                    neighbor
                )

                queue.append(
                    (
                        neighbor,
                        new_path,
                    )
                )

        return []