from app.cache.sql_cache import SQLCache


def main():

    print("=" * 70)
    print("SQL CACHE METRICS TEST")
    print("=" * 70)

    cache = SQLCache(
        max_size=2
    )

    key_1 = cache.build_key(
        question="Show all customers",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
    )

    key_2 = cache.build_key(
        question="Show all products",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
    )

    key_3 = cache.build_key(
        question="Show all orders",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
    )

    # ------------------------------------------------------
    # Initial state
    # ------------------------------------------------------

    stats = cache.stats()

    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["stores"] == 0
    assert stats["evictions"] == 0
    assert stats["current_size"] == 0

    print("[PASS] Initial metrics")

    # ------------------------------------------------------
    # Miss
    # ------------------------------------------------------

    assert cache.get(
        key_1
    ) is None

    stats = cache.stats()

    assert stats["misses"] == 1

    print("[PASS] Miss counter")

    # ------------------------------------------------------
    # Store
    # ------------------------------------------------------

    cache.set(
        key_1,
        "SELECT * FROM customers;",
    )

    cache.set(
        key_2,
        "SELECT * FROM products;",
    )

    stats = cache.stats()

    assert stats["stores"] == 2
    assert stats["current_size"] == 2

    print("[PASS] Store counter")

    # ------------------------------------------------------
    # Hit
    # ------------------------------------------------------

    assert cache.get(
        key_1
    ) is not None

    stats = cache.stats()

    assert stats["hits"] == 1

    print("[PASS] Hit counter")

    # ------------------------------------------------------
    # Eviction
    # ------------------------------------------------------

    cache.set(
        key_3,
        "SELECT * FROM orders;",
    )

    stats = cache.stats()

    assert stats["evictions"] == 1
    assert stats["current_size"] == 2

    print("[PASS] Eviction counter")

    # ------------------------------------------------------
    # Hit rate
    # ------------------------------------------------------

    stats = cache.stats()

    expected_hit_rate = (
        stats["hits"]
        / (
            stats["hits"]
            + stats["misses"]
        )
    )

    assert stats["hit_rate"] == expected_hit_rate

    print("[PASS] Hit rate")

    # ------------------------------------------------------
    # Reset stats
    # ------------------------------------------------------

    cache.reset_stats()

    stats = cache.stats()

    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["stores"] == 0
    assert stats["evictions"] == 0

    # Cache contents must remain.
    assert stats["current_size"] == 2

    print("[PASS] Stats reset without clearing cache")

    print()
    print("Final stats:")
    print(stats)

    print()
    print("=" * 70)
    print("ALL SQL CACHE METRICS TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()