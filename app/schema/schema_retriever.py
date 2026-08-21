from collections import deque

from app.core.config import settings

from app.schema.fusion.rrf import ReciprocalRankFusion
from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever


class SchemaRetriever:
    """
    Coordinates configured schema retrieval strategies.

    Pipeline:

        Individual Retrievers
                ↓
        Reciprocal Rank Fusion
                ↓
        Top-K Seed Tables
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
        Execute all configured retrieval strategies,
        combine their results with Reciprocal Rank Fusion,
        select the highest-ranked seed tables, and preserve
        any FK bridge tables required to connect those seeds.
        """

        if not schema:
            return {}

        if not question or not question.strip():
            return {}

        # --------------------------------------------------
        # Run individual retrievers
        # --------------------------------------------------

        results: list[RetrievalResult] = []

        for retriever in self.retrievers:

            result = retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )

            if result.schema:
                results.append(
                    result
                )

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
        # Select top-K seed tables
        # --------------------------------------------------

        top_k = settings.schema_retrieval_top_k

        seed_tables = list(
            merged.schema.keys()
        )[:top_k]

        # --------------------------------------------------
        # Preserve required relationship bridge tables
        # --------------------------------------------------

        expanded_tables = (
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
                and table_name not in final_tables
            ):
                final_tables.append(
                    table_name
                )

        for table_name in expanded_tables:

            if (
                table_name in schema
                and table_name not in final_tables
            ):
                final_tables.append(
                    table_name
                )

        return {
            table_name: schema[table_name]
            for table_name in final_tables
        }

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

        graph = cls._build_relationship_graph(
            schema
        )

        bridge_tables: list[str] = []

        # --------------------------------------------------
        # Examine every pair of selected seed tables.
        # --------------------------------------------------

        for index, start_table in enumerate(
            seed_tables
        ):

            for end_table in seed_tables[
                index + 1:
            ]:

                path = cls._find_shortest_path(
                    graph=graph,
                    start=start_table,
                    end=end_table,
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

                for table_name in path[1:-1]:

                    if (
                        table_name not in seed_tables
                        and table_name not in bridge_tables
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

        graph: dict[str, set[str]] = {
            table_name: set()
            for table_name in schema
        }

        for table_name, table_info in schema.items():

            foreign_keys = table_info.get(
                "foreign_keys",
                [],
            )

            for foreign_key in foreign_keys:

                referred_table = foreign_key.get(
                    "referred_table"
                )

                if not referred_table:
                    continue

                if referred_table not in schema:
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

            current_table, path = (
                queue.popleft()
            )

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