from app.services.query_service import QueryService


def main():
    print("=" * 70)
    print("SQL CACHE CONTEXT TEST")
    print("=" * 70)

    service = QueryService()

    # ------------------------------------------------------
    # Load real database schema
    # ------------------------------------------------------

    schema = service._load_schema()

    documents = (
        service._build_schema_documents(
            schema
        )
    )

    service._initialize_schema_index(
        documents
    )

    # ------------------------------------------------------
    # Real schema fingerprint
    # ------------------------------------------------------

    fingerprint_1 = (
        service._get_schema_fingerprint()
    )

    assert fingerprint_1

    print(
        "[PASS] Schema fingerprint available"
    )

    print(
        "Fingerprint:",
        fingerprint_1,
    )

    # ------------------------------------------------------
    # Same schema -> same fingerprint
    # ------------------------------------------------------

    service._initialize_schema_index(
        documents
    )

    fingerprint_2 = (
        service._get_schema_fingerprint()
    )

    assert (
        fingerprint_1
        == fingerprint_2
    )

    print(
        "[PASS] Schema fingerprint stable"
    )

    # ------------------------------------------------------
    # LLM context
    # ------------------------------------------------------

    provider, model = (
        service._get_llm_cache_context()
    )

    assert provider
    assert model

    print(
        "[PASS] LLM cache context available"
    )

    print(
        "Provider:",
        provider,
    )

    print(
        "Model:",
        model,
    )

    print()
    print("=" * 70)
    print(
        "ALL SQL CACHE CONTEXT TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()