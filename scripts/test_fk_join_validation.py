from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.services.semantic_validator import (
    SemanticValidator,
)


def make_join_intent() -> IntentAnalysis:
    return IntentAnalysis(
        primary=QueryIntent.LOOKUP,
        secondary=[
            QueryIntent.JOIN,
        ],
        scores={},
        confidence=1.0,
    )


def build_schema() -> dict:
    return {
        "customers": {
            "columns": [
                {"name": "id"},
                {"name": "name"},
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
                    "name": "orders_customer_id_fkey",
                    "constrained_columns": [
                        "customer_id",
                    ],
                    "referred_schema": "public",
                    "referred_table": "customers",
                    "referred_columns": [
                        "id",
                    ],
                    "options": {},
                    "comment": None,
                }
            ],
        },

        "order_items": {
            "columns": [
                {"name": "id"},
                {"name": "order_id"},
                {"name": "product_id"},
            ],
            "foreign_keys": [
                {
                    "name": "order_items_order_id_fkey",
                    "constrained_columns": [
                        "order_id",
                    ],
                    "referred_schema": "public",
                    "referred_table": "orders",
                    "referred_columns": [
                        "id",
                    ],
                    "options": {},
                    "comment": None,
                },
                {
                    "name": "order_items_product_id_fkey",
                    "constrained_columns": [
                        "product_id",
                    ],
                    "referred_schema": "public",
                    "referred_table": "products",
                    "referred_columns": [
                        "id",
                    ],
                    "options": {},
                    "comment": None,
                },
            ],
        },

        "products": {
            "columns": [
                {"name": "id"},
                {"name": "name"},
                {"name": "price"},
            ],
            "foreign_keys": [],
        },
    }


def validate(sql: str):
    validator = SemanticValidator()

    return validator.validate(
        question="Show customers with their orders",
        sql=sql,
        intent=make_join_intent(),
        schema=build_schema(),
    )


def main():
    print("=" * 70)
    print("FOREIGN-KEY JOIN VALIDATION TEST")
    print("=" * 70)

    # ------------------------------------------------------
    # 1. Direct valid FK
    # ------------------------------------------------------

    result = validate(
        """
        SELECT
            customers.name,
            orders.total_amount
        FROM customers
        JOIN orders
            ON orders.customer_id = customers.id;
        """
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Direct FK join accepted"
    )

    # ------------------------------------------------------
    # 2. Reversed equality direction
    # ------------------------------------------------------

    result = validate(
        """
        SELECT
            customers.name,
            orders.total_amount
        FROM customers
        JOIN orders
            ON customers.id = orders.customer_id;
        """
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Reversed FK equality accepted"
    )

    # ------------------------------------------------------
    # 3. Aliased valid FK
    # ------------------------------------------------------

    result = validate(
        """
        SELECT
            c.name,
            o.total_amount
        FROM customers AS c
        JOIN orders AS o
            ON o.customer_id = c.id;
        """
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Aliased FK join accepted"
    )

    # ------------------------------------------------------
    # 4. Invalid relationship
    # ------------------------------------------------------

    result = validate(
        """
        SELECT
            customers.name,
            orders.total_amount
        FROM customers
        JOIN orders
            ON orders.id = customers.id;
        """
    )

    assert result.valid is False

    assert any(
        "foreign-key relationship"
        in error.lower()
        for error in result.errors
    )

    print(
        "[PASS] Invented join relationship rejected"
    )

    # ------------------------------------------------------
    # 5. Invalid aliased relationship
    # ------------------------------------------------------

    result = validate(
        """
        SELECT
            c.name,
            o.total_amount
        FROM customers AS c
        JOIN orders AS o
            ON o.id = c.id;
        """
    )

    assert result.valid is False

    print(
        "[PASS] Invalid aliased relationship rejected"
    )

    # ------------------------------------------------------
    # 6. order_items -> orders
    # ------------------------------------------------------

    result = validate(
        """
        SELECT
            oi.id,
            o.total_amount
        FROM order_items AS oi
        JOIN orders AS o
            ON oi.order_id = o.id;
        """
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] order_items -> orders FK accepted"
    )

    # ------------------------------------------------------
    # 7. order_items -> products
    # ------------------------------------------------------

    result = validate(
        """
        SELECT
            oi.id,
            p.name
        FROM order_items AS oi
        JOIN products AS p
            ON oi.product_id = p.id;
        """
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] order_items -> products FK accepted"
    )

    # ------------------------------------------------------
    # 8. Missing JOIN
    # ------------------------------------------------------

    result = validate(
        """
        SELECT name
        FROM customers;
        """
    )

    assert result.valid is False

    assert any(
        "requires a join"
        in error.lower()
        for error in result.errors
    )

    print(
        "[PASS] Missing required JOIN rejected"
    )

    print()
    print("=" * 70)
    print(
        "ALL FOREIGN-KEY JOIN VALIDATION TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()