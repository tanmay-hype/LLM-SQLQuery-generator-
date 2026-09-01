import re
from dataclasses import dataclass

from sqlglot import exp, parse_one

from app.services.schema_relationship_extractor import (SchemaRelationshipExtractor)
from app.models.intent import QueryIntent
from app.models.semantic_contract import SemanticContract
from app.services.semantic_contract_builder import (
    SemanticContractBuilder,
)


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
        - deterministic semantic contract

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

    AGGREGATION_REQUEST_TOKENS = {
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

    # ======================================================
    # GROUPING KEYWORDS
    # ======================================================

    GROUPING_REQUEST_TOKENS = {
        "per",
        "each",
        "group",
        "monthly",
        "daily",
        "weekly",
        "yearly",
        "by",
    }

    # ======================================================
    # SORTING KEYWORDS
    # ======================================================

    SORTING_REQUEST_TOKENS = {
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

    # ======================================================
    # SUPERLATIVE KEYWORDS
    # ======================================================

    SUPERLATIVE_TOKENS = {
        "highest",
        "lowest",
        "largest",
        "smallest",
        "maximum",
        "minimum",
        "max",
        "min",
    }

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(
        self,
        contract_builder: SemanticContractBuilder | None = None,
        relationship_extractor: SchemaRelationshipExtractor | None = None,
    ):
        self.contract_builder = (
            contract_builder
            or SemanticContractBuilder()
        )
        self.relationship_extractor = (
            relationship_extractor
            or SchemaRelationshipExtractor()
        )

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
                    (
                        "Unable to parse SQL for semantic "
                        f"validation: {exc}"
                    )
                ],
            )

        question_tokens = self._tokenize(
            question
        )

        # --------------------------------------------------
        # Build deterministic semantic contract.
        #
        # This considers both:
        #   - primary intent
        #   - secondary intents
        # --------------------------------------------------

        contract = self.contract_builder.build(
            intent
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
                contract=contract,
            )
        )

        # --------------------------------------------------
        # 3. Validate GROUP BY semantics
        # --------------------------------------------------

        errors.extend(
            self._validate_grouping(
                question_tokens=question_tokens,
                statement=statement,
                contract=contract,
            )
        )

        # --------------------------------------------------
        # 4. Validate sorting semantics
        # --------------------------------------------------

        errors.extend(
            self._validate_sorting(
                question_tokens=question_tokens,
                statement=statement,
                contract=contract,
            )
        )

        # --------------------------------------------------
        # 5. Validate JOIN semantics
        # --------------------------------------------------

        errors.extend(
            self._validate_join(
                statement=statement,
                contract=contract,
                schema=schema,
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

        rather than an unrelated metric.
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

        uses_expected_metric = bool(
            referenced_columns
            & expected_columns
        )

        if uses_expected_metric:
            return errors

        # --------------------------------------------------
        # Special handling for customer spending.
        # --------------------------------------------------

        if (
            "spending"
            in matched_metric_keywords
            or "spent"
            in matched_metric_keywords
        ):

            if (
                "total_amount"
                in self._schema_column_names(
                    schema
                )
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
        contract: SemanticContract,
    ) -> list[str]:
        """
        Validate aggregation behavior.

        An aggregate function is normally required when
        aggregation is requested.

        However, superlative questions such as:

            "highest product price"

        may validly use:

            ORDER BY price DESC
            LIMIT 1

        instead of:

            MAX(price)

        Both forms are accepted.
        """

        errors: list[str] = []

        aggregation_requested = bool(
            question_tokens
            & self.AGGREGATION_REQUEST_TOKENS
        )

        if (
            not contract.requires_aggregation
            and not aggregation_requested
        ):
            return errors

        has_aggregate = self._has_aggregate(
            statement
        )

        if has_aggregate:
            return errors

        # --------------------------------------------------
        # Accept ORDER BY + LIMIT for superlative queries.
        # --------------------------------------------------

        if self._is_valid_superlative_query(
            question_tokens=question_tokens,
            statement=statement,
        ):
            return errors

        errors.append(
            "The question implies aggregation, "
            "but the generated SQL contains no "
            "aggregate function or equivalent "
            "superlative ordering."
        )

        return errors

    # ======================================================
    # GROUPING VALIDATION
    # ======================================================

    def _validate_grouping(
        self,
        question_tokens: set[str],
        statement,
        contract: SemanticContract,
    ) -> list[str]:
        """
        Validate grouping for queries such as:

            total order amount per customer
            sales by city
            orders per month

        Both question wording and the semantic contract
        participate in the decision.
        """

        errors: list[str] = []

        grouping_requested = bool(
            question_tokens
            & self.GROUPING_REQUEST_TOKENS
        )

        grouping_required = (
            contract.requires_group_by
            or grouping_requested
        )

        if not grouping_required:
            return errors

        has_group = self._has_group_by(
            statement
        )

        has_aggregate = self._has_aggregate(
            statement
        )

        # --------------------------------------------------
        # For aggregate queries, GROUP BY is required when
        # grouping was requested.
        # --------------------------------------------------

        if has_aggregate and not has_group:

            errors.append(
                "The question requests grouped "
                "aggregation, but the generated SQL "
                "does not contain GROUP BY."
            )

            return errors

        # --------------------------------------------------
        # If IntentDetector explicitly classified GROUP_BY,
        # respect the semantic contract even when the SQL
        # accidentally omitted both GROUP BY and aggregation.
        # --------------------------------------------------

        if (
            contract.requires_group_by
            and not has_group
            and contract.requires_aggregation
        ):

            errors.append(
                "The detected intent requires GROUP BY, "
                "but the generated SQL does not contain "
                "GROUP BY."
            )

        return errors

    # ======================================================
    # SORTING VALIDATION
    # ======================================================

    def _validate_sorting(
        self,
        question_tokens: set[str],
        statement,
        contract: SemanticContract,
    ) -> list[str]:
        """
        Validate ORDER BY for queries that explicitly
        request ordering.

        Superlative questions are allowed to use either:

        MAX()/MIN()

        or:

        ORDER BY ... LIMIT

        without requiring both forms.
        """

        errors: list[str] = []

        sorting_requested = bool(
            question_tokens
            & self.SORTING_REQUEST_TOKENS
        )

        if (
            not contract.requires_order_by
            and not sorting_requested
        ):
            return errors
        
        has_order = self._has_order_by(
            statement
        )
        
        if has_order:
            return errors
        
        # --------------------------------------------------
        # Superlative aggregate equivalence
        #
        # Examples:
        #
        #   "highest product price"
        #
        # can validly use:
        #
        #     SELECT MAX(price) ...
        #
        # instead of:
        #
        #   ORDER BY price DESC LIMIT 1
        #
        # Likewise MIN() satisfies lowest/minimum questions.
        # --------------------------------------------------
        
        if self._is_superlative_aggregate(
            question_tokens=question_tokens,
            statement=statement,
        ):
            return errors
        
        errors.append(
            "The question requests sorted results, "
            "but the generated SQL does not contain "
            "ORDER BY."
        )
        
        return errors



    # ======================================================
    # JOIN VALIDATION
    # ======================================================

    def _validate_join(
        self,
        statement,
        contract: SemanticContract,
        schema: dict,
    ) -> list[str]:
        """
        Validate JOIN semantics.

        Validation includes:

        1. A JOIN must exist when JOIN intent is required.
        2. JOIN equality predicates between physical tables
           must correspond to declared foreign-key
           relationships.
        3. Table aliases are resolved before FK comparison.

        Examples:

            Valid:
                orders.customer_id = customers.id

            Valid with aliases:
                o.customer_id = c.id

            Invalid:
                orders.id = customers.id
        """
        joins = list(
            statement.find_all(
                exp.Join
            )
        )
        
        # --------------------------------------------------
        # JOIN required but completely missing.
        # --------------------------------------------------
        
        if (
            contract.requires_join
            and not joins
        ):
            return [
                "The detected intent requires a JOIN, "
                "but the generated SQL contains no JOIN."
            ]
        
        # --------------------------------------------------
        # No JOIN means there is nothing further to validate.
        #
        # This also allows ordinary single-table queries.
        # --------------------------------------------------
        
        if not joins:
            return []
        
        relationships = self.relationship_extractor.extract(
            schema
        )
        
        # --------------------------------------------------
        # If the schema contains no FK metadata, do not
        # invent relationships or reject based on guesses.
        # --------------------------------------------------
        
        if not relationships:
            return []
        
        alias_map = self._build_table_alias_map(
            statement
        )
        
        errors: list[str] = []
        
        for join in joins:
            
            errors.extend(
                self._validate_join_expression(
                    join=join,
                    alias_map=alias_map,
                    relationships=relationships,
                )
            )
            
        return errors
    
    
    # ======================================================
    # TABLE ALIAS MAP
    # ======================================================
    
    @staticmethod
    def _build_table_alias_map(
        statement,
    ) -> dict[str, str]:
        """
        Build a mapping of table aliases to physical table names.

        Example:

            FROM customers c
            JOIN orders o ...

        becomes:

            {
                "customers": "customers",
                "c": "customers",
                "orders": "orders",
                "o": "orders",
            }
        """

        alias_map: dict[str, str] = {}

        for table in statement.find_all(
            exp.Table
        ):
            
            table_name = table.name
            
            if not table_name:
                continue
            
            alias_map[table_name] = table_name  
            
            alias = table.alias
            
            if alias:
                alias_map[alias] = table_name
    
        return alias_map


    # ======================================================
    # SINGLE JOIN VALIDATION
    # ======================================================
    
    
    def _validate_join_expression(
        self,
        join,
        alias_map: dict[str, str],
        relationships,
    ) -> list[str]:
        """
        Validate a single join expression against the provided alias map and relationships.
        """
        
        on_expression = join.args.get(
            "on"
        )
        
        if on_expression is None:
            return [
                (
                "The generated JOIN does not contain"
                " an ON condition that can be validated"
                "against schema relationships"
                )
            ]
            
        equality_predicates = list(
            on_expression.find_all(
                exp.EQ
            )
        )
        
        #The root ON expression itself may be an EQ
        
        if isinstance(on_expression, exp.EQ):
            equality_predicates.insert(
                0,
                on_expression
            )
        
        # Remove duplicates caused by the root expression
        # also appearing in find_all().
        
        unique_predicates = []
        
        seen_ids: set[int] = set()
        
        for predicate in equality_predicates:
            
            predicate_id = id(predicate)
            
            if predicate_id in seen_ids:
                continue
            
            seen_ids.add(predicate_id)
            unique_predicates.append(
                predicate
            )
        
        if not unique_predicates:
            return [
                (
                "The generated JOIN does not contain"
                " an equality predicate that can be validated"
                " against schema relationships"
                )
            ]
        
        found_column_pair = False
        
        for predicate in unique_predicates:
            
            left = predicate.this
            right = predicate.expression
            
            if (
                not isinstance(left, exp.Column)
                or not isinstance(right, exp.Column)
            ):
                continue
            
            left_table = self._resolve_column_table(
                column=left,
                alias_map=alias_map,
            )
            
            right_table = self._resolve_column_table(
                column=right,
                alias_map=alias_map,
            )
            
            # ----------------------------------------------
            # Unqualified columns cannot safely establish
            # which physical tables participate.
            # ----------------------------------------------
            
            if(
                left_table is None
                or right_table is None
            ):
                continue
            
            found_column_pair = True
            
            left_column = left.name
            right_column = right.name
            
            for relationship in relationships:
                
                if relationship.matches(
                    left_table=left_table,
                    left_column=left_column,
                    right_table=right_table,
                    right_column=right_column,
                ):
                    return[]
        
        if not found_column_pair:
            return [
                (
                "The generated JOIN does not contain"
                " an equality predicate between two "
                "physical columns that can be validated"
                " against schema relationships"
                )
            ]
        return [ 
            (
                "The JOIN condition does not match any"
                " declared foreign-key relationships in the schema."
                    
            )
        ]
    
    # ======================================================
    # COLUMN TABLE RESOLUTION
    # ======================================================

    @staticmethod
    def _resolve_column_table(
        column,
        alias_map: dict[str, str],
    ) -> str | None:
        """
        Resolve a SQLGlot Column table qualifier to its
        physical table name.

        Example:

            o.customer_id

        with:

            o -> orders

        resolves to:

            orders
        """

        table_reference = column.table

        if not table_reference:
            return None

        return alias_map.get(
            table_reference
        )
    
    
    # ======================================================
    # AGGREGATE DETECTION
    # ======================================================

    @staticmethod
    def _has_aggregate(
        statement,
    ) -> bool:
        """
        Return True when SQL contains an aggregate function.
        """

        return (
            statement.find(
                exp.AggFunc
            )
            is not None
        )

    # ======================================================
    # GROUP BY DETECTION
    # ======================================================

    @staticmethod
    def _has_group_by(
        statement,
    ) -> bool:
        """
        Return True when SQL contains GROUP BY.
        """

        return (
            statement.find(
                exp.Group
            )
            is not None
        )

    # ======================================================
    # ORDER BY DETECTION
    # ======================================================

    @staticmethod
    def _has_order_by(
        statement,
    ) -> bool:
        """
        Return True when SQL contains ORDER BY.
        """

        return (
            statement.find(
                exp.Order
            )
            is not None
        )

    # ======================================================
    # LIMIT DETECTION
    # ======================================================

    @staticmethod
    def _has_limit(
        statement,
    ) -> bool:
        """
        Return True when SQL contains LIMIT.
        """

        return (
            statement.find(
                exp.Limit
            )
            is not None
        )
    
    # ======================================================
    # SUPERLATIVE AGGREGATE DETECTION
    # ======================================================    
    
    @staticmethod
    def _is_superlative_aggregate(
        question_tokens: set[str],
        statement,
    ) -> bool:
        """
        Return True when an aggregate function directly
        satisfies a superlative request.

        Examples:

            highest / largest / maximum / max
                -> MAX(...)

            lowest / smallest / minimum / min
                -> MIN(...)
        """
        
        maximum_requested = bool(
            question_tokens
            & {"highest", "largest", "maximum", "max"}  
        )
        
        minimum_requested = bool(
            question_tokens
            & {"lowest", "smallest", "minimum", "min"}
        )
        
        if maximum_requested:
            
            has_max = (
                statement.find(
                    exp.Max
                )
                is not None
            )
            
            if has_max:
                return True
        
        if minimum_requested:
            
            has_min = (
                statement.find(
                    exp.Min
                )
                is not None
            )
            
            if has_min:
                return True
        
        return False
        
    
    # ======================================================
    # SUPERLATIVE QUERY DETECTION
    # ======================================================

    def _is_valid_superlative_query(
        self,
        question_tokens: set[str],
        statement,
    ) -> bool:
        """
        Accept ORDER BY + LIMIT as an alternative to
        MAX()/MIN() for superlative questions.

        Example:

           highest / largest
                -> ORDER BY column DESC LIMIT 1

            lowest / smallest
                -> ORDER BY column ASC LIMIT 1
        """
        
        maximum_requested = bool(
            question_tokens
            & {"highest", "largest", "maximum", "max"}  
        )
        
        minimum_requested = bool(
            question_tokens
            & {"lowest", "smallest", "minimum", "min"}
        )
        
        if (
            not maximum_requested
            and not minimum_requested
        ):
            return False
        
        # --------------------------------------------------
        # Read ORDER BY and LIMIT directly from the parsed
        # SELECT expression.
        #
        # This is more reliable here than relying only on
        # recursive find() calls.
        # --------------------------------------------------
        
        order = statement.args.get(
            "order"
        )
        
        limit = statement.args.get(
            "limit"
        )
        
        if  order is None or limit is None:
            return False
        
        ordered_expressions = list(
            order.expressions
        )
        
        if not ordered_expressions:
            return False
        
        first_order = ordered_expressions[0]
        
        # sqlglot represents ORDER BY expressions using
        # exp.Ordered. Its "desc" argument tells us the
        # requested direction.
        
        is_descending = bool(
            first_order.args.get(
                "desc"
            )
        )
        
        if maximum_requested:
            return is_descending
        
        if minimum_requested:
            return not is_descending
        
        return False


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