from app.cache.semantic_sql_cache_value_guard import (
    SemanticSQLCacheValueGuard,
)


guard = SemanticSQLCacheValueGuard()


def assert_same(left: str, right: str):
    assert guard.is_compatible(left, right)


def assert_different(left: str, right: str):
    assert not guard.is_compatible(left, right)


def test_same_city_value():
    assert_same(
        "Show customers where city is Mumbai",
        "List customers where city is Mumbai",
    )


def test_different_city_value():
    assert_different(
        "Show customers where city is Mumbai",
        "Show customers where city is Delhi",
    )


def test_same_email_value():
    assert_same(
        "Find customer with email alice@example.com",
        "Show customer with email alice@example.com",
    )


def test_different_email_value():
    assert_different(
        "Find customer with email alice@example.com",
        "Find customer with email bob@example.com",
    )


def test_same_named_value():
    assert_same(
        "Find product named Laptop",
        "Show product named Laptop",
    )


def test_different_named_value():
    assert_different(
        "Find product named Laptop",
        "Find product named Keyboard",
    )


def test_different_multiword_named_value():
    assert_different(
        "Find product named Gaming Laptop",
        "Find product named Wireless Keyboard",
    )


def test_same_from_value():
    assert_same(
        "Show customers from Mumbai",
        "List customers from Mumbai",
    )


def test_different_from_value():
    assert_different(
        "Show customers from Mumbai",
        "Show customers from Delhi",
    )


def test_numeric_paraphrase():
    assert_same(
        "Show orders above 5000",
        "List orders greater than 5000",
    )


def test_plain_paraphrase_without_values():
    assert_same(
        "Show all customers",
        "Give me all customers",
    )


def run():
    tests = [
        test_same_city_value,
        test_different_city_value,
        test_same_email_value,
        test_different_email_value,
        test_same_named_value,
        test_different_named_value,
        test_different_multiword_named_value,
        test_same_from_value,
        test_different_from_value,
        test_numeric_paraphrase,
        test_plain_paraphrase_without_values,
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