import re

from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis


class SchemaCompressor:
    """
    Compresses database schema before it is sent to the LLM.

    The compressor preserves columns that are likely to be
    required to answer the user's question while retaining
    primary keys, foreign keys, relationship columns, metrics,
    time columns, sorting columns, and common semantic fields.

    Compression is intentionally deterministic and does not
    require an LLM call.
    """

    # ======================================================
    # COMMON SEMANTIC COLUMNS
    # ======================================================

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

    # ======================================================
    # INTENT-SPECIFIC COLUMN KEYWORDS
    # ======================================================

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

    # ======================================================
    # QUESTION METRIC VOCABULARY
    # ======================================================

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

    # ======================================================
    # SEMANTIC COLUMN ALIASES
    # ======================================================

    COLUMN_ALIASES = {
        # Contact information
        "contact": {
            "email",
            "phone",
            "telephone",
            "mobile",
        },
        "contacts": {
            "email",
            "phone",
            "telephone",
            "mobile",
        },
        "email": {
            "email",
        },
        "emails": {
            "email",
        },

        # Location
        "location": {
            "city",
            "state",
            "country",
            "address",
        },
        "locations": {
            "city",
            "state",
            "country",
            "address",
        },

        # Product classification
        "category": {
            "category",
        },
        "categories": {
            "category",
        },

        # Human-readable identifiers
        "name": {
            "name",
        },
        "names": {
            "name",
        },
        "title": {
            "title",
        },
        "titles": {
            "title",
        },
    }

    # ======================================================
    # FILTERABLE COLUMN HINTS
    # ======================================================

    FILTERABLE_COLUMNS = {
        "name",
        "email",
        "city",
        "state",
        "country",
        "status",
        "type",
        "category",
        "title",
    }

    # ======================================================
    # FILTER LANGUAGE
    # ======================================================

    FILTER_PATTERNS = (
        r"\bfrom\s+\w+",
        r"\bin\s+(?:the\s+)?\w+",
        r"\bwhere\b",
        r"\bwith\s+\w+",
        r"\bhaving\s+\w+",
        r"\bwhose\b",
    )
    
    
    # ======================================================
    # TEMPORAL FILTER LANGUAGE
    # ======================================================

    TEMPORAL_QUESTION_KEYWORDS = {
        "after",
        "before",
        "since",
        "until",
        "between",
        "during",
        "today",
        "yesterday",
        "tomorrow",
        "recent",
        "latest",
        "earliest",
        "newest",
        "oldest",
        "date",
        "dates",
        "day",
        "daily",
        "week",
        "weekly",
        "month",
        "monthly",
        "year",
        "yearly",
    }

    # ======================================================
    # PUBLIC API
    # ======================================================

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
        2. Normalized singular/plural column matches.
        3. Semantically aliased columns.
        4. Primary keys.
        5. Foreign keys.
        6. Identifier columns.
        7. Question-driven metrics.
        8. Intent-specific columns.
        9. Likely filterable columns for filter-like questions.
        10. Common semantic columns.
        """

        if not schema:
            return {}

        tokens = self._tokenize(
            question
        )

        normalized_tokens = {
            self._normalize_token(token)
            for token in tokens
        }

        semantic_columns = (
            self._semantic_columns_from_question(
                tokens
            )
        )

        filter_like_question = (
            self._looks_like_filter_question(
                question
            )
        )
        
        temporal_question = bool(
            tokens
            & self.TEMPORAL_QUESTION_KEYWORDS
        )

        compressed: dict = {}

        for table_name, table in schema.items():

            compressed_table = (
                self._compress_table(
                    table_name=table_name,
                    table=table,
                    tokens=tokens,
                    normalized_tokens=normalized_tokens,
                    semantic_columns=semantic_columns,
                    filter_like_question=filter_like_question,
                    temporal_question=temporal_question,
                    intent=intent,
                )
            )

            compressed[
                table_name
            ] = compressed_table

        return compressed

    # ======================================================
    # TOKENIZATION
    # ======================================================

    @staticmethod
    def _tokenize(
        question: str,
    ) -> set[str]:
        """
        Convert the question into normalized lowercase
        lexical tokens.
        """

        return set(
            re.findall(
                r"\b\w+\b",
                question.lower(),
            )
        )

    # ======================================================
    # SIMPLE TOKEN NORMALIZATION
    # ======================================================

    @staticmethod
    def _normalize_token(
        token: str,
    ) -> str:
        """
        Normalize simple English plural forms.

        This is intentionally lightweight rather than a
        full NLP stemming system.

        Examples:

            customers -> customer
            names     -> name
            emails    -> email
            categories -> category
        """

        token = token.lower()

        if (
            len(token) > 4
            and token.endswith("ies")
        ):
            return (
                token[:-3]
                + "y"
            )

        if (
            len(token) > 3
            and token.endswith("es")
        ):
            candidate = token[:-2]

            # Handle ordinary forms such as:
            #
            # prices -> price
            #
            # before falling back to removing only "s".
            if candidate.endswith(
                (
                    "s",
                    "x",
                    "z",
                    "ch",
                    "sh",
                )
            ):
                return candidate

        if (
            len(token) > 3
            and token.endswith("s")
            and not token.endswith("ss")
        ):
            return token[:-1]

        return token

    # ======================================================
    # SEMANTIC QUESTION COLUMN EXPANSION
    # ======================================================

    def _semantic_columns_from_question(
        self,
        tokens: set[str],
    ) -> set[str]:
        """
        Convert natural-language question concepts into
        likely physical column concepts.

        Example:

            "contact details"

        can preserve:

            email
            phone
            mobile

        when those columns actually exist in the schema.
        """

        columns: set[str] = set()

        for token in tokens:

            aliases = (
                self.COLUMN_ALIASES.get(
                    token,
                    set(),
                )
            )

            columns.update(
                aliases
            )

        return columns

    # ======================================================
    # FILTER-LIKE QUESTION DETECTION
    # ======================================================

    @classmethod
    def _looks_like_filter_question(
        cls,
        question: str,
    ) -> bool:
        """
        Detect natural-language wording that probably
        requires filtering.

        This supplements IntentDetector because FILTER is
        not currently a fully scored primary intent.
        """

        normalized = question.lower()

        return any(
            re.search(
                pattern,
                normalized,
            )
            for pattern
            in cls.FILTER_PATTERNS
        )

    # ======================================================
    # TABLE COMPRESSION
    # ======================================================

    def _compress_table(
        self,
        table_name: str,
        table: dict,
        tokens: set[str],
        normalized_tokens: set[str],
        semantic_columns: set[str],
        filter_like_question: bool,
        temporal_question: bool,
        intent: IntentAnalysis,
    ) -> dict:
        """
        Compress one table while preserving the relationship
        information required for joins.
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
                normalized_tokens=normalized_tokens,
                semantic_columns=semantic_columns,
                filter_like_question=filter_like_question,
                temporal_question=temporal_question,
                intent=intent,
            )
        ]

        # --------------------------------------------------
        # Safety fallback
        # --------------------------------------------------

        if (
            not kept_columns
            and columns
        ):
            kept_columns = (
                columns[:3]
            )

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

    # ======================================================
    # COLUMN DECISION
    # ======================================================

    def _keep_column(
        self,
        column: dict,
        table: dict,
        tokens: set[str],
        normalized_tokens: set[str],
        semantic_columns: set[str],
        filter_like_question: bool,
        temporal_question: bool,
        intent: IntentAnalysis,
    ) -> bool:
        """
        Decide whether a physical database column should
        remain in the compressed schema.
        """

        column_name = column.get(
            "name"
        )

        if not column_name:
            return False

        name = (
            column_name.lower()
        )

        # ==================================================
        # 1. Exact question-column match
        # ==================================================

        if name in tokens:
            return True

        # ==================================================
        # 2. Normalized question-column match
        # ==================================================

        normalized_name = (
            self._normalize_token(
                name
            )
        )

        if (
            normalized_name
            in normalized_tokens
        ):
            return True

        # ==================================================
        # 3. Semantic alias match
        # ==================================================

        if name in semantic_columns:
            return True

        # ==================================================
        # 4. Primary key
        # ==================================================

        primary_keys = table.get(
            "primary_keys",
            {},
        )

        constrained_columns = (
            primary_keys.get(
                "constrained_columns",
                [],
            )
        )

        if name in {
            key.lower()
            for key
            in constrained_columns
        }:
            return True

        # ==================================================
        # 5. Foreign key
        # ==================================================

        for foreign_key in table.get(
            "foreign_keys",
            [],
        ):

            constrained_columns = (
                foreign_key.get(
                    "constrained_columns",
                    [],
                )
            )

            if name in {
                key.lower()
                for key
                in constrained_columns
            }:
                return True

        # ==================================================
        # 6. Identifier column
        # ==================================================

        if name.endswith(
            "_id"
        ):
            return True

        # ==================================================
        # 7. Question-driven financial metric preservation
        # ==================================================

        financial_metric_requested = bool(
            tokens
            & self.METRIC_QUESTION_KEYWORDS
        )

        if financial_metric_requested:

            if self._matches_keywords(
                name,
                self.AGGREGATION_COLUMNS,
            ):
                return True

        # ==================================================
        # 8. Question-driven quantity metric preservation
        # ==================================================

        quantity_metric_requested = bool(
            tokens
            & self.QUANTITY_QUESTION_KEYWORDS
        )

        if quantity_metric_requested:

            if self._matches_keywords(
                name,
                {
                    "quantity",
                    "count",
                    "units",
                },
            ):
                return True

        # ==================================================
        # 9. Aggregation intent
        # ==================================================

        if self._has_intent(
            intent,
            QueryIntent.AGGREGATION,
        ):

            if self._matches_keywords(
                name,
                self.AGGREGATION_COLUMNS,
            ):
                return True

        # ==================================================
        # 10. Time-series intent
        # ==================================================

        if self._has_intent(
            intent,
            QueryIntent.TIME_SERIES,
        ):

            if self._matches_keywords(
                name,
                self.TIME_COLUMNS,
            ):
                return True
        
        # ==================================================
        # 10b. Temporal question
        # ==================================================

        if temporal_question:

            if self._matches_keywords(
                name,
                self.TIME_COLUMNS,
            ):
                return True

        # ==================================================
        # 11. Sorting intent
        # ==================================================

        if self._has_intent(
            intent,
            QueryIntent.SORT,
        ):

            if self._matches_keywords(
                name,
                self.SORT_COLUMNS,
            ):
                return True

        # ==================================================
        # 12. Filter-like question
        # ==================================================

        if filter_like_question:

            if self._matches_keywords(
                name,
                self.FILTERABLE_COLUMNS,
            ):
                return True

        # ==================================================
        # 13. Common semantic column
        # ==================================================

        if self._matches_keywords(
            name,
            self.COMMON_COLUMNS,
        ):
            return True

        return False

    # ======================================================
    # KEYWORD MATCHING
    # ======================================================

    @staticmethod
    def _matches_keywords(
        column_name: str,
        keywords: set[str],
    ) -> bool:
        """
        Check whether a column matches one of the supplied
        semantic keywords.
        """

        if column_name in keywords:
            return True

        return any(
            keyword
            in column_name
            for keyword
            in keywords
        )

    # ======================================================
    # INTENT CHECK
    # ======================================================

    @staticmethod
    def _has_intent(
        intent: IntentAnalysis,
        target: QueryIntent,
    ) -> bool:
        """
        Check both primary and secondary intents.
        """

        return (
            intent.primary == target
            or target
            in intent.secondary
        )