import re
from dataclasses import dataclass

from sqlglot import exp, parse_one

from app.models.intent import QueryIntent


@dataclass
class SemanticValidationResult:
    """
    Result of semantic SQL validation.
    """

    valid: bool
    errors: list[str]


class SemanticValidator:
    """
    Performs deterministic semantic validation of generated SQL.

    This validator does NOT replace SQLValidator.

    SQLValidator answers:
        "Is this SQL structurally valid and safe?"

    SemanticValidator answers:
        "Does this SQL reasonably represent what the user asked?"

    The validator uses:
        - user question
        - detected intent
        - generated SQL
        - database schema

    It intentionally avoids an LLM call at this stage.
    """

    # ======================================================
    # METRIC KEYWORDS
    # ======================================================

    METRIC_KEYWORDS = {
        "spending": {
            "total_amount",
            "price",
            "unit_price",
        },
        "spent": {
            "total_amount",
            "price",
            "unit_price",
        },
        "revenue": {
            "total_amount",
            "price",
            "unit_price",
        },
        "sales": {
            "total_amount",
            "price",
            "unit_price",
        },
        "amount": {
            "total_amount",
            "price",
            "unit_price",
        },
        "value": {
            "total_amount",
            "price",
            "unit_price",
        },
        "quantity": {
            "quantity",
        },
        "units": {
            "quantity",
        },
        "number": {
            "id",
            "quantity",
        },
        "count": {
            "id",
        },
    }

    # ======================================================
    # AGGREGATION KEYWORDS
    # ======================================================

    AGGREGATION_FUNCTIONS = {
        "sum": exp.Sum,
        "avg": exp.Avg,
        "average": exp.Avg,
        "count": exp.Count,
        "min": exp.Min,
        "minimum": exp.Min,
        "max": exp.Max,
        "maximum": exp.Max,
    }

    # ======================================================
    # PUBLIC API
    # ======================================================

    def validate(
        self,
        question: str,
        sql: str,
        intent,
        schema: dict,
    ) -> SemanticValidationResult:
        """
        Validate whether generated SQL semantically matches
        the user's question.

        Returns
        -------
        SemanticValidationResult
        """

        errors: list[str] = []

        if not question or not question.strip():
            errors.append(
                "User question is empty."
            )

        if not sql or not sql.strip():
            errors.append(
                "Generated SQL is empty."
            )

        if errors:
            return SemanticValidationResult(
                valid=False,
                errors=errors,
            )

        try:
            statement = parse_one(
                sql,
                read="postgres",
            )
        except Exception as exc:
            return SemanticValidationResult(
                valid=False,
                errors=[
                    f"Unable to parse SQL for semantic validation: {exc}"
                ],
            )

        primary_intent = getattr(
            intent,
            "primary",
            None,
        )

        question_tokens = self._tokenize(
            question
        )

        # --------------------------------------------------
        # 1. Validate metric semantics
        # --------------------------------------------------

        errors.extend(
            self._validate_metrics(
                question_tokens=question_tokens,
                statement=statement,
                schema=schema,
            )
        )

        # --------------------------------------------------
        # 2. Validate aggregation semantics
        # --------------------------------------------------

        errors.extend(
            self._validate_aggregation(
                question_tokens=question_tokens,
                statement=statement,
                primary_intent=primary_intent,
            )
        )

        # --------------------------------------------------
        # 3. Validate GROUP BY semantics
        # --------------------------------------------------

        errors.extend(
            self._validate_grouping(
                question_tokens=question_tokens,
                statement=statement,
                primary_intent=primary_intent,
            )
        )

        # --------------------------------------------------
        # 4. Validate sorting semantics
        # --------------------------------------------------

        errors.extend(
            self._validate_sorting(
                question_tokens=question_tokens,
                statement=statement,
                primary_intent=primary_intent,
            )
        )

        return SemanticValidationResult(
            valid=not errors,
            errors=errors,
        )

    # ======================================================
    # TOKENIZATION
    # ======================================================

    @staticmethod
    def _tokenize(
        question: str,
    ) -> set[str]:
        """
        Convert the question into normalized tokens.
        """

        return set(
            re.findall(
                r"\b\w+\b",
                question.lower(),
            )
        )

    # ======================================================
    # METRIC VALIDATION
    # ======================================================

    def _validate_metrics(
        self,
        question_tokens: set[str],
        statement,
        schema: dict,
    ) -> list[str]:
        """
        Validate that important business metrics in the
        question are represented by appropriate columns
        in the generated SQL.

        Example:

            "Compare customer spending"

        should generally use:

            orders.total_amount

        rather than:

            order_items.quantity
        """

        errors: list[str] = []

        expected_columns: set[str] = set()

        matched_metric_keywords: set[str] = set()

        for token in question_tokens:

            if token in self.METRIC_KEYWORDS:

                matched_metric_keywords.add(
                    token
                )

                expected_columns.update(
                    self.METRIC_KEYWORDS[token]
                )

        if not expected_columns:
            return errors

        referenced_columns = (
            self._get_referenced_columns(
                statement
            )
        )

        # --------------------------------------------------
        # Determine whether SQL uses an expected metric.
        # --------------------------------------------------

        uses_expected_metric = bool(
            referenced_columns
            & expected_columns
        )

        if uses_expected_metric:
            return errors

        # --------------------------------------------------
        # Special handling for "spending".
        # --------------------------------------------------

        if (
            "spending"
            in matched_metric_keywords
            or "spent"
            in matched_metric_keywords
        ):

            if "total_amount" in (
                self._schema_column_names(schema)
            ):

                errors.append(
                    "The SQL does not use the expected "
                    "spending metric 'total_amount'. "
                    "The question refers to customer spending."
                )

                return errors

        # --------------------------------------------------
        # Generic metric mismatch.
        # --------------------------------------------------

        errors.append(
            "The SQL does not appear to use the metric "
            "requested by the user."
        )

        return errors

    # ======================================================
    # AGGREGATION VALIDATION
    # ======================================================

    def _validate_aggregation(
        self,
        question_tokens: set[str],
        statement,
        primary_intent,
    ) -> list[str]:
        """
        Validate aggregation behavior.
        """

        errors: list[str] = []

        aggregation_requested = bool(
            question_tokens
            & {
                "sum",
                "total",
                "average",
                "avg",
                "count",
                "maximum",
                "minimum",
                "max",
                "min",
                "spending",
                "spent",
                "revenue",
                "sales",
            }
        )

        if (
            primary_intent != QueryIntent.AGGREGATION
            and not aggregation_requested
        ):
            return errors

        aggregate_functions = list(
            statement.find_all(
                exp.AggFunc
            )
        )

        if not aggregate_functions:
            errors.append(
                "The question implies aggregation, "
                "but the generated SQL contains no "
                "aggregate function."
            )

        return errors

    # ======================================================
    # GROUPING VALIDATION
    # ======================================================

    def _validate_grouping(
        self,
        question_tokens: set[str],
        statement,
        primary_intent,
    ) -> list[str]:
        """
        Validate grouping for queries such as:

            total order amount per customer
            sales by city
            orders per month
        """

        errors: list[str] = []

        grouping_requested = bool(
            question_tokens
            & {
                "per",
                "each",
                "group",
                "monthly",
                "daily",
                "weekly",
                "yearly",
                "by",
            }
        )

        if (
            primary_intent
            not in {
                QueryIntent.GROUP_BY,
                QueryIntent.AGGREGATION,
                QueryIntent.TIME_SERIES,
            }
            and not grouping_requested
        ):
            return errors

        has_group = statement.find(
            exp.Group
        ) is not None

        has_aggregate = (
            statement.find(
                exp.AggFunc
            )
            is not None
        )

        # --------------------------------------------------
        # Grouping is only mandatory when aggregation exists.
        # --------------------------------------------------

        if has_aggregate and grouping_requested:

            if not has_group:

                errors.append(
                    "The question requests grouped "
                    "aggregation, but the generated SQL "
                    "does not contain GROUP BY."
                )

        return errors

    # ======================================================
    # SORTING VALIDATION
    # ======================================================

    def _validate_sorting(
        self,
        question_tokens: set[str],
        statement,
        primary_intent,
    ) -> list[str]:
        """
        Validate ORDER BY for queries that explicitly
        request ordering.
        """

        errors: list[str] = []

        sorting_requested = bool(
            question_tokens
            & {
                "top",
                "highest",
                "lowest",
                "largest",
                "smallest",
                "recent",
                "latest",
                "newest",
                "oldest",
                "earliest",
            }
        )

        if (
            primary_intent != QueryIntent.SORT
            and not sorting_requested
        ):
            return errors

        has_order = statement.find(
            exp.Order
        ) is not None

        if not has_order:

            errors.append(
                "The question requests ordered "
                "results, but the generated SQL "
                "does not contain ORDER BY."
            )

        return errors

    # ======================================================
    # SQL COLUMN EXTRACTION
    # ======================================================

    @staticmethod
    def _get_referenced_columns(
        statement,
    ) -> set[str]:
        """
        Extract physical column names referenced by SQL.
        """

        columns: set[str] = set()

        for column in statement.find_all(
            exp.Column
        ):

            name = column.name

            if name and name != "*":

                columns.add(
                    name
                )

        return columns

    # ======================================================
    # SCHEMA COLUMN EXTRACTION
    # ======================================================

    @staticmethod
    def _schema_column_names(
        schema: dict,
    ) -> set[str]:
        """
        Extract all physical column names from schema.
        """

        columns: set[str] = set()

        for table_info in schema.values():

            for column in table_info.get(
                "columns",
                [],
            ):

                name = column.get(
                    "name"
                )

                if name:

                    columns.add(
                        name
                    )

        return columns