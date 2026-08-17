
from app.services.semantic_validator import SemanticValidator
from app.services.intent_detector import IntentDetector


detector = IntentDetector()
validator = SemanticValidator()


schema = {
    "customers": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "email"},
            {"name": "city"},
            {"name": "created_at"},
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

    "products": {
        "columns": [
            {"name": "id"},
            {"name": "name"},
            {"name": "price"},
        ]
    },

    "order_items": {
        "columns": [
            {"name": "id"},
            {"name": "order_id"},
            {"name": "product_id"},
            {"name": "quantity"},
            {"name": "unit_price"},
        ]
    },
}


tests = [
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
            GROUP BY c.id, c.name;
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
            GROUP BY c.id, c.name
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
            GROUP BY c.id, c.name
            ORDER BY total_spending DESC;
        """,
    },
]


print("=" * 80)
print("SEMANTIC VALIDATOR TEST")
print("=" * 80)

passed = 0
failed = 0

for test in tests:

    question = test["question"]
    sql = test["sql"].strip()

    print("\n" + "=" * 80)
    print("QUESTION:", question)
    print("=" * 80)

    intent = detector.detect(question)

    print("PRIMARY INTENT:", intent.primary)
    print("SECONDARY INTENTS:", intent.secondary)
    print("CONFIDENCE:", intent.confidence)

    try:

        result = validator.validate(
            question=question,
            sql=sql,
            intent=intent,
            schema=schema,
        )

        print("\nVALID:", result.valid)
        print("ERRORS:", result.errors)

        if result.valid:
            passed += 1
        else:
            failed += 1

    except Exception as exc:

        failed += 1

        print("\nEXCEPTION:", type(exc).__name__)
        print("MESSAGE:", str(exc))


total = passed + failed

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("PASSED:", passed)
print("FAILED:", failed)

if total:
    efficiency = (passed / total) * 100
    print(f"EFFICIENCY: {efficiency:.2f}%")

print("=" * 80)

