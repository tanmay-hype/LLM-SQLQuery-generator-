from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.services.semantic_validator import (
    SemanticValidator,
)


def make_intent(
    primary: QueryIntent,
    secondary: list[QueryIntent] | None = None,
) -> IntentAnalysis:

    return IntentAnalysis(
        primary=primary,
        secondary=secondary or [],
        scores={},
        confidence=1.0,
    )


def build_schema() -> dict:
    return {
        "customers": {
            "columns": [
                {"name": "id"},
                {"name": "name"},
                {"name": "city"},
            ]
        },
        "orders": {
            "columns": [
                {"name": "id"},
                {"name": "customer_id"},
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
    }


def main():
    print("=" * 70)
    print("SEMANTIC CONTRACT VALIDATION TEST")
    print("=" * 70)

    validator = SemanticValidator()

    schema = build_schema()

    # ------------------------------------------------------
    # 1. Missing aggregation
    # ------------------------------------------------------

    result = validator.validate(
        question="What is the total order amount?",
        sql="""
            SELECT total_amount
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION
        ),
        schema=schema,
    )

    assert result.valid is False

    assert any(
        "aggregate"
        in error.lower()
        for error in result.errors
    )

    print(
        "[PASS] Missing aggregation rejected"
    )

    # ------------------------------------------------------
    # 2. Valid aggregation
    # ------------------------------------------------------

    result = validator.validate(
        question="What is the total order amount?",
        sql="""
            SELECT SUM(total_amount)
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION
        ),
        schema=schema,
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Valid aggregation accepted"
    )

    # ------------------------------------------------------
    # 3. Secondary GROUP_BY is enforced
    # ------------------------------------------------------

    result = validator.validate(
        question="What is the total order amount per customer?",
        sql="""
            SELECT
                customer_id,
                SUM(total_amount)
            FROM orders;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            [
                QueryIntent.GROUP_BY,
            ],
        ),
        schema=schema,
    )

    assert result.valid is False

    assert any(
        "group by"
        in error.lower()
        for error in result.errors
    )

    print(
        "[PASS] Missing GROUP BY rejected"
    )

    # ------------------------------------------------------
    # 4. Valid GROUP BY
    # ------------------------------------------------------

    result = validator.validate(
        question="What is the total order amount per customer?",
        sql="""
            SELECT
                customer_id,
                SUM(total_amount)
            FROM orders
            GROUP BY customer_id;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            [
                QueryIntent.GROUP_BY,
            ],
        ),
        schema=schema,
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Valid GROUP BY accepted"
    )

    # ------------------------------------------------------
    # 5. Secondary SORT is enforced
    # ------------------------------------------------------

    result = validator.validate(
        question="Show customers sorted by name",
        sql="""
            SELECT name
            FROM customers;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            [
                QueryIntent.SORT,
            ],
        ),
        schema=schema,
    )

    assert result.valid is False

    assert any(
        "order by"
        in error.lower()
        for error in result.errors
    )

    print(
        "[PASS] Missing ORDER BY rejected"
    )

    # ------------------------------------------------------
    # 6. Valid ORDER BY
    # ------------------------------------------------------

    result = validator.validate(
        question="Show customers sorted by name",
        sql="""
            SELECT name
            FROM customers
            ORDER BY name;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            [
                QueryIntent.SORT,
            ],
        ),
        schema=schema,
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Valid ORDER BY accepted"
    )

    # ------------------------------------------------------
    # 7. Secondary JOIN is enforced
    # ------------------------------------------------------

    result = validator.validate(
        question="Show customers with their orders",
        sql="""
            SELECT name
            FROM customers;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            [
                QueryIntent.JOIN,
            ],
        ),
        schema=schema,
    )

    assert result.valid is False

    assert any(
        "join"
        in error.lower()
        for error in result.errors
    )

    print(
        "[PASS] Missing JOIN rejected"
    )

    # ------------------------------------------------------
    # 8. Valid JOIN
    # ------------------------------------------------------

    result = validator.validate(
        question="Show customers with their orders",
        sql="""
            SELECT
                customers.name,
                orders.total_amount
            FROM customers
            JOIN orders
                ON orders.customer_id = customers.id;
        """,
        intent=make_intent(
            QueryIntent.LOOKUP,
            [
                QueryIntent.JOIN,
            ],
        ),
        schema=schema,
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Valid JOIN accepted"
    )

    # ------------------------------------------------------
    # 9. Superlative using ORDER BY + LIMIT
    # ------------------------------------------------------

    result = validator.validate(
        question="What is the highest product price?",
        sql="""
            SELECT price
            FROM products
            ORDER BY price DESC
            LIMIT 1;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            [
                QueryIntent.SORT,
            ],
        ),
        schema=schema,
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Superlative ORDER BY + LIMIT accepted"
    )

    # ------------------------------------------------------
    # 10. Superlative using MAX()
    # ------------------------------------------------------

    result = validator.validate(
        question="What is the highest product price?",
        sql="""
            SELECT MAX(price)
            FROM products;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION
        ),
        schema=schema,
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Superlative MAX accepted"
    )
    
    
    # ------------------------------------------------------
    # Superlative wrong aggregate must be rejected
    # ------------------------------------------------------
    
    result = validator.validate(
        question="What is the highest product price?",
        sql="""
            SELECT MIN(price)
            FROM products;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            [
                QueryIntent.SORT,
            ],
        ),
        schema=schema,
    )
    
    assert result.valid is False
    
    print(
        "[PASS] Superlative wrong aggregate rejected"
    )
    
    # ------------------------------------------------------
    # Lowest using MIN()
    # ------------------------------------------------------
    
    result = validator.validate(
        question="What is the lowest product price?",
        sql="""
            SELECT MIN(price)
            FROM products;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            [
                QueryIntent.SORT,
            ],
        ),
        schema=schema,
    )
    
    assert result.valid is True, result.errors
    
    print(
        "[PASS] Lowest using MIN() accepted"
    )


    # ------------------------------------------------------
    # 11. Complete multi-intent query
    # ------------------------------------------------------

    result = validator.validate(
        question=(
            "Show total customer spending "
            "per customer ordered by spending"
        ),
        sql="""
            SELECT
                customers.name,
                SUM(orders.total_amount) AS spending
            FROM customers
            JOIN orders
                ON orders.customer_id = customers.id
            GROUP BY customers.name
            ORDER BY spending DESC;
        """,
        intent=make_intent(
            QueryIntent.AGGREGATION,
            [
                QueryIntent.GROUP_BY,
                QueryIntent.SORT,
                QueryIntent.JOIN,
            ],
        ),
        schema=schema,
    )

    assert result.valid is True, result.errors

    print(
        "[PASS] Multi-intent SQL accepted"
    )

    print()
    print("=" * 70)
    print(
        "ALL SEMANTIC CONTRACT VALIDATION TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()