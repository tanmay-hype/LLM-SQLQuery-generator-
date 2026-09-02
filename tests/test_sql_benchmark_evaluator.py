from tests.sql_benchmark_evaluator import (
    evaluate_case,
)


def assert_pass(
    name: str,
    sql: str,
    expectations: dict,
) -> None:

    passed, errors = evaluate_case(
        sql=sql,
        expectations=expectations,
    )

    if not passed:
        raise AssertionError(
            f"{name} should PASS.\n"
            f"Errors: {errors}\n"
            f"SQL: {sql}"
        )

    print(f"[PASS] {name}")


def assert_fail(
    name: str,
    sql: str,
    expectations: dict,
) -> None:

    passed, errors = evaluate_case(
        sql=sql,
        expectations=expectations,
    )

    if passed:
        raise AssertionError(
            f"{name} should FAIL.\n"
            f"SQL: {sql}"
        )

    print(f"[PASS] {name}")


def main() -> None:

    # =====================================================
    # REQUIRED LITERALS
    # =====================================================

    assert_pass(
        "Required string literal",
        """
        SELECT *
        FROM customers
        WHERE city = 'Mumbai'
        """,
        {
            "required_tables": {"customers"},
            "required_columns": {"city"},
            "requires_where": True,
            "required_literals": {"Mumbai"},
        },
    )

    assert_fail(
        "Wrong string literal rejected",
        """
        SELECT *
        FROM customers
        WHERE city = 'Delhi'
        """,
        {
            "required_tables": {"customers"},
            "requires_where": True,
            "required_literals": {"Mumbai"},
        },
    )

    assert_pass(
        "Numeric literals",
        """
        SELECT *
        FROM products
        WHERE price BETWEEN 500 AND 2000
        """,
        {
            "required_tables": {"products"},
            "required_columns": {"price"},
            "requires_where": True,
            "required_literals": {"500", "2000"},
        },
    )

    assert_fail(
        "Missing numeric boundary rejected",
        """
        SELECT *
        FROM products
        WHERE price > 500
        """,
        {
            "required_tables": {"products"},
            "requires_where": True,
            "required_literals": {"500", "2000"},
        },
    )

    # =====================================================
    # DISTINCT AGGREGATE
    # =====================================================

    assert_pass(
        "COUNT DISTINCT accepted",
        """
        SELECT
            c.name,
            COUNT(DISTINCT oi.product_id)
        FROM customers c
        JOIN orders o
            ON o.customer_id = c.id
        JOIN order_items oi
            ON oi.order_id = o.id
        GROUP BY c.name
        """,
        {
            "required_tables": {
                "customers",
                "orders",
                "order_items",
            },
            "required_aggregates": {"COUNT"},
            "requires_group_by": True,
            "requires_distinct_aggregate": True,
        },
    )

    assert_fail(
        "Plain COUNT rejected when DISTINCT required",
        """
        SELECT
            c.name,
            COUNT(oi.product_id)
        FROM customers c
        JOIN orders o
            ON o.customer_id = c.id
        JOIN order_items oi
            ON oi.order_id = o.id
        GROUP BY c.name
        """,
        {
            "required_tables": {
                "customers",
                "orders",
                "order_items",
            },
            "required_aggregates": {"COUNT"},
            "requires_group_by": True,
            "requires_distinct_aggregate": True,
        },
    )

    # =====================================================
    # REVENUE EXPRESSION
    # =====================================================

    assert_pass(
        "Revenue multiplication accepted",
        """
        SELECT
            p.name,
            SUM(
                oi.quantity * oi.unit_price
            ) AS revenue
        FROM products p
        JOIN order_items oi
            ON oi.product_id = p.id
        GROUP BY p.name
        """,
        {
            "required_tables": {
                "products",
                "order_items",
            },
            "required_columns": {
                "quantity",
                "unit_price",
            },
            "required_aggregates": {"SUM"},
            "requires_group_by": True,
            "requires_revenue_expression": True,
        },
    )

    assert_fail(
        "Quantity-only revenue rejected",
        """
        SELECT
            p.name,
            SUM(oi.quantity) AS revenue
        FROM products p
        JOIN order_items oi
            ON oi.product_id = p.id
        GROUP BY p.name
        """,
        {
            "required_tables": {
                "products",
                "order_items",
            },
            "required_aggregates": {"SUM"},
            "requires_revenue_expression": True,
        },
    )

    assert_fail(
        "Unit-price-only revenue rejected",
        """
        SELECT
            p.name,
            SUM(oi.unit_price) AS revenue
        FROM products p
        JOIN order_items oi
            ON oi.product_id = p.id
        GROUP BY p.name
        """,
        {
            "required_tables": {
                "products",
                "order_items",
            },
            "required_aggregates": {"SUM"},
            "requires_revenue_expression": True,
        },
    )

    # =====================================================
    # EXACT LIMIT
    # =====================================================

    assert_pass(
        "Exact LIMIT accepted",
        """
        SELECT *
        FROM products
        ORDER BY price ASC
        LIMIT 5
        """,
        {
            "required_tables": {"products"},
            "required_columns": {"price"},
            "requires_order_by": True,
            "order_direction": "ASC",
            "expected_limit": 5,
        },
    )

    assert_fail(
        "Wrong LIMIT rejected",
        """
        SELECT *
        FROM products
        ORDER BY price ASC
        LIMIT 10
        """,
        {
            "required_tables": {"products"},
            "requires_order_by": True,
            "order_direction": "ASC",
            "expected_limit": 5,
        },
    )

    # =====================================================
    # DATE GRANULARITY
    # =====================================================

    assert_pass(
        "Monthly DATE_TRUNC accepted",
        """
        SELECT
            DATE_TRUNC(
                'month',
                order_date
            ) AS month,
            COUNT(*)
        FROM orders
        GROUP BY
            DATE_TRUNC(
                'month',
                order_date
            )
        """,
        {
            "required_tables": {"orders"},
            "required_columns": {"order_date"},
            "required_aggregates": {"COUNT"},
            "requires_group_by": True,
            "required_date_granularity": "month",
        },
    )

    assert_fail(
        "Wrong DATE_TRUNC granularity rejected",
        """
        SELECT
            DATE_TRUNC(
                'year',
                order_date
            ),
            COUNT(*)
        FROM orders
        GROUP BY
            DATE_TRUNC(
                'year',
                order_date
            )
        """,
        {
            "required_tables": {"orders"},
            "required_date_granularity": "month",
        },
    )

    # =====================================================
    # INSUFFICIENT INFORMATION
    # =====================================================

    assert_pass(
        "Insufficient information accepted",
        """
        SELECT 'Insufficient information';
        """,
        {
            "expected_insufficient": True,
        },
    )

    assert_fail(
        "Invented schema rejected by expectation",
        """
        SELECT phone
        FROM customers;
        """,
        {
            "expected_insufficient": True,
        },
    )
    
    
        # =====================================================
    # COMPARISON OPERATORS
    # =====================================================

    assert_pass(
        "Greater-than comparison accepted",
        """
        SELECT *
        FROM products
        WHERE price > 1000
        """,
        {
            "required_tables": {"products"},
            "requires_where": True,
            "required_literals": {"1000"},
            "required_comparisons": {">"},
        },
    )

    assert_fail(
        "Wrong comparison direction rejected",
        """
        SELECT *
        FROM products
        WHERE price < 1000
        """,
        {
            "required_tables": {"products"},
            "requires_where": True,
            "required_literals": {"1000"},
            "required_comparisons": {">"},
        },
    )

    assert_pass(
        "Not-equal comparison accepted",
        """
        SELECT *
        FROM customers
        WHERE city != 'Delhi'
        """,
        {
            "required_tables": {"customers"},
            "requires_where": True,
            "required_literals": {"Delhi"},
            "required_comparisons": {"!="},
        },
    )

    assert_fail(
        "Equality rejected when not-equal required",
        """
        SELECT *
        FROM customers
        WHERE city = 'Delhi'
        """,
        {
            "required_tables": {"customers"},
            "requires_where": True,
            "required_literals": {"Delhi"},
            "required_comparisons": {"!="},
        },
    )

    assert_pass(
        "BETWEEN comparison accepted",
        """
        SELECT *
        FROM products
        WHERE price BETWEEN 500 AND 2000
        """,
        {
            "required_tables": {"products"},
            "requires_where": True,
            "required_literals": {"500", "2000"},
            "required_comparisons": {"BETWEEN"},
        },
    )

    assert_fail(
        "Incomplete range rejected",
        """
        SELECT *
        FROM products
        WHERE price >= 500
        """,
        {
            "required_tables": {"products"},
            "requires_where": True,
            "required_literals": {"500", "2000"},
            "required_comparisons": {"BETWEEN"},
        },
    )

    # =====================================================
    # COMBINED V2 REQUIREMENTS
    # =====================================================

    assert_pass(
        "Combined ranking revenue query",
        """
        SELECT
            p.name,
            SUM(
                oi.quantity * oi.unit_price
            ) AS revenue
        FROM products p
        JOIN order_items oi
            ON oi.product_id = p.id
        GROUP BY p.name
        ORDER BY revenue DESC
        LIMIT 3
        """,
        {
            "required_tables": {
                "products",
                "order_items",
            },
            "required_columns": {
                "quantity",
                "unit_price",
            },
            "required_aggregates": {"SUM"},
            "requires_join": True,
            "requires_group_by": True,
            "requires_revenue_expression": True,
            "requires_order_by": True,
            "order_direction": "DESC",
            "expected_limit": 3,
        },
    )

    assert_fail(
        "Combined query wrong direction rejected",
        """
        SELECT
            p.name,
            SUM(
                oi.quantity * oi.unit_price
            ) AS revenue
        FROM products p
        JOIN order_items oi
            ON oi.product_id = p.id
        GROUP BY p.name
        ORDER BY revenue ASC
        LIMIT 3
        """,
        {
            "required_tables": {
                "products",
                "order_items",
            },
            "required_aggregates": {"SUM"},
            "requires_join": True,
            "requires_group_by": True,
            "requires_revenue_expression": True,
            "requires_order_by": True,
            "order_direction": "DESC",
            "expected_limit": 3,
        },
    )

    print()
    print(
        "ALL SQL BENCHMARK EVALUATOR TESTS PASSED"
    )


if __name__ == "__main__":
    main()