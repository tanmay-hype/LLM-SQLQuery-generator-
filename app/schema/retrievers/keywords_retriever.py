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
        Retrieve the most relevant tables from the schema.

        The retrieval process is:

        1. Tokenize the question.
        2. Score tables and columns.
        3. Select the highest-scoring tables.
        4. Expand selection using foreign-key relationships.
        5. Return the resulting schema with retrieval scores.
        """

        if not schema:
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

        selected_schema = self._select_tables(
            schema=schema,
            scores=scores,
            top_k=top_k,
        )

        # --------------------------------------------------
        # Expand through foreign-key relationships
        # --------------------------------------------------

        selected_tables = self._expand_related_tables(
            schema=schema,
            selected_tables=set(selected_schema.keys()),
        )

        final_schema = {
            table_name: schema[table_name]
            for table_name in selected_tables
            if table_name in schema
        }

        # Keep the selected table scores.
        # Tables added through FK expansion receive a score
        # of zero because they were not directly matched.
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
    def _tokenize(
        question: str,
    ) -> list[str]:
        """
        Convert the question into normalized tokens.
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
    ) -> dict:
        """
        Select the highest-scoring tables.

        Tables below the configured minimum score are ignored.

        If no tables pass the minimum score, fall back to the
        first top_k tables so the pipeline still has schema
        information available.
        """

        min_score = settings.schema_retrieval_min_score

        filtered_scores = {
            table_name: score
            for table_name, score in scores.items()
            if score >= min_score
        }

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        if not filtered_scores:
            fallback_tables = list(schema.keys())[:top_k]

            return {
                table_name: schema[table_name]
                for table_name in fallback_tables
            }

        # --------------------------------------------------
        # Rank tables
        # --------------------------------------------------

        ranked_tables = sorted(
            filtered_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        selected = {}

        for table_name, _ in ranked_tables[:top_k]:
            selected[table_name] = schema[table_name]

        return selected

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

        for token in tokens:

            if token == normalized_table_name:
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

            for token in tokens:

                if token == normalized_column_name:
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
        Expand the selected tables using foreign-key relationships.

        If:

            orders -> customers

        and either `orders` or `customers` is selected,
        the related table is also included.
        """

        expanded = set(selected_tables)

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

                # Current table references a selected table.
                if (
                    table_name in selected_tables
                    and referred_table in schema
                ):
                    expanded.add(referred_table)

                # Current table is referenced by a selected table.
                if (
                    referred_table in selected_tables
                    and table_name in schema
                ):
                    expanded.add(table_name)

        return expanded

