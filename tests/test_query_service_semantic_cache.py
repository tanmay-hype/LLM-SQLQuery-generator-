from app.cache.semantic_sql_cache import (
    SemanticSQLCache,
)
from app.cache.semantic_sql_cache_service import (
    SemanticSQLCacheService,
)
from app.cache.sql_cache import SQLCache
from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.services.query_service import QueryService


# ==========================================================
# TEST DOUBLES
# ==========================================================


class FakeEmbeddingService:
    def __init__(self):
        self.calls = 0

    def create_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.calls += 1

        embeddings = []

        for text in texts:
            normalized = text.strip().lower()

            if normalized in {
                "show all customers",
                "list all customers",
            }:
                embeddings.append(
                    [1.0, 0.0, 0.0]
                )
            else:
                embeddings.append(
                    [0.0, 1.0, 0.0]
                )

        return embeddings


class FakeStructuralValidator:
    def __init__(self):
        self.calls = 0

    def validate(
        self,
        sql: str,
        schema: dict,
    ) -> str:
        self.calls += 1
        return sql


class FakeSemanticResult:
    def __init__(
        self,
        valid: bool = True,
    ):
        self.valid = valid
        self.errors = []


class FakeSemanticValidator:
    def __init__(self):
        self.calls = 0

    def validate(
        self,
        *,
        question: str,
        sql: str,
        intent: IntentAnalysis,
        schema: dict,
    ):
        self.calls += 1

        return FakeSemanticResult(
            valid=True
        )


# ==========================================================
# HELPERS
# ==========================================================


def make_intent() -> IntentAnalysis:
    return IntentAnalysis(
        primary=QueryIntent.LOOKUP,
        secondary=[],
        scores={
            QueryIntent.LOOKUP: 10,
        },
        confidence=1.0,
    )


def build_service():
    """
    Construct QueryService without calling its normal
    constructor.

    This prevents creation of the real Gemini embedding
    client and other production dependencies.
    """

    service = QueryService.__new__(
        QueryService
    )

    service.sql_cache = SQLCache(
        max_size=16
    )

    service.semantic_sql_cache = (
        SemanticSQLCache(
            max_size=16,
            similarity_threshold=0.95,
        )
    )

    service.embedding_service = (
        FakeEmbeddingService()
    )

    service.semantic_sql_cache_service = (
        SemanticSQLCacheService(
            cache=service.semantic_sql_cache,
            embedding_service=(
                service.embedding_service
            ),
        )
    )

    service.sql_validator = (
        FakeStructuralValidator()
    )

    service.semantic_validator = (
        FakeSemanticValidator()
    )

    return service

def install_fallback_pipeline(
    service,
    *,
    schema: dict,
    intent: IntentAnalysis,
    schema_fingerprint: str,
    provider: str,
    model: str,
    generated_sql: str,
):
    """
    Install deterministic replacements for the normal
    generation pipeline.

    Returns counters so tests can prove that an L2 miss
    or rejection falls through to normal generation.
    """

    counters = {
        "retrieval": 0,
        "generation": 0,
        "execution": 0,
    }

    service._load_schema = (
        lambda: schema
    )

    service._build_schema_documents = (
        lambda schema: ["document"]
    )

    service._initialize_schema_index = (
        lambda documents: None
    )

    service._detect_intent = (
        lambda question: intent
    )

    service._get_schema_fingerprint = (
        lambda: schema_fingerprint
    )

    service._get_llm_cache_context = (
        lambda: (
            provider,
            model,
        )
    )

    def retrieve_schema(
        schema,
        question,
        documents,
    ):
        counters["retrieval"] += 1
        return schema

    service._retrieve_schema = retrieve_schema

    service._compress_schema = (
        lambda schema, question, intent: schema
    )

    service._format_schema = (
        lambda schema: "FORMATTED SCHEMA"
    )

    service._retrieve_examples = (
        lambda intent: []
    )

    service._build_prompt = (
        lambda schema,
        question,
        intent,
        examples: "TEST PROMPT"
    )

    def generate_and_validate_sql(
        prompt,
        question,
        formatted_schema,
        full_schema,
        intent,
    ):
        counters["generation"] += 1
        return generated_sql

    service._generate_and_validate_sql = (
        generate_and_validate_sql
    )

    def execute_sql(sql):
        counters["execution"] += 1

        return [
            {
                "sql": sql,
            }
        ]

    service._execute_sql = execute_sql

    return counters


# ==========================================================
# TEST
# ==========================================================


def test_semantic_hit_bypasses_generation():
    service = build_service()

    intent = make_intent()

    schema = {
        "customers": {
            "columns": [
                {
                    "name": "id",
                },
                {
                    "name": "name",
                },
            ],
            "primary_keys": {
                "constrained_columns": [
                    "id",
                ],
            },
            "foreign_keys": [],
        }
    }

    schema_fingerprint = (
        "test-schema-fingerprint"
    )

    provider = "gemini"
    model = "test-model"

    sql = (
        "SELECT id, name "
        "FROM customers;"
    )

    # ------------------------------------------------------
    # Seed L2 with the original question
    # ------------------------------------------------------

    service.semantic_sql_cache_service.store(
        question="Show all customers",
        sql=sql,
        intent=intent,
        schema_fingerprint=(
            schema_fingerprint
        ),
        provider=provider,
        model=model,
        cache_version="v1",
    )

    # ------------------------------------------------------
    # Confirm the paraphrase is NOT in exact L1
    # ------------------------------------------------------

    cache_key = service.sql_cache.build_key(
        question="List all customers",
        schema_fingerprint=(
            schema_fingerprint
        ),
        provider=provider,
        model=model,
        cache_version="v1",
    )

    assert (
        service.sql_cache.get(
            cache_key
        )
        is None
    )

    # ------------------------------------------------------
    # Perform L2 lookup
    # ------------------------------------------------------

    cached_sql = (
        service._get_semantic_cached_sql(
            question="List all customers",
            intent=intent,
            full_schema=schema,
            schema_fingerprint=(
                schema_fingerprint
            ),
            provider=provider,
            model=model,
        )
    )

    assert cached_sql == sql

    # L2 candidate must have gone through both validators.
    assert (
        service.sql_validator.calls
        == 1
    )

    assert (
        service.semantic_validator.calls
        == 1
    )

    # ------------------------------------------------------
    # Simulate QueryService's L2 → L1 promotion
    # ------------------------------------------------------

    service._store_cached_sql(
        cache_key=cache_key,
        sql=cached_sql,
    )

    assert (
        service.sql_cache.get(
            cache_key
        )
        == sql
    )

def test_generate_sql_semantic_hit_skips_generation():
    service = build_service()

    intent = make_intent()

    schema = {
        "customers": {
            "columns": [
                {
                    "name": "id",
                },
                {
                    "name": "name",
                },
            ],
            "primary_keys": {
                "constrained_columns": [
                    "id",
                ],
            },
            "foreign_keys": [],
        }
    }

    schema_fingerprint = (
        "test-schema-fingerprint"
    )

    provider = "gemini"
    model = "test-model"

    sql = (
        "SELECT id, name "
        "FROM customers;"
    )

    # Seed L2 with equivalent question.
    service.semantic_sql_cache_service.store(
        question="Show all customers",
        sql=sql,
        intent=intent,
        schema_fingerprint=schema_fingerprint,
        provider=provider,
        model=model,
        cache_version="v1",
    )

    # Stub the setup stages used by generate_sql().
    service._load_schema = (
        lambda: schema
    )

    service._build_schema_documents = (
        lambda schema: ["document"]
    )

    service._initialize_schema_index = (
        lambda documents: None
    )

    service._detect_intent = (
        lambda question: intent
    )

    service._get_schema_fingerprint = (
        lambda: schema_fingerprint
    )

    service._get_llm_cache_context = (
        lambda: (
            provider,
            model,
        )
    )

    generation_calls = {
        "count": 0,
    }

    retrieval_calls = {
        "count": 0,
    }

    def fail_if_retrieval_runs(
        *,
        schema,
        question,
        documents,
    ):
        retrieval_calls["count"] += 1

        raise AssertionError(
            "Schema retrieval should not run "
            "on a semantic cache hit."
        )

    def fail_if_generation_runs(
        *,
        prompt,
        question,
        formatted_schema,
        full_schema,
        intent,
    ):
        generation_calls["count"] += 1

        raise AssertionError(
            "SQL generation should not run "
            "on a semantic cache hit."
        )

    service._retrieve_schema = (
        fail_if_retrieval_runs
    )

    service._generate_and_validate_sql = (
        fail_if_generation_runs
    )

    service._execute_sql = (
        lambda sql: [
            {
                "id": 1,
                "name": "Alice",
            }
        ]
    )

    response = service.generate_sql(
        "List all customers"
    )

    assert response.sql == sql

    assert response.results == [
        {
            "id": 1,
            "name": "Alice",
        }
    ]

    assert (
        retrieval_calls["count"]
        == 0
    )

    assert (
        generation_calls["count"]
        == 0
    )

    # Verify L2 hit was promoted into L1.
    cache_key = service.sql_cache.build_key(
        question="List all customers",
        schema_fingerprint=schema_fingerprint,
        provider=provider,
        model=model,
        cache_version="v1",
    )

    assert (
        service.sql_cache.get(
            cache_key
        )
        == sql
    )
    
def test_different_limit_rejects_semantic_cache():
    service = build_service()

    intent = make_intent()

    schema = {
        "products": {
            "columns": [
                {"name": "id"},
                {"name": "name"},
                {"name": "price"},
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    fingerprint = "schema-v1"
    provider = "gemini"
    model = "test-model"

    cached_sql = (
        "SELECT id, name, price "
        "FROM products "
        "ORDER BY price DESC "
        "LIMIT 5;"
    )

    generated_sql = (
        "SELECT id, name, price "
        "FROM products "
        "ORDER BY price DESC "
        "LIMIT 10;"
    )

    service.semantic_sql_cache_service.store(
        question="Show the top 5 products",
        sql=cached_sql,
        intent=intent,
        schema_fingerprint=fingerprint,
        provider=provider,
        model=model,
        cache_version="v1",
    )

    counters = install_fallback_pipeline(
        service,
        schema=schema,
        intent=intent,
        schema_fingerprint=fingerprint,
        provider=provider,
        model=model,
        generated_sql=generated_sql,
    )

    response = service.generate_sql(
        "Show the top 10 products"
    )

    assert response.sql == generated_sql
    assert counters["retrieval"] == 1
    assert counters["generation"] == 1
    assert counters["execution"] == 1


def test_opposite_ranking_rejects_semantic_cache():
    service = build_service()

    intent = make_intent()

    schema = {
        "products": {
            "columns": [
                {"name": "id"},
                {"name": "name"},
                {"name": "price"},
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    fingerprint = "schema-v1"
    provider = "gemini"
    model = "test-model"

    cached_sql = (
        "SELECT id, name, price "
        "FROM products "
        "ORDER BY price ASC "
        "LIMIT 1;"
    )

    generated_sql = (
        "SELECT id, name, price "
        "FROM products "
        "ORDER BY price DESC "
        "LIMIT 1;"
    )

    service.semantic_sql_cache_service.store(
        question="Show the cheapest product",
        sql=cached_sql,
        intent=intent,
        schema_fingerprint=fingerprint,
        provider=provider,
        model=model,
        cache_version="v1",
    )

    counters = install_fallback_pipeline(
        service,
        schema=schema,
        intent=intent,
        schema_fingerprint=fingerprint,
        provider=provider,
        model=model,
        generated_sql=generated_sql,
    )

    response = service.generate_sql(
        "Show the most expensive product"
    )

    assert response.sql == generated_sql
    assert counters["retrieval"] == 1
    assert counters["generation"] == 1
    assert counters["execution"] == 1


def test_schema_fingerprint_mismatch_falls_back():
    service = build_service()

    intent = make_intent()

    schema = {
        "customers": {
            "columns": [
                {"name": "id"},
                {"name": "name"},
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    provider = "gemini"
    model = "test-model"

    cached_sql = (
        "SELECT id, name "
        "FROM customers;"
    )

    generated_sql = (
        "SELECT id, name "
        "FROM customers "
        "ORDER BY id;"
    )

    service.semantic_sql_cache_service.store(
        question="Show all customers",
        sql=cached_sql,
        intent=intent,
        schema_fingerprint="old-schema",
        provider=provider,
        model=model,
        cache_version="v1",
    )

    counters = install_fallback_pipeline(
        service,
        schema=schema,
        intent=intent,
        schema_fingerprint="new-schema",
        provider=provider,
        model=model,
        generated_sql=generated_sql,
    )

    response = service.generate_sql(
        "List all customers"
    )

    assert response.sql == generated_sql
    assert counters["retrieval"] == 1
    assert counters["generation"] == 1
    assert counters["execution"] == 1


def test_invalid_semantic_cached_sql_is_deleted_and_falls_back():
    service = build_service()

    intent = make_intent()

    schema = {
        "customers": {
            "columns": [
                {"name": "id"},
                {"name": "name"},
            ],
            "primary_keys": {
                "constrained_columns": ["id"],
            },
            "foreign_keys": [],
        }
    }

    fingerprint = "schema-v1"
    provider = "gemini"
    model = "test-model"

    bad_sql = (
        "SELECT missing_column "
        "FROM customers;"
    )

    generated_sql = (
        "SELECT id, name "
        "FROM customers;"
    )

    service.semantic_sql_cache_service.store(
        question="Show all customers",
        sql=bad_sql,
        intent=intent,
        schema_fingerprint=fingerprint,
        provider=provider,
        model=model,
        cache_version="v1",
    )

    # Replace the permissive fake structural validator
    # with one that rejects the cached SQL only.
    class RejectBadCachedSQL:
        def validate(
            self,
            sql: str,
            schema: dict,
        ) -> str:
            if sql == bad_sql:
                from app.exceptions import SQLValidationError

                raise SQLValidationError(
                    "Invalid cached SQL"
                )

            return sql

    service.sql_validator = RejectBadCachedSQL()

    counters = install_fallback_pipeline(
        service,
        schema=schema,
        intent=intent,
        schema_fingerprint=fingerprint,
        provider=provider,
        model=model,
        generated_sql=generated_sql,
    )

    response = service.generate_sql(
        "List all customers"
    )

    assert response.sql == generated_sql
    assert counters["retrieval"] == 1
    assert counters["generation"] == 1
    assert counters["execution"] == 1

    # Bad L2 entry should have been deleted.
    assert len(
        service.semantic_sql_cache
    ) == 1

    # The length is 1 because normal generation stores the
    # newly validated replacement SQL back into L2.
    replacement = (
        service.semantic_sql_cache.search(
            tuple(
                service.embedding_service
                .create_embeddings(
                    ["List all customers"]
                )[0]
            ),
            schema_fingerprint=fingerprint,
            provider=provider,
            model=model,
            cache_version="v1",
        )
    )

    assert replacement is not None

    entry, _ = replacement

    assert entry.sql == generated_sql
    assert entry.sql != bad_sql
    
def test_different_unquoted_categorical_value_rejected():
    compatibility = (
        SemanticSQLCacheCompatibility()
    )

    intent = make_intent(
        primary=QueryIntent.FILTER
    )

    compatible = compatibility.is_compatible(
        cached_question=(
            "Show customers from Mumbai"
        ),
        new_question=(
            "Show customers from Delhi"
        ),
        cached_intent=intent,
        new_intent=intent,
    )

    assert compatible is False


# ==========================================================
# SIMPLE RUNNER
# ==========================================================


def main():
    tests = [
        test_semantic_hit_bypasses_generation,
        test_generate_sql_semantic_hit_skips_generation,
        test_different_limit_rejects_semantic_cache,
        test_opposite_ranking_rejects_semantic_cache,
        test_schema_fingerprint_mismatch_falls_back,
        test_invalid_semantic_cached_sql_is_deleted_and_falls_back,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(
                f"[PASS] {test.__name__}"
            )
            passed += 1

        except Exception as exc:
            print(
                f"[FAIL] {test.__name__}: "
                f"{exc}"
            )
            failed += 1

    print()
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(
        f"TOTAL: {passed + failed}"
    )

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()