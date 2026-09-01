from app.models.intent import QueryIntent
from app.models.intent_analysis import IntentAnalysis
from app.services.semantic_contract_builder import (
    SemanticContractBuilder,
)


def make_analysis(
    primary: QueryIntent,
    secondary: list[QueryIntent] | None = None,
) -> IntentAnalysis:
    """
    Small helper for constructing IntentAnalysis objects
    without depending on IntentDetector behavior.
    """

    secondary = secondary or []

    return IntentAnalysis(
        primary=primary,
        secondary=secondary,
        scores={},
        confidence=1.0,
    )


def main():
    print("=" * 70)
    print("SEMANTIC CONTRACT BUILDER TEST")
    print("=" * 70)

    builder = SemanticContractBuilder()

    # ------------------------------------------------------
    # 1. Simple lookup
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.LOOKUP,
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.requires_aggregation
        is False
    )

    assert (
        contract.requires_group_by
        is False
    )

    assert (
        contract.requires_order_by
        is False
    )

    assert (
        contract.requires_join
        is False
    )

    print(
        "[PASS] Simple lookup contract"
    )

    # ------------------------------------------------------
    # 2. Aggregation
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.AGGREGATION,
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.requires_aggregation
        is True
    )

    assert (
        contract.requires_group_by
        is False
    )

    print(
        "[PASS] Aggregation contract"
    )

    # ------------------------------------------------------
    # 3. Group-by as secondary intent
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.AGGREGATION,
        secondary=[
            QueryIntent.GROUP_BY,
        ],
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.requires_aggregation
        is True
    )

    assert (
        contract.requires_group_by
        is True
    )

    print(
        "[PASS] Aggregation + group-by contract"
    )

    # ------------------------------------------------------
    # 4. Sorting
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.LOOKUP,
        secondary=[
            QueryIntent.SORT,
        ],
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.requires_order_by
        is True
    )

    print(
        "[PASS] Sort contract"
    )

    # ------------------------------------------------------
    # 5. Join
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.JOIN,
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.requires_join
        is True
    )

    print(
        "[PASS] Join contract"
    )

    # ------------------------------------------------------
    # 6. Multi-intent
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.AGGREGATION,
        secondary=[
            QueryIntent.GROUP_BY,
            QueryIntent.SORT,
            QueryIntent.JOIN,
        ],
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.requires_aggregation
        is True
    )

    assert (
        contract.requires_group_by
        is True
    )

    assert (
        contract.requires_order_by
        is True
    )

    assert (
        contract.requires_join
        is True
    )

    print(
        "[PASS] Multi-intent contract"
    )

    # ------------------------------------------------------
    # 7. UNKNOWN intent
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.UNKNOWN,
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.requires_aggregation
        is False
    )

    assert (
        contract.requires_group_by
        is False
    )

    assert (
        contract.requires_order_by
        is False
    )

    assert (
        contract.requires_join
        is False
    )

    print(
        "[PASS] Unknown intent contract"
    )

    # ------------------------------------------------------
    # 8. Required collections default empty
    # ------------------------------------------------------

    analysis = make_analysis(
        primary=QueryIntent.LOOKUP,
    )

    contract = builder.build(
        analysis
    )

    assert (
        contract.required_tables
        == frozenset()
    )

    assert (
        contract.required_columns
        == frozenset()
    )

    print(
        "[PASS] Required collections default empty"
    )

    print()
    print("=" * 70)
    print(
        "ALL SEMANTIC CONTRACT BUILDER TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()