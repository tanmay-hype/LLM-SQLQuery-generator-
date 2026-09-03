from app.cache.semantic_cache_entry import SemanticSQLCacheEntry
from app.cache.semantic_sql_cache_compatibility import (
    SemanticSQLCacheCompatibility,
)
from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis


def make_intent(
    primary=QueryIntent.LOOKUP,
    secondary=(),
):
    return IntentAnalysis(
        primary=primary,
        secondary=list(secondary),
        scores={},
        confidence=1.0,
    )


def make_entry(
    question: str,
    *,
    primary=QueryIntent.LOOKUP,
    secondary=(),
):
    return SemanticSQLCacheEntry(
        question=question,
        sql="SELECT 1;",
        embedding=(1.0, 0.0),
        schema_fingerprint="schema-v1",
        provider="gemini",
        model="gemini-test",
        cache_version="v1",
        primary_intent=primary,
        secondary_intents=tuple(secondary),
    )


compatibility = SemanticSQLCacheCompatibility()


def assert_compatible(
    cached_question,
    new_question,
    *,
    primary=QueryIntent.LOOKUP,
    secondary=(),
):
    entry = make_entry(
        cached_question,
        primary=primary,
        secondary=secondary,
    )

    intent = make_intent(
        primary=primary,
        secondary=secondary,
    )

    assert compatibility.is_compatible(
        new_question,
        intent,
        entry,
    )


def assert_incompatible(
    cached_question,
    new_question,
    *,
    cached_primary=QueryIntent.LOOKUP,
    current_primary=QueryIntent.LOOKUP,
    cached_secondary=(),
    current_secondary=(),
):
    entry = make_entry(
        cached_question,
        primary=cached_primary,
        secondary=cached_secondary,
    )

    intent = make_intent(
        primary=current_primary,
        secondary=current_secondary,
    )

    assert not compatibility.is_compatible(
        new_question,
        intent,
        entry,
    )


def test_simple_paraphrase_is_compatible():
    assert_compatible(
        "Show all customers",
        "Give me all customers",
    )


def test_same_limit_is_compatible():
    assert_compatible(
        "Show the top 5 products",
        "Give me the top 5 products",
        primary=QueryIntent.SORT,
    )


def test_different_limit_is_rejected():
    assert_incompatible(
        "Show the top 5 products",
        "Show the top 10 products",
        cached_primary=QueryIntent.SORT,
        current_primary=QueryIntent.SORT,
    )


def test_different_numeric_filter_is_rejected():
    assert_incompatible(
        "Show orders above 5000",
        "Show orders above 1000",
    )


def test_greater_vs_less_is_rejected():
    assert_incompatible(
        "Show orders greater than 5000",
        "Show orders less than 5000",
    )


def test_above_paraphrase_is_compatible():
    assert_compatible(
        "Show orders greater than 5000",
        "Show orders above 5000",
    )


def test_cheapest_vs_expensive_is_rejected():
    assert_incompatible(
        "Show the 5 cheapest products",
        "Show the 5 most expensive products",
        cached_primary=QueryIntent.SORT,
        current_primary=QueryIntent.SORT,
    )


def test_latest_vs_oldest_is_rejected():
    assert_incompatible(
        "Show the latest 5 orders",
        "Show the oldest 5 orders",
        cached_primary=QueryIntent.SORT,
        current_primary=QueryIntent.SORT,
    )


def test_same_latest_semantics_is_compatible():
    assert_compatible(
        "Show the latest 5 orders",
        "Show the most recent 5 orders",
        primary=QueryIntent.SORT,
    )


def test_negation_change_is_rejected():
    assert_incompatible(
        "Show customers from Delhi",
        "Show customers not from Delhi",
    )


def test_between_vs_non_between_is_rejected():
    assert_incompatible(
        "Show products between 500 and 2000",
        "Show products above 500 and under 2000",
    )


def test_between_paraphrase_with_same_numbers():
    assert_compatible(
        "Show products between 500 and 2000",
        "Find products between 500 and 2000",
    )


def test_primary_intent_change_is_rejected():
    assert_incompatible(
        "Show customers",
        "Count customers",
        cached_primary=QueryIntent.LOOKUP,
        current_primary=QueryIntent.AGGREGATION,
    )


def test_secondary_intent_change_is_rejected():
    assert_incompatible(
        "Show customers",
        "Show customers",
        cached_primary=QueryIntent.LOOKUP,
        current_primary=QueryIntent.LOOKUP,
        cached_secondary=(),
        current_secondary=(QueryIntent.SORT,),
    )


def test_same_quoted_literal_is_compatible():
    assert_compatible(
        'Show customers from "Mumbai"',
        'List customers from "Mumbai"',
    )


def test_different_quoted_literal_is_rejected():
    assert_incompatible(
        'Show customers from "Mumbai"',
        'Show customers from "Delhi"',
    )


def run():
    tests = [
        test_simple_paraphrase_is_compatible,
        test_same_limit_is_compatible,
        test_different_limit_is_rejected,
        test_different_numeric_filter_is_rejected,
        test_greater_vs_less_is_rejected,
        test_above_paraphrase_is_compatible,
        test_cheapest_vs_expensive_is_rejected,
        test_latest_vs_oldest_is_rejected,
        test_same_latest_semantics_is_compatible,
        test_negation_change_is_rejected,
        test_between_vs_non_between_is_rejected,
        test_between_paraphrase_with_same_numbers,
        test_primary_intent_change_is_rejected,
        test_secondary_intent_change_is_rejected,
        test_same_quoted_literal_is_compatible,
        test_different_quoted_literal_is_rejected,
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