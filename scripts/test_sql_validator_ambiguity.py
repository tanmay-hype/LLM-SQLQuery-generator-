from app.exceptions import SQLValidationError
from app.services.validator import SQLValidator


SCHEMA = {
    "customers": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "email"},
        ],
        "foreign_keys": [],
    },

    "orders": {
        "columns": [
            {"name": "id"},
            {"name": "customer_id"},
            {"name": "total_amount"},
        ],
        "foreign_keys": [
            {
                "constrained_columns": [
                    "customer_id",
                ],
                "referred_table": "customers",
                "referred_columns": [
                    "id",
                ],
            }
        ],
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
    expected_message: str,
    label: str,
) -> None:

    try:

        SQLValidator.validate(
            sql=sql,
            schema=SCHEMA,
        )

    except SQLValidationError as exc:

        message = str(exc)

        assert (
            expected_message.lower()
            in message.lower()
        ), message

        print(
            f"[PASS] {label}"
        )

        return

    raise AssertionError(
        f"Expected SQLValidationError: {label}"
    )


def main():
    print("=" * 70)
    print("SQL VALIDATOR AMBIGUITY TEST")
    print("=" * 70)

    # ------------------------------------------------------
    # 1. Single-table unqualified column
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT id, name
        FROM customers;
        """,
        "Single-table unqualified columns accepted",
    )

    # ------------------------------------------------------
    # 2. Qualified duplicate column
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            customers.id,
            orders.id
        FROM customers
        JOIN orders
            ON orders.customer_id = customers.id;
        """,
        "Qualified duplicate columns accepted",
    )

    # ------------------------------------------------------
    # 3. Qualified aliases
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT
            c.id,
            o.id
        FROM customers AS c
        JOIN orders AS o
            ON o.customer_id = c.id;
        """,
        "Qualified aliased columns accepted",
    )

    # ------------------------------------------------------
    # 4. Ambiguous unqualified id
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT id
        FROM customers
        JOIN orders
            ON orders.customer_id = customers.id;
        """,
        expected_message=(
            "Ambiguous unqualified column"
        ),
        label=(
            "Ambiguous unqualified column rejected"
        ),
    )

    # ------------------------------------------------------
    # 5. Unique unqualified column in multi-table query
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT total_amount
        FROM customers
        JOIN orders
            ON orders.customer_id = customers.id;
        """,
        (
            "Unique unqualified multi-table "
            "column accepted"
        ),
    )

    # ------------------------------------------------------
    # 6. Unknown unqualified column
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT phone_number
        FROM customers;
        """,
        expected_message=(
            "Unknown column referenced"
        ),
        label=(
            "Unknown unqualified column rejected"
        ),
    )

    # ------------------------------------------------------
    # 7. Unknown qualified column
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT customers.phone_number
        FROM customers;
        """,
        expected_message=(
            "Unknown column referenced"
        ),
        label=(
            "Unknown qualified column rejected"
        ),
    )

    # ------------------------------------------------------
    # 8. Unknown table
    # ------------------------------------------------------

    assert_invalid(
        """
        SELECT id
        FROM customer_profiles;
        """,
        expected_message=(
            "Unknown table"
        ),
        label=(
            "Unknown table rejected"
        ),
    )

    # ------------------------------------------------------
    # 9. Wildcard
    # ------------------------------------------------------

    assert_valid(
        """
        SELECT *
        FROM customers;
        """,
        "Wildcard accepted",
    )

    print()
    print("=" * 70)
    print(
        "ALL SQL VALIDATOR AMBIGUITY TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()