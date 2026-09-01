from app.core.dependencies import get_sql_cache


def main():
    print("=" * 70)
    print("SHARED SQL CACHE DEPENDENCY TEST")
    print("=" * 70)

    cache_1 = get_sql_cache()
    cache_2 = get_sql_cache()

    # ------------------------------------------------------
    # 1. Same object
    # ------------------------------------------------------

    assert cache_1 is cache_2

    print(
        "[PASS] Same SQLCache instance returned"
    )

    # ------------------------------------------------------
    # 2. Write through first reference
    # ------------------------------------------------------

    key = cache_1.build_key(
        question="Show all customers",
        schema_fingerprint="test-schema",
        provider="gemini",
        model="gemini-2.5-pro",
        cache_version="v1",
    )

    cache_1.set(
        key,
        "SELECT * FROM customers;",
    )

    # ------------------------------------------------------
    # 3. Read through second reference
    # ------------------------------------------------------

    cached_sql = cache_2.get(
        key
    )

    assert (
        cached_sql
        == "SELECT * FROM customers;"
    )

    print(
        "[PASS] Cache data shared between references"
    )

    # ------------------------------------------------------
    # 4. Size is shared
    # ------------------------------------------------------

    assert len(cache_1) == 1
    assert len(cache_2) == 1

    print(
        "[PASS] Shared cache size"
    )

    # ------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------

    cache_1.clear()

    assert len(cache_2) == 0

    print(
        "[PASS] Shared cache clear"
    )

    print()
    print("=" * 70)
    print(
        "ALL SHARED SQL CACHE TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()