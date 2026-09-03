from app.cache.semantic_sql_cache import SemanticSQLCache
from app.cache.semantic_sql_cache_service import (
    SemanticSQLCacheService,
)
from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis


class FakeEmbeddingService:
    def __init__(self):
        self.calls = 0

        self.embeddings = {
            "show all customers": (1.0, 0.0, 0.0),
            "give me all customers": (0.99, 0.01, 0.0),
            "show all products": (0.0, 1.0, 0.0),

            "show the top 5 products": (0.0, 0.0, 1.0),
            "give me the top 5 products": (0.0, 0.01, 0.99),
            "show the top 10 products": (0.0, 0.01, 0.99),
        }

    def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.calls += 1

        results = []

        for text in texts:
            try:
                 embedding = self.embeddings[
                    text.lower()
                ]
            except KeyError as exc:
                raise ValueError(
                    f"No fake embedding for: {text}"
                ) from exc

            results.append(
                list(embedding)
            ) 

        return results


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


def make_service(
    threshold=0.95,
):
    embedding_service = FakeEmbeddingService()

    cache = SemanticSQLCache(
        max_size=20,
        similarity_threshold=threshold,
    )

    service = SemanticSQLCacheService(
        cache=cache,
        embedding_service=embedding_service,
    )

    return service, cache, embedding_service


def context():
    return {
        "schema_fingerprint": "schema-v1",
        "provider": "gemini",
        "model": "gemini-test",
        "cache_version": "v1",
    }


def test_store_adds_entry():
    service, cache, embeddings = make_service()

    entry = service.store(
        question="Show all customers",
        sql="SELECT * FROM customers;",
        intent=make_intent(),
        **context(),
    )

    assert len(cache) == 1
    assert entry.question == "Show all customers"
    assert entry.sql == "SELECT * FROM customers;"
    assert embeddings.calls == 1


def test_safe_paraphrase_hits():
    service, _, embeddings = make_service()

    service.store(
        question="Show all customers",
        sql="SELECT * FROM customers;",
        intent=make_intent(),
        **context(),
    )

    result = service.lookup(
        question="Give me all customers",
        intent=make_intent(),
        **context(),
    )

    assert result is not None

    entry, score = result

    assert entry.sql == "SELECT * FROM customers;"
    assert score >= 0.95
    assert embeddings.calls == 2


def test_unrelated_question_misses():
    service, _, _ = make_service()

    service.store(
        question="Show all customers",
        sql="SELECT * FROM customers;",
        intent=make_intent(),
        **context(),
    )

    result = service.lookup(
        question="Show all products",
        intent=make_intent(),
        **context(),
    )

    assert result is None


def test_different_limit_rejected_after_similarity():
    service, _, _ = make_service()

    sort_intent = make_intent(
        primary=QueryIntent.SORT,
    )

    service.store(
        question="Show the top 5 products",
        sql=(
            "SELECT * FROM products "
            "ORDER BY price DESC LIMIT 5;"
        ),
        intent=sort_intent,
        **context(),
    )

    result = service.lookup(
        question="Show the top 10 products",
        intent=sort_intent,
        **context(),
    )

    assert result is None


def test_same_limit_paraphrase_hits():
    service, _, _ = make_service()

    sort_intent = make_intent(
        primary=QueryIntent.SORT,
    )

    service.store(
        question="Show the top 5 products",
        sql=(
            "SELECT * FROM products "
            "ORDER BY price DESC LIMIT 5;"
        ),
        intent=sort_intent,
        **context(),
    )

    result = service.lookup(
        question="Give me the top 5 products",
        intent=sort_intent,
        **context(),
    )

    assert result is not None


def test_schema_mismatch_misses():
    service, _, _ = make_service()

    service.store(
        question="Show all customers",
        sql="SELECT * FROM customers;",
        intent=make_intent(),
        **context(),
    )

    different_context = context()
    different_context["schema_fingerprint"] = "schema-v2"

    result = service.lookup(
        question="Give me all customers",
        intent=make_intent(),
        **different_context,
    )

    assert result is None


def test_provider_mismatch_misses():
    service, _, _ = make_service()

    service.store(
        question="Show all customers",
        sql="SELECT * FROM customers;",
        intent=make_intent(),
        **context(),
    )

    different_context = context()
    different_context["provider"] = "openai"

    result = service.lookup(
        question="Give me all customers",
        intent=make_intent(),
        **different_context,
    )

    assert result is None


def test_primary_intent_mismatch_rejected():
    service, _, _ = make_service()

    service.store(
        question="Show all customers",
        sql="SELECT * FROM customers;",
        intent=make_intent(),
        **context(),
    )

    result = service.lookup(
        question="Give me all customers",
        intent=make_intent(
            primary=QueryIntent.AGGREGATION,
        ),
        **context(),
    )

    assert result is None


def test_delete():
    service, cache, _ = make_service()

    entry = service.store(
        question="Show all customers",
        sql="SELECT * FROM customers;",
        intent=make_intent(),
        **context(),
    )

    assert service.delete(entry) is True
    assert len(cache) == 0


def test_empty_sql_rejected():
    service, _, _ = make_service()

    try:
        service.store(
            question="Show all customers",
            sql="   ",
            intent=make_intent(),
            **context(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected empty SQL to be rejected"
        )


def run():
    tests = [
        test_store_adds_entry,
        test_safe_paraphrase_hits,
        test_unrelated_question_misses,
        test_different_limit_rejected_after_similarity,
        test_same_limit_paraphrase_hits,
        test_schema_mismatch_misses,
        test_provider_mismatch_misses,
        test_primary_intent_mismatch_rejected,
        test_delete,
        test_empty_sql_rejected,
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