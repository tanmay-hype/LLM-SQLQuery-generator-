from app.exceptions import SQLValidationError
from app.services.validator import SQLValidator


SCHEMA = {
    "orders": {
        "columns": [
            {"name": "id"},
            {"name": "customer_id"},
            {"name": "order_date"},
            {"name": "total_amount"},
        ],
        "foreign_keys": [],
    },
}


def assert_valid(
    sql: str,
    label: str,
) -> None:

    SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    print(
        f"[PASS] {label}"
    )


def assert_invalid(
    sql: str,
    label: str,
) -> None:

    try:

        SQLValidator.validate(
            sql=sql,
            schema=SCHEMA,
        )

    except SQLValidationError as exc:

        assert (
            "not included in group by"
            in str(exc).lower()
        ), str(exc)

        print(
            f"[PASS] {label}"
        )

        return

    raise AssertionError(
        f"Expected SQLValidationError: {label}"
    )


def main():
    print("=" * 70)
    print("AGGREGATE PROJECTION VALIDATION TEST")
    print("=" * 70)

    # ------------------------------------------------------
    # 1. Pure aggregate
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT SUM(total_amount)
        FROM orders;
        """,
        "Pure aggregate accepted",
    )

    # ------------------------------------------------------
    # 2. Multiple pure aggregates
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            SUM(total_amount),
            COUNT(id)
        FROM orders;
        """,
        "Multiple aggregates accepted",
    )

    # ------------------------------------------------------
    # 3. Correct grouped column
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            customer_id,
            SUM(total_amount)
        FROM orders
        GROUP BY customer_id;
        """,
        "Grouped aggregate accepted",
    )

    # ------------------------------------------------------
    # 4. Missing GROUP BY
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT
            customer_id,
            SUM(total_amount)
        FROM orders;
        """,
        "Missing GROUP BY rejected",
    )

    # ------------------------------------------------------
    # 5. Wrong GROUP BY column
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT
            customer_id,
            SUM(total_amount)
        FROM orders
        GROUP BY order_date;
        """,
        "Wrong GROUP BY column rejected",
    )

    # ------------------------------------------------------
    # 6. Grouped expression
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            DATE_TRUNC(
                'month',
                order_date
            ),
            SUM(total_amount)
        FROM orders
        GROUP BY DATE_TRUNC(
            'month',
            order_date
        );
        """,
        "Grouped expression accepted",
    )

    # ------------------------------------------------------
    # 7. Missing grouped expression
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT
            DATE_TRUNC(
                'month',
                order_date
            ),
            SUM(total_amount)
        FROM orders;
        """,
        "Ungrouped expression rejected",
    )

    # ------------------------------------------------------
    # 8. SELECT alias used in GROUP BY
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            DATE_TRUNC(
                'month',
                order_date
            ) AS month,
            SUM(total_amount)
        FROM orders
        GROUP BY month;
        """,
        "GROUP BY SELECT alias accepted",
    )

    # ------------------------------------------------------
    # 9. Constant with aggregate
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            'all' AS category,
            COUNT(*)
        FROM orders;
        """,
        "Constant with aggregate accepted",
    )

    # ------------------------------------------------------
    # 10. Aggregate wrapped in function
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            COALESCE(
                SUM(total_amount),
                0
            )
        FROM orders;
        """,
        "Wrapped aggregate accepted",
    )

    # ------------------------------------------------------
    # 11. Aggregate arithmetic
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            SUM(total_amount) + 10
        FROM orders;
        """,
        "Aggregate arithmetic accepted",
    )

    # ------------------------------------------------------
    # 12. Mixed aggregate/non-aggregate expression
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT
            customer_id
            + SUM(total_amount)
        FROM orders;
        """,
        (
            "Mixed aggregate/non-aggregate "
            "expression rejected"
        ),
    )

    # ------------------------------------------------------
    # 13. Mixed expression with grouped column
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            customer_id
            + SUM(total_amount)
        FROM orders
        GROUP BY customer_id;
        """,
        (
            "Mixed expression with grouped "
            "column accepted"
        ),
    )

    # ------------------------------------------------------
    # 14. Ordinary non-aggregate SELECT
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            customer_id,
            total_amount
        FROM orders;
        """,
        "Non-aggregate query unaffected",
    )

    print()
    print("=" * 70)
    print(
        "ALL AGGREGATE PROJECTION VALIDATION TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()