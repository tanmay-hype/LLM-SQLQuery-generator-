import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from app.models.intent import QueryIntent
from app.services.semantic_validator import SemanticValidator


validator = SemanticValidator()

schema = {
    "customers": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "email"},
            {"name": "city"},
            {"name": "created_at"},
        ],
    },
    "orders": {
        "columns": [
            {"name": "id"},
            {"name": "customer_id"},
            {"name": "order_date"},
            {"name": "total_amount"},
        ],
    },
    "products": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "price"},
        ],
    },
    "order_items": {
        "columns": [
            {"name": "id"},
            {"name": "order_id"},
            {"name": "product_id"},
            {"name": "quantity"},
            {"name": "unit_price"},
        ],
    },
}


TEST_CASES = [
    {
        "question": "Compare customer spending",
        "intent": QueryIntent.COMPARISON,
        "sql": """
            SELECT
                c.name,
                SUM(oi.quantity) AS total_spending
            FROM customers AS c
            JOIN orders AS o
                ON c.id = o.customer_id
            JOIN order_items AS oi
                ON o.id = oi.order_id
            GROUP BY c.id, c.name;
        """,
        "should_be_valid": False,
        "description": "Spending incorrectly calculated using quantity",
    },
    {
        "question": "Show total order amount per customer",
        "intent": QueryIntent.AGGREGATION,
        "sql": """
            SELECT
                c.name,
                COUNT(o.id) AS total_order_amount
            FROM customers AS c
            JOIN orders AS o
                ON c.id = o.customer_id
            GROUP BY c.id, c.name;
        """,
        "should_be_valid": False,
        "description": "Order amount incorrectly calculated using COUNT",
    },
    {
        "question": "Show monthly order trends",
        "intent": QueryIntent.TIME_SERIES,
        "sql": """
            SELECT
                DATE_TRUNC('month', order_date) AS month,
                COUNT(id) AS order_count
            FROM orders;
        """,
        "should_be_valid": False,
        "description": "Monthly trend missing GROUP BY",
    },
    {
        "question": "Show the most recent orders",
        "intent": QueryIntent.SORT,
        "sql": """
            SELECT *
            FROM orders;
        """,
        "should_be_valid": False,
        "description": "Recent orders missing ORDER BY",
    },
    {
        "question": "Show top customers",
        "intent": QueryIntent.SORT,
        "sql": """
            SELECT
                c.name
            FROM customers AS c;
        """,
        "should_be_valid": False,
        "description": "Top customers missing ORDER BY",
    },
    {
        "question": "Show all customers",
        "intent": QueryIntent.LOOKUP,
        "sql": """
            SELECT
                c.name
            FROM customers AS c
            ORDER BY c.name DESC;
        """,
        "should_be_valid": True,
        "description": "Ordering is allowed even though not required",
    },
]


def main():

    passed = 0
    failed = 0

    print("=" * 80)
    print("SEMANTIC VALIDATOR NEGATIVE TEST")
    print("=" * 80)

    for test in TEST_CASES:

        print("\n" + "=" * 80)
        print("QUESTION:", test["question"])
        print("DESCRIPTION:", test["description"])
        print("=" * 80)

        result = validator.validate(
            question=test["question"],
            sql=test["sql"],
            intent=type(
                "IntentAnalysis",
                (),
                {
                    "primary": test["intent"],
                    "secondary": [],
                    "confidence": 1.0,
                },
            )(),
            schema=schema,
        )

        expected = test["should_be_valid"]

        if result.valid == expected:

            print("PASS")
            passed += 1

        else:

            print("FAIL")
            failed += 1

        print("EXPECTED VALID:", expected)
        print("ACTUAL VALID:", result.valid)
        print("ERRORS:", result.errors)

    total = passed + failed

    efficiency = (
        passed / total * 100
        if total
        else 0
    )

    print("\n" + "=" * 80)
    print("NEGATIVE TEST SUMMARY")
    print("=" * 80)
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"EFFICIENCY: {efficiency:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()