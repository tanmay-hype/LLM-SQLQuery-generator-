import argparse
import re

from sqlglot import exp, parse_one

from app.services.query_service import QueryService


# ==========================================================
# GENERALIZATION TEST CASES
# ==========================================================

TEST_CASES = [
    # ------------------------------------------------------
    # LOOKUP
    # ------------------------------------------------------

    {
        "question": "Show all customers",
        "required_tables": {
            "customers",
        },
    },
    {
        "question": "List customer names and emails",
        "required_tables": {
            "customers",
        },
        "required_columns": {
            "name",
            "email",
        },
    },
    {
        "question": "Show products and their prices",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "name",
            "price",
        },
    },

    # ------------------------------------------------------
    # FILTER
    # ------------------------------------------------------

    {
        "question": "Show customers from Delhi",
        "required_tables": {
            "customers",
        },
        "required_columns": {
            "city",
        },
        "requires_where": True,
    },
    {
        "question": "Find products in the Electronics category",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "category",
        },
        "requires_where": True,
    },

    # ------------------------------------------------------
    # JOINS
    # ------------------------------------------------------

    {
        "question": "Which customers have placed orders?",
        "required_tables": {
            "customers",
            "orders",
        },
        "requires_join": True,
    },
    {
        "question": "Which products have been ordered?",
        "required_tables": {
            "products",
            "order_items",
        },
        "requires_join": True,
    },
    {
        "question": "Show customers and the products they purchased",
        "required_tables": {
            "customers",
            "orders",
            "order_items",
            "products",
        },
        "requires_join": True,
    },

    # ------------------------------------------------------
    # AGGREGATION
    # ------------------------------------------------------

    {
        "question": "How many customers are there?",
        "required_tables": {
            "customers",
        },
        "required_aggregates": {
            "COUNT",
        },
    },
    {
        "question": "What is the total value of all orders?",
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
    },
    {
        "question": "What is the average order amount?",
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "required_aggregates": {
            "AVG",
        },
    },

    # ------------------------------------------------------
    # IMPORTANT:
    #
    # Both of these are semantically valid:
    #
    #   SELECT MAX(price) FROM products;
    #
    # and:
    #
    #   SELECT price
    #   FROM products
    #   ORDER BY price DESC
    #   LIMIT 1;
    #
    # Therefore this case accepts either implementation.
    # ------------------------------------------------------

    {
        "question": "What is the highest product price?",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
        "semantic_alternatives": [
            {
                "required_aggregates": {
                    "MAX",
                },
            },
            {
                "requires_order_by": True,
                "order_direction": "DESC",
                "requires_limit": True,
                "expected_limit": 1,
            },
        ],
    },

    # ------------------------------------------------------
    # GROUP BY
    # ------------------------------------------------------

    {
        "question": "Show total spending per customer",
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
    },
    {
        "question": "Show product count by category",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "category",
        },
        "required_aggregates": {
            "COUNT",
        },
        "requires_group_by": True,
    },
    {
        "question": "Show order totals by customer",
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
    },

    # ------------------------------------------------------
    # SORT / TOP-N
    # ------------------------------------------------------

    {
        "question": "Show the most expensive product",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
        "requires_order_by": True,
        "order_direction": "DESC",
        "requires_limit": True,
    },
    {
        "question": "Show the cheapest product",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
        "requires_order_by": True,
        "order_direction": "ASC",
        "requires_limit": True,
    },
    {
        "question": "Show the top 3 customers by spending",
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
        "expected_limit": 3,
    },

    # ------------------------------------------------------
    # TIME SERIES
    # ------------------------------------------------------

    {
        "question": "Show monthly sales",
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "required_date_granularity": "month",
    },
    {
        "question": "Show daily order activity",
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "required_date_granularity": "day",
    },
    {
        "question": "Show sales by year",
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "required_date_granularity": "year",
    },

    # ------------------------------------------------------
    # MULTI-HOP
    # ------------------------------------------------------

    {
        "question": "Which customers bought the most items?",
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
        "required_columns": {
            "quantity",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
    },
    {
        "question": "Which products generated the most sales?",
        "required_tables": {
            "products",
            "order_items",
        },
        "required_columns": {
            "quantity",
            "unit_price",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
    },

    # ------------------------------------------------------
    # SYNONYMS
    # ------------------------------------------------------

    {
        "question": "Which buyers spent the most?",
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
    },
    {
        "question": "Show merchandise prices",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
    },
    {
        "question": "Show purchase activity over time",
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
        },
        "requires_order_by": True,
    },

    # ------------------------------------------------------
    # DISTINCT / EXISTENCE
    # ------------------------------------------------------

    {
        "question": "Which customers have ever ordered?",
        "required_tables": {
            "customers",
            "orders",
        },
        "requires_join": True,
        "requires_distinct": True,
    },
    {
        "question": "Which products have actually been purchased?",
        "required_tables": {
            "products",
            "order_items",
        },
        "requires_join": True,
        "requires_distinct": True,
    },

    # ------------------------------------------------------
    # COMPARISON
    # ------------------------------------------------------

    {
        "question": "Compare customer spending",
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
    },

    # ------------------------------------------------------
    # IMPOSSIBLE / HALLUCINATION
    # ------------------------------------------------------

    {
        "question": "Show customer phone numbers",
        "expected_insufficient": True,
    },
    {
        "question": "Show employee salaries",
        "expected_insufficient": True,
    },
    {
        "question": "Show shipment tracking numbers",
        "expected_insufficient": True,
    },
]


# ==========================================================
# AST HELPERS
# ==========================================================

def extract_tables(
    statement,
) -> set[str]:

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
            except Exception:
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
            except Exception:
                pass

    return None


def has_distinct(
    statement,
) -> bool:

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
# DATE_TRUNC EXTRACTION
# ==========================================================

def extract_date_granularities(
    statement,
) -> set[str]:

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
# SEMANTIC ALTERNATIVE EVALUATION
# ==========================================================

def evaluate_semantic_alternative(
    statement,
    alternative: dict,
) -> list[str]:
    """
    Evaluate one acceptable implementation of a semantic
    requirement.

    Example:

        "highest product price"

    may be implemented as either:

        MAX(price)

    or:

        ORDER BY price DESC
        LIMIT 1
    """

    errors: list[str] = []

    aggregates = extract_aggregates(
        statement
    )

    # ------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # ORDER BY
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # LIMIT
    # ------------------------------------------------------

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

    errors: list[str] = []

    # ------------------------------------------------------
    # Insufficient-information expectation
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

    statement = parse_one(
        sql,
        read="postgres",
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
    # DISTINCT
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

    alternatives = (
        expectations.get(
            "semantic_alternatives",
            [],
        )
    )

    if alternatives:

        alternative_results = [
            evaluate_semantic_alternative(
                statement=statement,
                alternative=alternative,
            )
            for alternative in alternatives
        ]

        alternative_passed = any(
            not alternative_errors
            for alternative_errors
            in alternative_results
        )

        if not alternative_passed:

            errors.append(
                "None of the accepted semantic "
                "alternatives matched."
            )

            for index, alternative_errors in enumerate(
                alternative_results,
                start=1,
            ):

                errors.append(
                    f"Alternative {index}: "
                    + "; ".join(
                        alternative_errors
                    )
                )

    return (
        not errors,
        errors,
    )


# ==========================================================
# TEST SELECTION
# ==========================================================

def parse_test_numbers(
    value: str,
) -> list[int]:
    """
    Parse:

        --tests 2,4,8,12

    into:

        [2, 4, 8, 12]
    """

    values: list[int] = []

    for item in value.split(","):

        item = item.strip()

        if not item:
            continue

        try:
            number = int(
                item
            )
        except ValueError as exc:

            raise argparse.ArgumentTypeError(
                f"Invalid test number: {item}"
            ) from exc

        values.append(
            number
        )

    if not values:

        raise argparse.ArgumentTypeError(
            "At least one test number is required."
        )

    return values


def get_selected_tests(
    single_test: int | None,
    multiple_tests: list[int] | None,
    run_all: bool,
) -> list[tuple[int, dict]]:
    """
    Return selected benchmark cases.

    IMPORTANT:

    Without --all, --test, or --tests, no expensive
    benchmark is executed accidentally.
    """

    total = len(
        TEST_CASES
    )

    if run_all:

        return list(
            enumerate(
                TEST_CASES,
                start=1,
            )
        )

    requested: list[int] = []

    if single_test is not None:
        requested.append(
            single_test
        )

    if multiple_tests:
        requested.extend(
            multiple_tests
        )

    # Remove duplicates while preserving order.
    requested = list(
        dict.fromkeys(
            requested
        )
    )

    if not requested:

        return []

    invalid = [
        number
        for number in requested
        if (
            number < 1
            or number > total
        )
    ]

    if invalid:

        raise ValueError(
            "Invalid test number(s): "
            + ", ".join(
                str(number)
                for number in invalid
            )
            + f". Valid range is 1-{total}."
        )

    return [
        (
            number,
            TEST_CASES[
                number - 1
            ],
        )
        for number in requested
    ]


# ==========================================================
# LIST TESTS
# ==========================================================

def list_tests() -> None:

    print("=" * 80)
    print(
        "AVAILABLE GENERALIZATION TESTS"
    )
    print("=" * 80)

    for index, test in enumerate(
        TEST_CASES,
        start=1,
    ):

        print(
            f"{index:>2}: "
            f"{test['question']}"
        )

    print("=" * 80)


# ==========================================================
# ARGUMENT PARSER
# ==========================================================

def build_argument_parser(
) -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Run SQL generalization benchmark tests "
            "without unnecessarily invoking the LLM "
            "for every benchmark case."
        )
    )

    parser.add_argument(
        "--test",
        type=int,
        help=(
            "Run one test only. "
            "Example: --test 12"
        ),
    )

    parser.add_argument(
        "--tests",
        type=parse_test_numbers,
        help=(
            "Run selected tests. "
            "Example: --tests 2,4,8,12"
        ),
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run the complete benchmark. "
            "This may cause many LLM API calls."
        ),
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help=(
            "List available tests without "
            "calling the LLM."
        ),
    )

    return parser


# ==========================================================
# MAIN BENCHMARK
# ==========================================================

def main():

    parser = (
        build_argument_parser()
    )

    args = parser.parse_args()

    # ------------------------------------------------------
    # List mode
    #
    # Costs zero LLM calls.
    # ------------------------------------------------------

    if args.list:

        list_tests()

        return

    # ------------------------------------------------------
    # Select tests
    # ------------------------------------------------------

    try:

        selected_tests = (
            get_selected_tests(
                single_test=args.test,
                multiple_tests=args.tests,
                run_all=args.all,
            )
        )

    except ValueError as exc:

        parser.error(
            str(exc)
        )

        return

    # ------------------------------------------------------
    # Protect against accidental expensive runs.
    # ------------------------------------------------------

    if not selected_tests:

        print("=" * 80)
        print(
            "NO TESTS EXECUTED"
        )
        print("=" * 80)

        print(
            "Choose one of:"
        )

        print()
        print(
            "  --test 12"
        )

        print(
            "  --tests 2,4,8,12"
        )

        print(
            "  --all"
        )

        print(
            "  --list"
        )

        print()
        print(
            "The full benchmark is not run "
            "automatically to avoid unnecessary "
            "LLM API charges."
        )

        print("=" * 80)

        return

    print("=" * 80)
    print(
        "SQL GENERALIZATION BENCHMARK"
    )
    print("=" * 80)

    print(
        "SELECTED TESTS:",
        [
            number
            for number, _
            in selected_tests
        ],
    )

    print(
        "TEST COUNT:",
        len(
            selected_tests
        ),
    )

    print("=" * 80)

    # ------------------------------------------------------
    # QueryService is only initialized when we're
    # actually going to execute benchmark cases.
    # ------------------------------------------------------

    service = QueryService()

    passed = 0

    failed = 0

    errors_count = 0

    # ======================================================
    # RUN TESTS
    # ======================================================

    for (
        test_number,
        test,
    ) in selected_tests:

        question = (
            test[
                "question"
            ]
        )

        print()
        print("=" * 80)

        print(
            f"TEST {test_number}: "
            f"{question}"
        )

        print("=" * 80)

        try:

            # ----------------------------------------------
            # Full production pipeline.
            #
            # This is the expensive part because the
            # configured LLM may be called.
            # ----------------------------------------------

            response = (
                service.generate_sql(
                    question
                )
            )

            sql = (
                response.sql
            )

            valid, evaluation_errors = (
                evaluate_case(
                    sql=sql,
                    expectations=test,
                )
            )

            print()
            print(
                "GENERATED SQL:"
            )

            print("-" * 80)

            print(
                sql
            )

            print()

            if valid:

                print(
                    "STATUS: PASS"
                )

                passed += 1

            else:

                print(
                    "STATUS: FAIL"
                )

                for error in (
                    evaluation_errors
                ):

                    print(
                        "ERROR:",
                        error,
                    )

                failed += 1

        except Exception as exc:

            errors_count += 1

            print()
            print(
                "STATUS: ERROR"
            )

            print(
                "EXCEPTION:",
                type(exc).__name__,
            )

            print(
                "MESSAGE:",
                str(exc),
            )

    # ======================================================
    # SUMMARY
    # ======================================================

    total = len(
        selected_tests
    )

    evaluated = (
        passed
        + failed
    )

    semantic_accuracy = (
        (
            passed
            / evaluated
            * 100
        )
        if evaluated
        else 0.0
    )

    evaluation_completion = (
        (
            evaluated
            / total
            * 100
        )
        if total
        else 0.0
    )

    print()
    print("=" * 80)

    print(
        "SQL GENERALIZATION SUMMARY"
    )

    print("=" * 80)

    print(
        f"PASSED: {passed}"
    )

    print(
        f"FAILED: {failed}"
    )

    print(
        f"ERRORS: {errors_count}"
    )

    print(
        f"TOTAL EXECUTED: {total}"
    )

    print(
        "SEMANTIC ACCURACY: "
        f"{semantic_accuracy:.2f}%"
    )

    print(
        "EVALUATION COMPLETION: "
        f"{evaluation_completion:.2f}%"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()