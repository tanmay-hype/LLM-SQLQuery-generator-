# scripts/test_sql_cache_semantic_validation.py

from app.cache.sql_cache import SQLCache
from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.services.query_service import QueryService


SCHEMA = {
    "orders": {
        "columns": [
            {"name": "id"},
            {"name": "customer_id"},
            {"name": "total_amount"},
        ],
        "primary_keys": {
            "constrained_columns": ["id"],
        },
        "foreign_keys": [],
    },
}


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


def main():
    print("=" * 72)
    print("SQL CACHE SEMANTIC VALIDATION TEST")
    print("=" * 72)

    cache = SQLCache(
        max_size=10
    )

    service = QueryService(
        sql_cache=cache
    )

    # ======================================================
    # 1. Valid cached SQL
    # ======================================================

    key_valid = "valid-key"

    cache.set(
        key_valid,
        """
        SELECT
            customer_id,
            SUM(total_amount)
        FROM orders
        GROUP BY customer_id;
        """,
    )

    result = service._get_cached_sql(
        cache_key=key_valid,
        question="Show total spending per customer",
        intent=make_intent(
            QueryIntent.AGGREGATION,
            QueryIntent.GROUP_BY,
        ),
        full_schema=SCHEMA,
    )

    assert result is not None

    assert cache.get(
        key_valid
    ) is not None

    print(
        "[PASS] Valid cached SQL accepted"
    )

    # ======================================================
    # 2. Structurally invalid cached SQL
    # ======================================================

    key_structural = "structural-key"

    cache.set(
        key_structural,
        """
        SELECT imaginary_column
        FROM orders;
        """,
    )

    result = service._get_cached_sql(
        cache_key=key_structural,
        question="List orders",
        intent=make_intent(
            QueryIntent.LOOKUP
        ),
        full_schema=SCHEMA,
    )

    assert result is None

    assert cache.get(
        key_structural
    ) is None

    print(
        "[PASS] Structurally invalid cached SQL evicted"
    )

    # ======================================================
    # 3. Structurally valid but semantically invalid SQL
    # ======================================================

    key_semantic = "semantic-key"

    cache.set(
        key_semantic,
        """
        SELECT total_amount
        FROM orders;
        """,
    )

    result = service._get_cached_sql(
        cache_key=key_semantic,
        question="What is the total order amount?",
        intent=make_intent(
            QueryIntent.AGGREGATION
        ),
        full_schema=SCHEMA,
    )

    assert result is None

    assert cache.get(
        key_semantic
    ) is None

    print(
        "[PASS] Semantically invalid cached SQL evicted"
    )

    print()
    print("=" * 72)
    print(
        "ALL SQL CACHE SEMANTIC VALIDATION TESTS PASSED"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()