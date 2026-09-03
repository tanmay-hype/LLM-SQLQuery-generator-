from app.cache.semantic_cache_entry import SemanticSQLCacheEntry
from app.cache.semantic_sql_cache import SemanticSQLCache
from app.models.intent import QueryIntent


def make_entry(
    question: str,
    embedding: tuple[float, ...],
    sql: str = "SELECT * FROM customers;",
) -> SemanticSQLCacheEntry:
    return SemanticSQLCacheEntry(
        question=question,
        sql=sql,
        embedding=embedding,
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-test",
        cache_version="v1",
        primary_intent=QueryIntent.LOOKUP,
        secondary_intents=(),
    )


def test_exact_vector_match():
    cache = SemanticSQLCache(
        max_size=10,
        similarity_threshold=0.95,
    )

    entry = make_entry(
        "show all customers",
        (1.0, 0.0, 0.0),
    )

    cache.add(entry)

    result = cache.search((1.0, 0.0, 0.0))

    assert result is not None

    matched_entry, score = result

    assert matched_entry == entry
    assert abs(score - 1.0) < 1e-9


def test_similar_vector_match():
    cache = SemanticSQLCache(
        max_size=10,
        similarity_threshold=0.95,
    )

    entry = make_entry(
        "show all customers",
        (1.0, 0.0),
    )

    cache.add(entry)

    result = cache.search((0.99, 0.01))

    assert result is not None

    matched_entry, score = result

    assert matched_entry == entry
    assert score >= 0.95


def test_below_threshold_is_miss():
    cache = SemanticSQLCache(
        max_size=10,
        similarity_threshold=0.95,
    )

    cache.add(
        make_entry(
            "show all customers",
            (1.0, 0.0),
        )
    )

    result = cache.search((0.0, 1.0))

    assert result is None


def test_best_match_is_selected():
    cache = SemanticSQLCache(
        max_size=10,
        similarity_threshold=0.50,
    )

    customers = make_entry(
        "show customers",
        (1.0, 0.0),
    )

    products = make_entry(
        "show products",
        (0.0, 1.0),
        sql="SELECT * FROM products;",
    )

    cache.add(customers)
    cache.add(products)

    result = cache.search((0.1, 0.9))

    assert result is not None

    matched_entry, _ = result

    assert matched_entry == products


def test_dimension_mismatch_is_ignored():
    cache = SemanticSQLCache(
        max_size=10,
        similarity_threshold=0.50,
    )

    cache.add(
        make_entry(
            "show customers",
            (1.0, 0.0, 0.0),
        )
    )

    result = cache.search((1.0, 0.0))

    assert result is None


def test_eviction():
    cache = SemanticSQLCache(
        max_size=2,
        similarity_threshold=0.95,
    )

    first = make_entry(
        "first",
        (1.0, 0.0, 0.0),
    )

    second = make_entry(
        "second",
        (0.0, 1.0, 0.0),
    )

    third = make_entry(
        "third",
        (0.0, 0.0, 1.0),
    )

    cache.add(first)
    cache.add(second)
    cache.add(third)

    assert len(cache) == 2
    assert cache.delete(first) is False
    assert cache.stats()["evictions"] == 1


def test_delete():
    cache = SemanticSQLCache()

    entry = make_entry(
        "show customers",
        (1.0, 0.0),
    )

    cache.add(entry)

    assert cache.delete(entry) is True
    assert cache.delete(entry) is False
    assert len(cache) == 0


def test_clear_does_not_reset_metrics():
    cache = SemanticSQLCache()

    entry = make_entry(
        "show customers",
        (1.0, 0.0),
    )

    cache.add(entry)
    cache.search((1.0, 0.0))

    cache.clear()

    stats = cache.stats()

    assert stats["size"] == 0
    assert stats["stores"] == 1
    assert stats["hits"] == 1


def test_reset_stats():
    cache = SemanticSQLCache()

    entry = make_entry(
        "show customers",
        (1.0, 0.0),
    )

    cache.add(entry)
    cache.search((1.0, 0.0))
    cache.search((0.0, 1.0))

    cache.reset_stats()

    assert cache.stats() == {
        "size": 1,
        "hits": 0,
        "misses": 0,
        "stores": 0,
        "evictions": 0,
    }


def test_invalid_zero_vector_rejected():
    cache = SemanticSQLCache()

    try:
        cache.search((0.0, 0.0))
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected zero vector to raise ValueError"
        )


def run():
    tests = [
        test_exact_vector_match,
        test_similar_vector_match,
        test_below_threshold_is_miss,
        test_best_match_is_selected,
        test_dimension_mismatch_is_ignored,
        test_eviction,
        test_delete,
        test_clear_does_not_reset_metrics,
        test_reset_stats,
        test_invalid_zero_vector_rejected,
    ]

    passed = 0

    for test in tests:
        try:
            test()
            passed += 1
            print(f"[PASS] {test.__name__}")
        except Exception as exc:
            print(
                f"[FAIL] {test.__name__}: "
                f"{type(exc).__name__}: {exc}"
            )

    print()
    print(f"PASSED: {passed}")
    print(f"FAILED: {len(tests) - passed}")
    print(f"TOTAL: {len(tests)}")

    if passed != len(tests):
        raise SystemExit(1)


if __name__ == "__main__":
    run()