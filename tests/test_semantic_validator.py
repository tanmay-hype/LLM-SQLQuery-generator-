from app.models.intent import QueryIntent
from app.services.intent_detector import IntentDetector
from app.services.semantic_validator import SemanticValidator


detector = IntentDetector()
validator = SemanticValidator()


schema = {
    "customers": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
        ]
    },
    "orders": {
        "columns": [
            {"name": "id"},
            {"name": "customer_id"},
            {"name": "order_date"},
            {"name": "total_amount"},
        ]
    },
    "order_items": {
        "columns": [
            {"name": "id"},
            {"name": "order_id"},
            {"name": "product_id"},
            {"name": "quantity"},
        ]
    },
    "products": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "price"},
        ]
    },
}


TEST_CASES = [
    {
        "question": "Show all customers",
        "sql": """
            SELECT name
            FROM customers;
        """,
    },
    {
        "question": "Which customers have placed orders?",
        "sql": """
            SELECT DISTINCT
                c.name
            FROM customers AS c
            JOIN orders AS o
                ON c.id = o.customer_id;
        """,
    },
    {
        "question": "Show total order amount per customer",
        "sql": """
            SELECT
                c.name,
                SUM(o.total_amount) AS total_order_amount
            FROM customers AS c
            JOIN orders AS o
                ON c.id = o.customer_id
            GROUP BY
                c.id,
                c.name;
        """,
    },
    {
        "question": "Show monthly order trends",
        "sql": """
            SELECT
                DATE_TRUNC('month', order_date) AS month,
                COUNT(id) AS order_count
            FROM orders
            GROUP BY month
            ORDER BY month;
        """,
    },
    {
        "question": "Show the most recent orders",
        "sql": """
            SELECT *
            FROM orders
            ORDER BY order_date DESC;
        """,
    },
    {
        "question": "Show top customers",
        "sql": """
            SELECT
                c.name,
                SUM(o.total_amount) AS total_spent
            FROM customers AS c
            JOIN orders AS o
                ON c.id = o.customer_id
            GROUP BY
                c.id,
                c.name
            ORDER BY total_spent DESC;
        """,
    },
    {
        "question": "Compare customer spending",
        "sql": """
            SELECT
                c.name,
                SUM(o.total_amount) AS total_spending
            FROM customers AS c
            JOIN orders AS o
                ON c.id = o.customer_id
            GROUP BY
                c.id,
                c.name
            ORDER BY total_spending DESC;
        """,
    },
]


print("=" * 80)
print("SEMANTIC VALIDATOR POSITIVE TEST")
print("=" * 80)


passed = 0
failed = 0


for test in TEST_CASES:

    question = test["question"]
    sql = test["sql"]

    print("=" * 80)
    print(f"QUESTION: {question}")
    print("=" * 80)

    try:
        intent = detector.detect(question)

        print(f"PRIMARY INTENT: {intent.primary}")
        print(f"SECONDARY INTENTS: {intent.secondary}")
        print(f"CONFIDENCE: {intent.confidence}")

        result = validator.validate(
            question=question,
            sql=sql,
            intent=intent,
            schema=schema,
        )

        print()
        print(f"VALID: {result.valid}")
        print(f"ERRORS: {result.errors}")

        if result.valid:
            passed += 1
        else:
            failed += 1

    except Exception as exc:
        failed += 1

        print()
        print("EXCEPTION:", type(exc).__name__)
        print("MESSAGE:", str(exc))


total = passed + failed
efficiency = (
    (passed / total) * 100
    if total
    else 0
)


print()
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"PASSED: {passed}")
print(f"FAILED: {failed}")
print(f"EFFICIENCY: {efficiency:.2f}%")
print("=" * 80)