import re

from app.core.config import settings

from app.schema.models.retrieval_result import RetrievalResult
from app.schema.models.schema_document import SchemaDocument
from app.schema.retrievers.base import BaseSchemaRetriever


class KeywordRetriever(BaseSchemaRetriever):
    """
    Retrieves relevant database tables using keyword matching
    against table names and column names.
    """

    # --------------------------------------------------
    # Scoring
    # --------------------------------------------------

    TABLE_EXACT_MATCH = 10
    TABLE_PARTIAL_MATCH = 5

    COLUMN_EXACT_MATCH = 6
    COLUMN_PARTIAL_MATCH = 3

    # --------------------------------------------------
    # Retrieval
    # --------------------------------------------------

    def retrieve(
        self,
        schema: dict,
        question: str,
        documents: list[SchemaDocument],
        top_k: int | None = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant tables using keyword matching.

        Process:

        1. Tokenize the question.
        2. Score tables and columns.
        3. Select the highest-scoring tables.
        4. Expand only one level through foreign-key relationships.
        5. Return the selected schema and scores.
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

        if top_k is None:
            top_k = settings.schema_retrieval_top_k

        tokens = self._tokenize(question)

        scores = self._score_tables(
            schema=schema,
            tokens=tokens,
        )

        selected_tables = self._select_tables(
            schema=schema,
            scores=scores,
            top_k=top_k,
        )

        # --------------------------------------------------
        # Foreign-key expansion
        # --------------------------------------------------

        expanded_tables = self._expand_related_tables(
            schema=schema,
            selected_tables=set(selected_tables),
        )

        final_schema = {
            table_name: schema[table_name]
            for table_name in expanded_tables
            if table_name in schema
        }

        # Directly matched tables retain their score.
        # FK-expanded tables receive a score of zero.
        final_scores = {
            table_name: scores.get(table_name, 0)
            for table_name in final_schema
        }

        return RetrievalResult(
            schema=final_schema,
            scores=final_scores,
        )

    # --------------------------------------------------
    # Tokenization
    # --------------------------------------------------

    @staticmethod
    def _tokenize(question: str) -> list[str]:
        """
        Convert the question into normalized tokens.

        Example:

            "Show customer names and email addresses"

        becomes approximately:

            ["show", "customer", "names", "and",
             "email", "addresses"]
        """

        return re.findall(
            r"\w+",
            question.lower(),
        )

    # --------------------------------------------------
    # Scoring
    # --------------------------------------------------

    def _score_tables(
        self,
        schema: dict,
        tokens: list[str],
    ) -> dict[str, int]:
        """
        Calculate relevance scores for every table.
        """

        scores: dict[str, int] = {}

        for table_name, table_info in schema.items():

            score = 0

            # Table-name matching
            score += self._table_score(
                table_name=table_name,
                tokens=tokens,
            )

            # Column-name matching
            score += self._column_score(
                columns=table_info.get("columns", []),
                tokens=tokens,
            )

            if score > 0:
                scores[table_name] = score

        return scores

    # --------------------------------------------------
    # Table Selection
    # --------------------------------------------------

    def _select_tables(
        self,
        schema: dict,
        scores: dict[str, int],
        top_k: int,
    ) -> set[str]:
        """
        Select the highest-scoring tables.

        Only tables meeting the minimum relevance score
        are selected.

        If no table reaches the minimum score, return an
        empty set and allow semantic retrieval to contribute
        in hybrid mode.
        """

        min_score = settings.schema_retrieval_min_score

        filtered_scores = {
            table_name: score
            for table_name, score in scores.items()
            if score >= min_score
        }

        if not filtered_scores:
            return set()

        ranked_tables = sorted(
            filtered_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return {
            table_name
            for table_name, _ in ranked_tables[:top_k]
        }

    # --------------------------------------------------
    # Table Scoring
    # --------------------------------------------------

    def _table_score(
        self,
        table_name: str,
        tokens: list[str],
    ) -> int:
        """
        Score a table based on table-name matches.
        """

        score = 0

        normalized_table_name = table_name.lower()

        # Treat underscores as word separators.
        table_tokens = set(
            re.findall(
                r"\w+",
                normalized_table_name.replace("_", " "),
            )
        )

        for token in tokens:

            if token in table_tokens:
                score += self.TABLE_EXACT_MATCH

            elif token in normalized_table_name:
                score += self.TABLE_PARTIAL_MATCH

        return score

    # --------------------------------------------------
    # Column Scoring
    # --------------------------------------------------

    def _column_score(
        self,
        columns: list[dict],
        tokens: list[str],
    ) -> int:
        """
        Score a table based on column-name matches.
        """

        score = 0

        for column in columns:

            column_name = column.get("name")

            if not column_name:
                continue

            normalized_column_name = column_name.lower()

            column_tokens = set(
                re.findall(
                    r"\w+",
                    normalized_column_name.replace("_", " "),
                )
            )

            for token in tokens:

                if token in column_tokens:
                    score += self.COLUMN_EXACT_MATCH

                elif token in normalized_column_name:
                    score += self.COLUMN_PARTIAL_MATCH

        return score

    # --------------------------------------------------
    # Foreign-Key Expansion
    # --------------------------------------------------

    @staticmethod
    def _expand_related_tables(
        schema: dict,
        selected_tables: set[str],
    ) -> set[str]:
        """
        Expand selected tables by one level through
        foreign-key relationships.

        Example:

            orders -> customers

        If "orders" is selected, "customers" is added.

        If "customers" is selected and orders references
        customers, "orders" is added.

        Only one FK level is expanded.
        """

        if not selected_tables:
            return set()

        expanded = set(selected_tables)

        for table_name in selected_tables:

            table_info = schema.get(
                table_name,
                {},
            )

            foreign_keys = table_info.get(
                "foreign_keys",
                [],
            )

            for foreign_key in foreign_keys:

                referred_table = foreign_key.get(
                    "referred_table"
                )

                if (
                    referred_table
                    and referred_table in schema
                ):
                    expanded.add(
                        referred_table
                    )

        # Also find tables that reference the selected
        # tables.
        for table_name, table_info in schema.items():

            foreign_keys = table_info.get(
                "foreign_keys",
                [],
            )

            for foreign_key in foreign_keys:

                referred_table = foreign_key.get(
                    "referred_table"
                )

                if referred_table in selected_tables:
                    expanded.add(table_name)

        return expanded
