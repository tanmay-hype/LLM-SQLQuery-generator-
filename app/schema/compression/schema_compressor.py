import re

from app.models.intent_analysis import IntentAnalysis
from app.models.intent import QueryIntent


class SchemaCompressor:
    """
    Compresses database schema before it is sent to the LLM.

    The compressor keeps only information that is likely to be
    required for SQL generation while preserving keys and
    relationships needed for JOINs.
    """

    # --------------------------------------------------
    # Common semantic columns
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
        "total",
    }

    # --------------------------------------------------
    # Intent-specific column keywords
    # --------------------------------------------------

    AGGREGATION_COLUMNS = {
        "amount",
        "price",
        "cost",
        "total",
        "quantity",
        "salary",
        "revenue",
        "count",
    }

    TIME_COLUMNS = {
        "date",
        "time",
        "created_at",
        "updated_at",
        "timestamp",
    }

    SORT_COLUMNS = {
        "amount",
        "price",
        "quantity",
        "total",
        "date",
        "created_at",
        "updated_at",
        "name",
    }
    
    METRIC_QUESTION_KEYWORDS = {
        "amount",
        "total",
        "spending",
        "spent",
        "sales",
        "revenue",
        "value",
        "cost",
        "price",
        "money",
    }
    
    QUANTITY_QUESTION_KEYWORDS = {
        "quantity",
        "quantities",
        "units",
        "items",
        "number",
        "count",
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
        Compress the supplied schema.

        The compression process preserves:

        1. Explicitly mentioned columns.
        2. Primary keys.
        3. Foreign keys.
        4. Intent-specific columns.
        5. Common semantic columns.

        Everything else is removed.
        """

        if not schema:
            return {}

        tokens = self._tokenize(question)

        compressed = {}

        for table_name, table in schema.items():

            compressed_table = self._compress_table(
                table_name=table_name,
                table=table,
                tokens=tokens,
                intent=intent,
            )

            compressed[table_name] = compressed_table

        return compressed

    # --------------------------------------------------
    # Tokenization
    # --------------------------------------------------

    @staticmethod
    def _tokenize(question: str) -> set[str]:
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
    # Table compression
    # --------------------------------------------------

    def _compress_table(
        self,
        table_name: str,
        table: dict,
        tokens: set[str],
        intent: IntentAnalysis,
    ) -> dict:
        """
        Compress a single table while preserving
        relationship information.
        """

        columns = table.get(
            "columns",
            [],
        )

        kept_columns = [
            column
            for column in columns
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

        # A table should never become completely unusable.
        #
        # If no column survived compression, keep the first
        # few columns as a safety fallback.
        if not kept_columns and columns:
            kept_columns = columns[:3]

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
    # Column decision
    # --------------------------------------------------

    def _keep_column(
        self,
        column: dict,
        table: dict,
        tokens: set[str],
        intent: IntentAnalysis,
    ) -> bool:
        """
        Decide whether a column should remain in the
        compressed schema.
        """

        column_name = column.get("name")

        if not column_name:
            return False

        name = column_name.lower()

        # --------------------------------------------------
        # 1. Explicit question match
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
            key.lower()
            for key in constrained_columns
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
                key.lower()
                for key in constrained_columns
            }:
                return True

        # --------------------------------------------------
        # 4. Identifier columns
        # --------------------------------------------------

        if name.endswith("_id"):
            return True
        
        
        # --------------------------------------------------
        # 5. Question-driven financial metric preserevation
        # --------------------------------------------------

        financial_metric_requested = bool(
            tokens
            & self.METRIC_QUESTION_KEYWORDS
        )
        if financial_metric_requested :
            if self._matches_keywords(
                name,
                self.AGGREGATION_COLUMNS,
            ):
                return True
        
        # --------------------------------------------------
        # 6. Question-driven quantity metric preserevation
        # --------------------------------------------------

        quantity_metric_requested = bool(
            tokens
            & self.QUANTITY_QUESTION_KEYWORDS
        )
        if quantity_metric_requested :
            if self._matches_keywords(
                name,
                {
                    "quantity",
                    "count",
                    "units",
                },
            ):
                return True

        # --------------------------------------------------
        # 7. Aggregation intent
        # --------------------------------------------------

        if self._has_intent(
            intent,
            QueryIntent.AGGREGATION,
        ):

            if self._matches_keywords(
                name,
                self.AGGREGATION_COLUMNS,
            ):
                return True

        # --------------------------------------------------
        # 8. Time-series intent
        # --------------------------------------------------

        if self._has_intent(
            intent,
            QueryIntent.TIME_SERIES,
        ):

            if self._matches_keywords(
                name,
                self.TIME_COLUMNS,
            ):
                return True

        # --------------------------------------------------
        # 9. Sorting intent
        # --------------------------------------------------

        if self._has_intent(
            intent,
            QueryIntent.SORT,
        ):

            if self._matches_keywords(
                name,
                self.SORT_COLUMNS,
            ):
                return True

        # --------------------------------------------------
        # 10. Common semantic columns
        # --------------------------------------------------

        if self._matches_keywords(
            name,
            self.COMMON_COLUMNS,
        ):
            return True

        return False

    # --------------------------------------------------
    # Keyword matching
    # --------------------------------------------------

    @staticmethod
    def _matches_keywords(
        column_name: str,
        keywords: set[str],
    ) -> bool:
        """
        Check whether a column matches one of the
        supplied semantic keywords.
        """

        if column_name in keywords:
            return True

        return any(
            keyword in column_name
            for keyword in keywords
        )
    
    @staticmethod
    def _has_intent(
        intent: IntentAnalysis,
        target: QueryIntent,
    ) -> bool:
        """
        Check whether the intent analysis indicates
        a specific query intent.
        """

        return (
            intent.primary == target
            or target in intent.secondary
        )