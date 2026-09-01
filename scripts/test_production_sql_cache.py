from app.core.dependencies import (
    get_query_service,
    get_sql_cache,
)


def main():
    print("=" * 70)
    print("PRODUCTION SQL CACHE TEST")
    print("=" * 70)

    cache = get_sql_cache()
    cache.clear()
    cache.reset_stats()

    service = get_query_service()

    question = (
        "Show all customers"
    )

    # ------------------------------------------------------
    # First request
    # ------------------------------------------------------

    print()
    print("FIRST REQUEST")
    print("-" * 70)

    response_1 = service.generate_sql(
        question
    )

    print(
        "SQL:",
        response_1.sql,
    )

    print(
        "Cache size after first request:",
        len(cache),
    )

    assert len(cache) == 1
    stats_1 = cache.stats()
    
    assert stats_1["hits"] == 0
    assert stats_1["misses"] == 1
    assert stats_1["stores"] == 1

    # ------------------------------------------------------
    # Second request
    # ------------------------------------------------------

    print()
    print("SECOND REQUEST")
    print("-" * 70)

    response_2 = service.generate_sql(
        question
    )

    print(
        "SQL:",
        response_2.sql,
    )

    print(
        "Cache size after second request:",
        len(cache),
    )
    
    print(
        "Cache stats after second request:",
        cache.stats(),
    )

    assert (
        response_1.sql
        == response_2.sql
    )

    assert len(cache) == 1
    
    stats_2 = cache.stats()
    
    assert stats_2["hits"] == 1
    assert stats_2["misses"] == 1
    assert stats_2["stores"] == 1
    assert stats_2["evictions"] == 0
    assert stats_2["current_size"] == 1
    assert stats_2["hit_rate"] == 0.5

    print()
    print("=" * 70)
    print(
        "PRODUCTION SQL CACHE TEST PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()