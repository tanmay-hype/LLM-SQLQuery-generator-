from app.exceptions import SQLValidationError
from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.services.semantic_validator import SemanticValidator
from app.services.validator import SQLValidator


SCHEMA = {
    "customers": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "email"},
            {"name": "city"},
        ],
        "primary_keys": {
            "constrained_columns": ["id"],
        },
        "foreign_keys": [],
    },

    "orders": {
        "columns": [
            {"name": "id"},
            {"name": "customer_id"},
            {"name": "order_date"},
            {"name": "total_amount"},
        ],
        "primary_keys": {
            "constrained_columns": ["id"],
        },
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

    "products": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "category"},
            {"name": "price"},
        ],
        "primary_keys": {
            "constrained_columns": ["id"],
        },
        "foreign_keys": [],
    },

    "order_items": {
        "columns": [
            {"name": "id"},
            {"name": "order_id"},
            {"name": "product_id"},
            {"name": "quantity"},
            {"name": "unit_price"},
        ],
        "primary_keys": {
            "constrained_columns": ["id"],
        },
        "foreign_keys": [
            {
                "constrained_columns": [
                    "order_id",
                ],
                "referred_table": "orders",
                "referred_columns": [
                    "id",
                ],
            },
            {
                "constrained_columns": [
                    "product_id",
                ],
                "referred_table": "products",
                "referred_columns": [
                    "id",
                ],
            },
        ],
    },
}


sql_validator = SQLValidator()
semantic_validator = SemanticValidator()


def make_intent(
    primary: QueryIntent,
    *secondary: QueryIntent,
) -> IntentAnalysis:
    return IntentAnalysis(
        primary=primary,
        secondary=list(secondary),
        scores={},
        confidence=1.0,
    )


def validate_pipeline(
    question: str,
    sql: str,
    intent: IntentAnalysis,
):
    """
    Reproduce the production validation boundary:

        SQLValidator
            ->
        SemanticValidator
    """

    validated_sql = sql_validator.validate(
        sql,
        SCHEMA,
    )

    semantic_result = semantic_validator.validate(
        question=question,
        sql=validated_sql,
        intent=intent,
        schema=SCHEMA,
    )

    return validated_sql, semantic_result


def assert_valid(
    question: str,
    sql: str,
    intent: IntentAnalysis,
    label: str,
):
    validated_sql, semantic_result = (
        validate_pipeline(
            question,
            sql,
            intent,
        )
    )

    assert validated_sql

    assert semantic_result.valid, (
        semantic_result.errors
    )

    print(
        f"[PASS] {label}"
    )


def assert_structural_invalid(
    question: str,
    sql: str,
    intent: IntentAnalysis,
    label: str,
):
    try:

        validate_pipeline(
            question,
            sql,
            intent,
        )

    except SQLValidationError:

        print(
            f"[PASS] {label}"
        )

        return

    raise AssertionError(
        "Expected structural validation failure: "
        f"{label}"
    )


def assert_semantic_invalid(
    question: str,
    sql: str,
    intent: IntentAnalysis,
    label: str,
):
    try:

        _, semantic_result = (
            validate_pipeline(
                question,
                sql,
                intent,
            )
        )

    except SQLValidationError as exc:

        raise AssertionError(
            "Expected semantic failure, "
            "but structural validation failed: "
            f"{exc}"
        ) from exc

    assert not semantic_result.valid, (
        "Expected semantic validation failure: "
        f"{label}"
    )

    print(
        f"[PASS] {label}"
    )


def main():
    print("=" * 72)
    print("STRUCTURAL + SEMANTIC VALIDATOR INTEGRATION TEST")
    print("=" * 72)

    # ======================================================
    # 1. Simple lookup
    # ======================================================

    assert_valid(
        question="List customer names",
        sql="""
            SELECT name
            FROM customers;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP
        ),
        label=(
            "Simple lookup accepted"
        ),
    )

    # ======================================================
    # 2. Unknown table -> structural rejection
    # ======================================================

    assert_structural_invalid(
        question="List customer profiles",
        sql="""
            SELECT id
            FROM customer_profiles;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP
        ),
        label=(
            "Unknown table rejected structurally"
        ),
    )

    # ======================================================
    # 3. Unknown qualified column
    # ======================================================

    assert_structural_invalid(
        question="Show customer phone numbers",
        sql="""
            SELECT customers.phone_number
            FROM customers;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP
        ),
        label=(
            "Unknown column rejected structurally"
        ),
    )

    # ======================================================
    # 4. Ambiguous unqualified column
    # ======================================================

    assert_structural_invalid(
        question="Show customer and order IDs",
        sql="""
            SELECT id
            FROM customers
            JOIN orders
                ON orders.customer_id = customers.id;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            QueryIntent.JOIN,
        ),
        label=(
            "Ambiguous column rejected structurally"
        ),
    )

    # ======================================================
    # 5. Invalid aggregate projection
    # ======================================================

    assert_structural_invalid(
        question="Show total spending per customer",
        sql="""
            SELECT
                customer_id,
                SUM(total_amount)
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        ),
        label=(
            "Invalid aggregate projection rejected "
            "structurally"
        ),
    )

    # ======================================================
    # 6. Missing requested aggregation
    # ======================================================

    assert_semantic_invalid(
        question="What is the total order amount?",
        sql="""
            SELECT total_amount
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION
        ),
        label=(
            "Missing aggregation rejected semantically"
        ),
    )

    # ======================================================
    # 7. Missing requested GROUP BY
    # ======================================================

    assert_semantic_invalid(
        question="Show total spending per customer",
        sql="""
            SELECT SUM(total_amount)
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        ),
        label=(
            "Missing GROUP BY rejected semantically"
        ),
    )

    # ======================================================
    # 8. Missing requested ORDER BY
    # ======================================================

    assert_semantic_invalid(
        question="Show the top orders",
        sql="""
            SELECT
                id,
                total_amount
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            QueryIntent.SORT,
        ),
        label=(
            "Missing ORDER BY rejected semantically"
        ),
    )

    # ======================================================
    # 9. Missing requested JOIN
    # ======================================================

    assert_semantic_invalid(
        question="Show customers with their orders",
        sql="""
            SELECT
                customer_id,
                total_amount
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            QueryIntent.JOIN,
        ),
        label=(
            "Missing JOIN rejected semantically"
        ),
    )

    # ======================================================
    # 10. Invented JOIN relationship
    # ======================================================

    assert_semantic_invalid(
        question="Show customers with their orders",
        sql="""
            SELECT
                c.name,
                o.total_amount
            FROM customers AS c
            JOIN orders AS o
                ON o.id = c.id;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            QueryIntent.JOIN,
        ),
        label=(
            "Invented FK relationship rejected "
            "semantically"
        ),
    )

    # ======================================================
    # 11. Valid FK JOIN
    # ======================================================

    assert_valid(
        question="Show customers with their orders",
        sql="""
            SELECT
                c.name,
                o.total_amount
            FROM customers AS c
            JOIN orders AS o
                ON o.customer_id = c.id;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            QueryIntent.JOIN,
        ),
        label=(
            "Valid FK JOIN accepted"
        ),
    )

    # ======================================================
    # 12. Valid grouped aggregation
    # ======================================================

    assert_valid(
        question="Show total spending per customer",
        sql="""
            SELECT
                customer_id,
                SUM(total_amount) AS total_spending
            FROM orders
            GROUP BY customer_id;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        ),
        label=(
            "Valid grouped aggregation accepted"
        ),
    )

    # ======================================================
    # 13. Valid sort
    # ======================================================

    assert_valid(
        question="Show the top orders",
        sql="""
            SELECT
                id,
                total_amount
            FROM orders
            ORDER BY total_amount DESC;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            QueryIntent.SORT,
        ),
        label=(
            "Valid ORDER BY accepted"
        ),
    )

    # ======================================================
    # 14. Valid multi-intent query
    # ======================================================

    assert_valid(
        question=(
            "Show customers ranked by their "
            "total spending"
        ),
        sql="""
            SELECT
                c.id,
                c.name,
                SUM(o.total_amount) AS total_spending
            FROM customers AS c
            JOIN orders AS o
                ON o.customer_id = c.id
            GROUP BY
                c.id,
                c.name
            ORDER BY total_spending DESC;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
            QueryIntent.JOIN,
            QueryIntent.SORT,
        ),
        label=(
            "Valid multi-intent query accepted"
        ),
    )

    print()
    print("=" * 72)
    print(
        "ALL VALIDATOR INTEGRATION TESTS PASSED"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()

