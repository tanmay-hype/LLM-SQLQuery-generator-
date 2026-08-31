from app.cache.sql_cache import SQLCache


def main():
    print("=" * 70)
    print("SQL CACHE TEST")
    print("=" * 70)

    cache = SQLCache(
        max_size=2
    )

    # ------------------------------------------------------
    # 1. Deterministic key
    # ------------------------------------------------------

    key_1 = cache.build_key(
        question="Show all customers",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
    )

    key_2 = cache.build_key(
        question="  SHOW   ALL customers  ",
        schema_fingerprint="schema-v1",
        provider="Gemini",
        model="GEMINI-2.5-PRO",
    )

    assert key_1 == key_2

    print(
        "[PASS] Question normalization"
    )

    # ------------------------------------------------------
    # 2. Cache miss
    # ------------------------------------------------------

    assert cache.get(
        key_1
    ) is None

    print(
        "[PASS] Cache miss"
    )

    # ------------------------------------------------------
    # 3. Cache set/get
    # ------------------------------------------------------

    sql = (
        "SELECT * FROM customers;"
    )

    cache.set(
        key_1,
        sql,
    )

    assert cache.get(
        key_1
    ) == sql

    assert len(cache) == 1

    print(
        "[PASS] Cache set/get"
    )

    # ------------------------------------------------------
    # 4. Different schema -> different key
    # ------------------------------------------------------

    changed_schema_key = (
        cache.build_key(
            question="Show all customers",
            schema_fingerprint="schema-v2",
            provider="gemini",
            model="gemini-2.5-pro",
        )
    )

    assert (
        changed_schema_key
        != key_1
    )

    assert cache.get(
        changed_schema_key
    ) is None

    print(
        "[PASS] Schema-aware key"
    )

    # ------------------------------------------------------
    # 5. Different model -> different key
    # ------------------------------------------------------

    different_model_key = (
        cache.build_key(
            question="Show all customers",
            schema_fingerprint="schema-v1",
            provider="gemini",
            model="another-model",
        )
    )

    assert (
        different_model_key
        != key_1
    )

    print(
        "[PASS] Model-aware key"
    )

    # ------------------------------------------------------
    # 6. LRU eviction
    # ------------------------------------------------------

    key_b = cache.build_key(
        question="Show all products",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
    )

    cache.set(
        key_b,
        "SELECT * FROM products;",
    )

    # Access key_1 so it becomes the most recently used.
    assert cache.get(
        key_1
    ) is not None

    key_c = cache.build_key(
        question="Show all orders",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
    )

    cache.set(
        key_c,
        "SELECT * FROM orders;",
    )

    assert len(cache) == 2

    # key_b should have been evicted.
    assert cache.get(
        key_b
    ) is None

    # key_1 was recently used and should remain.
    assert cache.get(
        key_1
    ) is not None

    assert cache.get(
        key_c
    ) is not None

    print(
        "[PASS] LRU eviction"
    )

    # ------------------------------------------------------
    # 7. Clear
    # ------------------------------------------------------

    cache.clear()

    assert len(cache) == 0

    assert cache.get(
        key_1
    ) is None

    print(
        "[PASS] Cache clear"
    )

    print()
    print("=" * 70)
    print(
        "ALL SQL CACHE TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()