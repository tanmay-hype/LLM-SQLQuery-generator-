import re

from sqlglot import exp, parse_one
from sqlglot.errors import ParseError


# ==========================================================
# AST HELPERS
# ==========================================================


def extract_tables(
    statement,
) -> set[str]:
    """
    Extract physical table names while excluding CTE names.
    """

    cte_names = {
        cte.alias_or_name
        for cte in statement.find_all(
            exp.CTE
        )
        if cte.alias_or_name
    }

    return {
        table.name
        for table in statement.find_all(
            exp.Table
        )
        if (
            table.name
            and table.name not in cte_names
        )
    }


def extract_columns(
    statement,
) -> set[str]:
    """
    Extract referenced column names.
    """

    return {
        column.name
        for column in statement.find_all(
            exp.Column
        )
        if column.name
    }


def extract_aggregates(
    statement,
) -> set[str]:
    """
    Extract aggregate function names.
    """

    return {
        node.key.upper()
        for node in statement.find_all(
            exp.AggFunc
        )
    }


def has_group_by(
    statement,
) -> bool:
    return (
        statement.find(
            exp.Group
        )
        is not None
    )


def has_order_by(
    statement,
) -> bool:
    return (
        statement.find(
            exp.Order
        )
        is not None
    )


def has_where(
    statement,
) -> bool:
    return (
        statement.find(
            exp.Where
        )
        is not None
    )


def has_join(
    statement,
) -> bool:
    return bool(
        list(
            statement.find_all(
                exp.Join
            )
        )
    )


def has_limit(
    statement,
) -> bool:
    return (
        statement.find(
            exp.Limit
        )
        is not None
        or statement.find(
            exp.Fetch
        )
        is not None
    )


def get_limit_value(
    statement,
) -> int | None:
    """
    Return LIMIT/FETCH value when it is a literal integer.
    """

    limit = statement.find(
        exp.Limit
    )

    if limit is not None:
        expression = limit.expression

        if expression is not None:
            try:
                return int(
                    expression.name
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

    fetch = statement.find(
        exp.Fetch
    )

    if fetch is not None:
        count = fetch.args.get(
            "count"
        )

        if count is not None:
            try:
                return int(
                    count.name
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

    return None


def has_distinct(
    statement,
) -> bool:
    """
    Detect SELECT DISTINCT.
    """

    select_node = (
        statement
        if isinstance(
            statement,
            exp.Select,
        )
        else statement.find(
            exp.Select
        )
    )

    if select_node is None:
        return False

    return bool(
        select_node.args.get(
            "distinct"
        )
    )


def get_order_direction(
    statement,
) -> str | None:
    """
    Return direction of the first ORDER BY expression.
    """

    order = statement.find(
        exp.Order
    )

    if order is None:
        return None

    expressions = (
        order.expressions
    )

    if not expressions:
        return None

    first = expressions[0]

    if isinstance(
        first,
        exp.Ordered,
    ):
        return (
            "DESC"
            if first.args.get(
                "desc"
            )
            else "ASC"
        )

    return None


# ==========================================================
# DATE GRANULARITY
# ==========================================================


def extract_date_granularities(
    statement,
) -> set[str]:
    """
    Extract DATE_TRUNC granularities.

    Example:

        DATE_TRUNC('month', order_date)

    returns:

        {"month"}
    """

    sql_text = statement.sql(
        dialect="postgres"
    )

    matches = re.findall(
        r"""
        DATE_TRUNC
        \s*
        \(
        \s*
        ['"]?
        ([A-Za-z]+)
        ['"]?
        \s*,
        """,
        sql_text,
        re.IGNORECASE | re.VERBOSE,
    )

    return {
        match.lower()
        for match in matches
    }


# ==========================================================
# INSUFFICIENT INFORMATION
# ==========================================================


def is_insufficient_query(
    sql: str,
) -> bool:
    normalized = (
        " ".join(
            sql.lower().split()
        )
    )

    return (
        "insufficient information"
        in normalized
    )


# ==========================================================
# V2: LITERAL VALIDATION
# ==========================================================


def extract_literals(
    statement,
) -> set[str]:
    """
    Extract SQL literal values.

    Examples:

        city = 'Mumbai'
        price > 1000
        order_date >= '2025-01-01'

    produce literal values such as:

        {"Mumbai", "1000", "2025-01-01"}
    """

    literals: set[str] = set()

    for literal in statement.find_all(
        exp.Literal
    ):
        value = literal.this

        if value is not None:
            literals.add(
                str(value)
            )

    return literals

# ==========================================================
# V2: COMPARISON VALIDATION
# ==========================================================


def extract_comparison_operators(
    statement,
) -> set[str]:
    """
    Extract comparison operators used in predicates.

    Supported operators:

        =
        !=
        >
        >=
        <
        <=
        BETWEEN
    """

    operators: set[str] = set()

    operator_types = (
        (exp.EQ, "="),
        (exp.NEQ, "!="),
        (exp.GT, ">"),
        (exp.GTE, ">="),
        (exp.LT, "<"),
        (exp.LTE, "<="),
        (exp.Between, "BETWEEN"),
    )

    for expression_type, operator in operator_types:
        if any(
            statement.find_all(
                expression_type
            )
        ):
            operators.add(
                operator
            )

    return operators


# ==========================================================
# V2: DISTINCT AGGREGATE VALIDATION
# ==========================================================


def has_distinct_aggregate(
    statement,
) -> bool:
    """
    Detect an aggregate containing DISTINCT.

    Example:

        COUNT(DISTINCT product_id)
    """

    for aggregate in statement.find_all(
        exp.AggFunc
    ):
        if aggregate.find(
            exp.Distinct
        ) is not None:
            return True

    return False


# ==========================================================
# V2: REVENUE EXPRESSION VALIDATION
# ==========================================================


def has_revenue_expression(
    statement,
) -> bool:
    """
    Detect multiplication involving quantity and unit_price.

    Expected semantic form:

        quantity * unit_price

    The multiplication may appear inside SUM(), aliases,
    parentheses, or another surrounding expression.
    """

    for multiplication in statement.find_all(
        exp.Mul
    ):
        columns = {
            column.name.lower()
            for column in multiplication.find_all(
                exp.Column
            )
            if column.name
        }

        if {
            "quantity",
            "unit_price",
        }.issubset(
            columns
        ):
            return True

    return False


# ==========================================================
# SEMANTIC ALTERNATIVES
# ==========================================================


def evaluate_semantic_alternative(
    statement,
    alternative: dict,
) -> list[str]:
    """
    Evaluate one acceptable SQL implementation.
    """

    errors: list[str] = []

    aggregates = extract_aggregates(
        statement
    )

    required_aggregates = set(
        alternative.get(
            "required_aggregates",
            set(),
        )
    )

    missing_aggregates = (
        required_aggregates
        - aggregates
    )

    if missing_aggregates:
        errors.append(
            "Missing aggregate(s): "
            + ", ".join(
                sorted(
                    missing_aggregates
                )
            )
        )

    if (
        alternative.get(
            "requires_order_by"
        )
        and not has_order_by(
            statement
        )
    ):
        errors.append(
            "ORDER BY is required."
        )

    expected_direction = (
        alternative.get(
            "order_direction"
        )
    )

    if expected_direction:
        actual_direction = (
            get_order_direction(
                statement
            )
        )

        if (
            actual_direction
            != expected_direction
        ):
            errors.append(
                "Incorrect ORDER BY direction. "
                f"Expected {expected_direction}, "
                f"got {actual_direction}."
            )

    if (
        alternative.get(
            "requires_limit"
        )
        and not has_limit(
            statement
        )
    ):
        errors.append(
            "LIMIT/FETCH is required."
        )

    expected_limit = (
        alternative.get(
            "expected_limit"
        )
    )

    if expected_limit is not None:
        actual_limit = (
            get_limit_value(
                statement
            )
        )

        if (
            actual_limit
            != expected_limit
        ):
            errors.append(
                "Incorrect LIMIT. "
                f"Expected {expected_limit}, "
                f"got {actual_limit}."
            )

    return errors


# ==========================================================
# EVALUATION
# ==========================================================


def evaluate_case(
    sql: str,
    expectations: dict,
) -> tuple[bool, list[str]]:
    """
    Evaluate generated SQL against deterministic semantic
    expectations.

    This evaluator intentionally checks semantic structure
    rather than requiring one exact SQL string.
    """

    errors: list[str] = []

    # ------------------------------------------------------
    # Insufficient information
    # ------------------------------------------------------

    if expectations.get(
        "expected_insufficient"
    ):
        if not is_insufficient_query(
            sql
        ):
            errors.append(
                "Expected insufficient-information response."
            )

        return (
            not errors,
            errors,
        )

    # ------------------------------------------------------
    # Parse SQL
    # ------------------------------------------------------

    try:
        statement = parse_one(
            sql,
            read="postgres",
        )
    except (
        ParseError,
        ValueError,
        TypeError,
    ) as exc:
        return (
            False,
            [
                "SQL could not be parsed: "
                f"{exc}"
            ],
        )

    if statement is None:
        return (
            False,
            [
                "SQL could not be parsed."
            ],
        )

    tables = extract_tables(
        statement
    )

    columns = extract_columns(
        statement
    )

    aggregates = extract_aggregates(
        statement
    )

    # ------------------------------------------------------
    # Tables
    # ------------------------------------------------------

    missing_tables = (
        set(
            expectations.get(
                "required_tables",
                set(),
            )
        )
        - tables
    )

    if missing_tables:
        errors.append(
            "Missing table(s): "
            + ", ".join(
                sorted(
                    missing_tables
                )
            )
        )

    # ------------------------------------------------------
    # Columns
    # ------------------------------------------------------

    missing_columns = (
        set(
            expectations.get(
                "required_columns",
                set(),
            )
        )
        - columns
    )

    if missing_columns:
        errors.append(
            "Missing column(s): "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    # ------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------

    missing_aggregates = (
        set(
            expectations.get(
                "required_aggregates",
                set(),
            )
        )
        - aggregates
    )

    if missing_aggregates:
        errors.append(
            "Missing aggregate(s): "
            + ", ".join(
                sorted(
                    missing_aggregates
                )
            )
        )

    # ------------------------------------------------------
    # WHERE
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_where"
        )
        and not has_where(
            statement
        )
    ):
        errors.append(
            "WHERE clause is required."
        )

    # ------------------------------------------------------
    # Required literals
    # ------------------------------------------------------

    required_literals = {
        str(value).lower()
        for value in expectations.get(
            "required_literals",
            set(),
        )
    }

    if required_literals:
        actual_literals = {
            value.lower()
            for value in extract_literals(
                statement
            )
        }

        missing_literals = (
            required_literals
            - actual_literals
        )

        if missing_literals:
            errors.append(
                "Missing required literal(s): "
                + ", ".join(
                    sorted(
                        missing_literals
                    )
                )
            )
    # ------------------------------------------------------
    # Required comparison operators
    # ------------------------------------------------------

    required_comparisons = {
        str(operator).upper()
        for operator in expectations.get(
            "required_comparisons",
            set(),
        )
    }

    if required_comparisons:
        actual_comparisons = {
            operator.upper()
            for operator
            in extract_comparison_operators(
                statement
            )
        }

        missing_comparisons = (
            required_comparisons
            - actual_comparisons
        )

        if missing_comparisons:
            errors.append(
                "Missing required comparison operator(s): "
                + ", ".join(
                    sorted(
                        missing_comparisons
                    )
                )
            )

    # ------------------------------------------------------
    # JOIN
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_join"
        )
        and not has_join(
            statement
        )
    ):
        errors.append(
            "JOIN is required."
        )

    # ------------------------------------------------------
    # GROUP BY
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_group_by"
        )
        and not has_group_by(
            statement
        )
    ):
        errors.append(
            "GROUP BY is required."
        )

    # ------------------------------------------------------
    # ORDER BY
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_order_by"
        )
        and not has_order_by(
            statement
        )
    ):
        errors.append(
            "ORDER BY is required."
        )

    expected_direction = (
        expectations.get(
            "order_direction"
        )
    )

    if expected_direction:
        actual_direction = (
            get_order_direction(
                statement
            )
        )

        if (
            actual_direction
            != expected_direction
        ):
            errors.append(
                "Incorrect ORDER BY direction. "
                f"Expected {expected_direction}, "
                f"got {actual_direction}."
            )

    # ------------------------------------------------------
    # LIMIT
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_limit"
        )
        and not has_limit(
            statement
        )
    ):
        errors.append(
            "LIMIT/FETCH is required."
        )

    expected_limit = (
        expectations.get(
            "expected_limit"
        )
    )

    if expected_limit is not None:
        actual_limit = (
            get_limit_value(
                statement
            )
        )

        if (
            actual_limit
            != expected_limit
        ):
            errors.append(
                "Incorrect LIMIT. "
                f"Expected {expected_limit}, "
                f"got {actual_limit}."
            )

    # ------------------------------------------------------
    # SELECT DISTINCT
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_distinct"
        )
        and not has_distinct(
            statement
        )
    ):
        errors.append(
            "DISTINCT is required."
        )

    # ------------------------------------------------------
    # DISTINCT aggregate
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_distinct_aggregate"
        )
        and not has_distinct_aggregate(
            statement
        )
    ):
        errors.append(
            "DISTINCT aggregate is required."
        )

    # ------------------------------------------------------
    # Revenue expression
    # ------------------------------------------------------

    if (
        expectations.get(
            "requires_revenue_expression"
        )
        and not has_revenue_expression(
            statement
        )
    ):
        errors.append(
            "Revenue expression must use "
            "quantity * unit_price."
        )

    # ------------------------------------------------------
    # Date granularity
    # ------------------------------------------------------

    required_granularity = (
        expectations.get(
            "required_date_granularity"
        )
    )

    if required_granularity:
        granularities = (
            extract_date_granularities(
                statement
            )
        )

        if (
            required_granularity.lower()
            not in granularities
        ):
            errors.append(
                "Incorrect or missing date granularity. "
                f"Expected {required_granularity}."
            )

    # ------------------------------------------------------
    # Semantic alternatives
    # ------------------------------------------------------

    alternatives = expectations.get(
        "semantic_alternatives",
        [],
    )

    if alternatives:
        alternative_results = [
            evaluate_semantic_alternative(
                statement=statement,
                alternative=alternative,
            )
            for alternative in alternatives
        ]

        if not any(
            not alternative_errors
            for alternative_errors
            in alternative_results
        ):
            errors.append(
                "None of the accepted semantic "
                "alternatives matched."
            )

            for (
                alternative_index,
                alternative_errors,
            ) in enumerate(
                alternative_results,
                start=1,
            ):
                errors.append(
                    f"Alternative {alternative_index}: "
                    + "; ".join(
                        alternative_errors
                    )
                )

    return (
        not errors,
        errors,
    )