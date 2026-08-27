import re

from sqlglot import exp, parse_one

from app.services.query_service import QueryService


TEST_CASES = [
    {
        "question": "Who has spent the most?",
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
        "requires_order_by": True,
        "order_direction": "DESC",
        "requires_limit": True,
    },
    {
        "question": "Show buyers and their total purchases",
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
        "question": "Which catalog items are most valuable?",
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
        "requires_order_by": True,
        "order_direction": "DESC",
    },
    {
        "question": "Give me sales activity by month",
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
        "question": (
            "Which people bought the greatest "
            "number of items?"
        ),
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
        "question": (
            "Show the value of purchases "
            "for each buyer"
        ),
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
        "question": (
            "Which merchandise has actually "
            "been purchased?"
        ),
        "required_tables": {
            "products",
            "order_items",
        },
        "requires_distinct": True,
    },
    {
        "question": "Show purchase history over time",
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
        },
        "requires_order_by": True,
    },
    {
        "question": (
            "Which buyers purchased the largest "
            "number of products?"
        ),
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
        "question": (
            "Show item categories and their prices"
        ),
        "required_tables": {
            "products",
        },
        "required_columns": {
            "category",
            "price",
        },
    },
    {
        "question": (
            "Which buyers placed transactions?"
        ),
        "required_tables": {
            "customers",
            "orders",
        },
        "requires_distinct": True,
    },
    {
        "question": (
            "Which items produced the highest "
            "sales value?"
        ),
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
]


def extract_tables(statement) -> set[str]:
    cte_names = {
        cte.alias_or_name
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }

    tables = set()

    for table in statement.find_all(exp.Table):

        table_name = table.name

        if (
            table_name
            and table_name not in cte_names
        ):
            tables.add(
                table_name
            )

    return tables


def extract_columns(statement) -> set[str]:
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
    aggregates = set()

    for node in statement.find_all(
        exp.AggFunc
    ):
        aggregates.add(
            node.key.upper()
        )

    return aggregates


def has_group_by(statement) -> bool:
    return (
        statement.find(exp.Group)
        is not None
    )


def has_order_by(statement) -> bool:
    return (
        statement.find(exp.Order)
        is not None
    )


def has_limit(statement) -> bool:
    return (
        statement.find(exp.Limit)
        is not None
        or statement.find(exp.Fetch)
        is not None
    )


def has_distinct(statement) -> bool:
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

    ordered_expressions = (
        order.expressions
    )

    if not ordered_expressions:
        return None

    first = ordered_expressions[0]

    if isinstance(
        first,
        exp.Ordered,
    ):
        return (
            "DESC"
            if first.args.get("desc")
            else "ASC"
        )

    return None


def extract_date_granularities(
    statement,
) -> set[str]:
    """
    Extract DATE_TRUNC granularities from parsed SQL.

    Examples:

        DATE_TRUNC('month', order_date)
            -> {"month"}

        DATE_TRUNC('day', order_date)
            -> {"day"}
    """

    granularities: set[str] = set()

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

    for value in matches:

        normalized = (
            value
            .strip()
            .lower()
        )

        if normalized:
            granularities.add(
                normalized
            )

    return granularities

def evaluate_case(
    sql: str,
    expectations: dict,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

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

    required_tables = set(
        expectations.get(
            "required_tables",
            set(),
        )
    )

    missing_tables = (
        required_tables
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

    required_columns = set(
        expectations.get(
            "required_columns",
            set(),
        )
    )

    missing_columns = (
        required_columns
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

    required_aggregates = set(
        expectations.get(
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

    return (
        not errors,
        errors,
    )


def main():

    print("=" * 80)
    print(
        "SQL SEMANTIC ACCURACY TEST"
    )
    print("=" * 80)

    service = QueryService()

    passed = 0
    failed = 0

    for index, test in enumerate(
        TEST_CASES,
        start=1,
    ):

        question = test[
            "question"
        ]

        print()
        print("=" * 80)
        print(
            f"TEST {index}: {question}"
        )
        print("=" * 80)

        try:

            response = (
                service.generate_sql(
                    question
                )
            )

            sql = response.sql

            valid, errors = (
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
            print(sql)

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

                for error in errors:
                    print(
                        "ERROR:",
                        error,
                    )

                failed += 1

        except Exception as exc:

            print()
            print(
                "STATUS: EXCEPTION"
            )

            print(
                "EXCEPTION:",
                type(exc).__name__,
            )

            print(
                "MESSAGE:",
                str(exc),
            )

            failed += 1

    total = len(
        TEST_CASES
    )

    accuracy = (
        passed
        / total
        * 100
    )

    print()
    print("=" * 80)
    print(
        "SQL SEMANTIC ACCURACY SUMMARY"
    )
    print("=" * 80)

    print(
        f"PASSED: {passed}"
    )

    print(
        f"FAILED: {failed}"
    )

    print(
        f"TOTAL:  {total}"
    )

    print(
        f"SEMANTIC ACCURACY: "
        f"{accuracy:.2f}%"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()