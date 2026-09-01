from app.cache.sql_cache import SQLCache


def main():
    print("=" * 70)
    print("SQL CACHE TEST")
    print("=" * 70)

    cache = SQLCache(
        max_size=2
    )

    # ------------------------------------------------------
    # 1. Deterministic key / question normalization
    # ------------------------------------------------------

    key_1 = cache.build_key(
        question="Show all customers",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
        cache_version="v1",
    )

    key_2 = cache.build_key(
        question="  SHOW   ALL customers  ",
        schema_fingerprint="schema-v1",
        provider="Gemini",
        model="GEMINI-2.5-PRO",
        cache_version="v1",
    )

    assert key_1 == key_2

    print(
        "[PASS] Question normalization"
    )

    # ------------------------------------------------------
    # 2. Cache version -> different key
    # ------------------------------------------------------

    version_v2_key = cache.build_key(
        question="Show all customers",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
        cache_version="v2",
    )

    assert (
        version_v2_key
        != key_1
    )

    print(
        "[PASS] Cache version changes key"
    )

    # ------------------------------------------------------
    # 3. Cache miss
    # ------------------------------------------------------

    assert cache.get(
        key_1
    ) is None

    print(
        "[PASS] Cache miss"
    )

    # ------------------------------------------------------
    # 4. Cache set/get
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
    # 5. Different schema -> different key
    # ------------------------------------------------------

    changed_schema_key = cache.build_key(
        question="Show all customers",
        schema_fingerprint="schema-v2",
        provider="gemini",
        model="gemini-2.5-pro",
        cache_version="v1",
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
    # 6. Different model -> different key
    # ------------------------------------------------------

    different_model_key = cache.build_key(
        question="Show all customers",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="another-model",
        cache_version="v1",
    )

    assert (
        different_model_key
        != key_1
    )

    print(
        "[PASS] Model-aware key"
    )

    # ------------------------------------------------------
    # 7. Different provider -> different key
    # ------------------------------------------------------

    different_provider_key = cache.build_key(
        question="Show all customers",
        schema_fingerprint="schema-v1",
        provider="openai",
        model="gemini-2.5-pro",
        cache_version="v1",
    )

    assert (
        different_provider_key
        != key_1
    )

    print(
        "[PASS] Provider-aware key"
    )

    # ------------------------------------------------------
    # 8. LRU eviction
    # ------------------------------------------------------

    key_b = cache.build_key(
        question="Show all products",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
        cache_version="v1",
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
        cache_version="v1",
    )

    cache.set(
        key_c,
        "SELECT * FROM orders;",
    )

    assert len(cache) == 2

    # key_b should have been evicted because key_1
    # was accessed more recently.
    assert cache.get(
        key_b
    ) is None

    # key_1 should still exist.
    assert cache.get(
        key_1
    ) is not None

    # key_c should also exist.
    assert cache.get(
        key_c
    ) is not None

    print(
        "[PASS] LRU eviction"
    )
    
    # ------------------------------------------------------
    # 9. Delete
    # ------------------------------------------------------
     
    delete_key = cache.build_key(
        question="Delete test",
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-2.5-pro",
        cache_version="v1",
    )

    cache.set(
        delete_key,
        "SELECT 1;",
    )

    assert cache.get(
        delete_key
    ) == "SELECT 1;"

    deleted = cache.delete(
        delete_key
    )

    assert deleted is True

    assert cache.get(
        delete_key 
    ) is None

    # Deleting an already missing key should be safe.
    
    deleted_again = cache.delete(
        delete_key
    )

    assert deleted_again is False

    print(
       "[PASS] Cache delete"
    ) 
    
    # ------------------------------------------------------
    # 10. Clear
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