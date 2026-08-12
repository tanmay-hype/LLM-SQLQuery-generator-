import re

from app.models.intent_analysis import IntentAnalysis
from app.models.intent import QueryIntent


class SchemaCompressor:
    """
    Compresses database schema information before it is
    sent to the LLM.

    The goal is to preserve columns that are important for:

    - SELECT operations
    - WHERE filtering
    - JOIN operations
    - GROUP BY operations
    - ORDER BY operations
    - Aggregations
    - Time-series queries
    - Primary keys
    - Foreign keys

    while removing irrelevant columns to reduce prompt size.
    """

    # --------------------------------------------------
    # Commonly useful columns
    # --------------------------------------------------

    COMMON_COLUMNS = {
        "name",
        "title",
        "status",
        "type",
        "category",
        "amount",
        "price",
        "quantity",
        "date",
        "created_at",
        "updated_at",
    }

    # --------------------------------------------------
    # Aggregation-related column names
    # --------------------------------------------------

    AGGREGATION_KEYWORDS = {
        "amount",
        "price",
        "cost",
        "total",
        "quantity",
        "count",
        "salary",
        "revenue",
    }

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def compress(
        self,
        schema: dict,
        question: str,
        intent: IntentAnalysis,
    ) -> dict:
        """
        Compress the supplied schema according to the
        user's question and detected intent.

        Parameters
        ----------
        schema:
            Relevant schema returned by SchemaRetriever.

        question:
            Original natural-language question.

        intent:
            Result produced by IntentDetector.

        Returns
        -------
        dict
            Compressed schema suitable for prompt generation.
        """

        if not schema:
            return {}

        tokens = self._tokenize(question)

        compressed = {}

        for table_name, table in schema.items():

            compressed[table_name] = self._compress_table(
                table=table,
                tokens=tokens,
                intent=intent,
            )

        return compressed

    # --------------------------------------------------
    # Tokenization
    # --------------------------------------------------

    @staticmethod
    def _tokenize(
        question: str,
    ) -> set[str]:
        """
        Convert the question into normalized tokens.
        """

        return set(
            re.findall(
                r"\w+",
                question.lower(),
            )
        )

    # --------------------------------------------------
    # Table Compression
    # --------------------------------------------------

    def _compress_table(
        self,
        table: dict,
        tokens: set[str],
        intent: IntentAnalysis,
    ) -> dict:
        """
        Compress a single table while preserving
        structurally important information.
        """

        original_columns = table.get(
            "columns",
            [],
        )

        kept_columns = [
            column
            for column in original_columns
            if self._keep_column(
                column=column,
                table=table,
                tokens=tokens,
                intent=intent,
            )
        ]

        # --------------------------------------------------
        # Safety fallback
        # --------------------------------------------------

        # If nothing matched, preserve a small number of
        # columns rather than sending an empty table schema.
        if not kept_columns:
            kept_columns = original_columns[:3]

        return {
            "columns": kept_columns,
            "primary_keys": table.get(
                "primary_keys",
                {},
            ),
            "foreign_keys": table.get(
                "foreign_keys",
                [],
            ),
        }

    # --------------------------------------------------
    # Column Selection
    # --------------------------------------------------

    def _keep_column(
        self,
        column: dict,
        table: dict,
        tokens: set[str],
        intent: IntentAnalysis,
    ) -> bool:
        """
        Determine whether a column should be preserved.
        """

        name = column.get("name")

        if not name:
            return False

        name = name.lower()

        # --------------------------------------------------
        # 1. Direct question match
        # --------------------------------------------------

        if name in tokens:
            return True

        # --------------------------------------------------
        # 2. Primary key
        # --------------------------------------------------

        primary_keys = table.get(
            "primary_keys",
            {},
        )

        constrained_columns = primary_keys.get(
            "constrained_columns",
            [],
        )

        if name in {
            column.lower()
            for column in constrained_columns
        }:
            return True

        # --------------------------------------------------
        # 3. Foreign key
        # --------------------------------------------------

        for foreign_key in table.get(
            "foreign_keys",
            [],
        ):

            constrained_columns = foreign_key.get(
                "constrained_columns",
                [],
            )

            if name in {
                column.lower()
                for column in constrained_columns
            }:
                return True

        # --------------------------------------------------
        # 4. Identifier columns
        # --------------------------------------------------

        if name == "id":
            return True

        if name.endswith("_id"):
            return True

        # --------------------------------------------------
        # 5. Common useful columns
        # --------------------------------------------------

        if name in self.COMMON_COLUMNS:
            return True

        # --------------------------------------------------
        # 6. Time-series intent
        # --------------------------------------------------

        if intent.primary == QueryIntent.TIME_SERIES:

            if any(
                keyword in name
                for keyword in (
                    "date",
                    "time",
                    "month",
                    "year",
                )
            ):
                return True

        # --------------------------------------------------
        # 7. Aggregation intent
        # --------------------------------------------------

        if intent.primary == QueryIntent.AGGREGATION:

            if any(
                keyword in name
                for keyword in self.AGGREGATION_KEYWORDS
            ):
                return True

        # --------------------------------------------------
        # 8. Group-by intent
        # --------------------------------------------------

        if intent.primary == QueryIntent.GROUP_BY:

            if name in {
                "name",
                "title",
                "category",
                "type",
                "status",
                "city",
                "country",
                "date",
            }:
                return True

        # --------------------------------------------------
        # 9. Sort intent
        # --------------------------------------------------

        if intent.primary == QueryIntent.SORT:

            if any(
                keyword in name
                for keyword in (
                    "amount",
                    "price",
                    "total",
                    "date",
                    "created_at",
                    "quantity",
                )
            ):
                return True

        return False