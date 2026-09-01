from app.core.dependencies import (
    get_query_service,
    get_sql_cache,
)


def main():
    print("=" * 70)
    print("INVALID CACHED SQL EVICTION TEST")
    print("=" * 70)

    cache = get_sql_cache()
    cache.clear()
    cache.reset_stats()

    service = get_query_service()

    question = "Show all customers"

    # ------------------------------------------------------
    # Build the exact production cache key
    # ------------------------------------------------------

    schema = service._load_schema()

    documents = service._build_schema_documents(
        schema
    )

    service._initialize_schema_index(
        documents
    )

    schema_fingerprint = (
        service._get_schema_fingerprint()
    )

    cache_key = service._build_sql_cache_key(
        question=question,
        schema_fingerprint=schema_fingerprint,
    )

    assert cache_key is not None

    print(
        "[PASS] Production cache key created"
    )

    # ------------------------------------------------------
    # Insert intentionally invalid cached SQL
    # ------------------------------------------------------

    invalid_sql = (
        "SELECT imaginary_column "
        "FROM customers;"
    )

    cache.set(
        cache_key,
        invalid_sql,
    )

    assert len(cache) == 1

    print(
        "[PASS] Invalid SQL inserted into cache"
    )

    # ------------------------------------------------------
    # Ask QueryService to read the cached entry directly
    #
    # This must:
    # 1. hit the cache
    # 2. fail structural validation
    # 3. delete the invalid entry
    # 4. return None
    #
    # No LLM generation happens in this test.
    # ------------------------------------------------------

    cached_sql = service._get_cached_sql(
        cache_key=cache_key,
        full_schema=schema,
    )

    assert cached_sql is None

    print(
        "[PASS] Invalid cached SQL rejected"
    )

    # ------------------------------------------------------
    # Verify eviction
    # ------------------------------------------------------

    assert len(cache) == 0

    print(
        "[PASS] Invalid cached SQL removed"
    )

    # ------------------------------------------------------
    # Verify metrics
    # ------------------------------------------------------

    stats = cache.stats()

    print(
        "Cache stats:",
        stats,
    )

    assert stats["hits"] == 1
    assert stats["current_size"] == 0

    # Explicit invalid-entry deletion must not count
    # as LRU eviction.
    assert stats["evictions"] == 0

    print(
        "[PASS] Cache metrics remain correct"
    )

    print()
    print("=" * 70)
    print(
        "INVALID CACHED SQL EVICTION TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()