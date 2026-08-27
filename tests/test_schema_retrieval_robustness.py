from app.services.query_service import QueryService


# ==========================================================
# ROBUSTNESS TEST CASES
# ==========================================================

TEST_CASES = [
    {
        "question": "Who has spent the most?",
        "required_tables": {
            "customers",
            "orders",
        },
    },
    {
        "question": "Show buyers and their total purchases",
        "required_tables": {
            "customers",
            "orders",
        },
    },
    {
        "question": "Which catalog items are most valuable?",
        "required_tables": {
            "products",
        },
    },
    {
        "question": "Give me sales activity by month",
        "required_tables": {
            "orders",
        },
    },
    {
        "question": "Which people bought the greatest number of items?",
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
    },
    {
        "question": "Show the value of purchases for each buyer",
        "required_tables": {
            "customers",
            "orders",
        },
    },
    {
        "question": "Which merchandise has actually been purchased?",
        "required_tables": {
            "products",
            "order_items",
        },
    },
    {
        "question": "Show purchase history over time",
        "required_tables": {
            "orders",
        },
    },
    {
        "question": "Which buyers purchased the largest number of products?",
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
    },
    {
        "question": "Show item categories and their prices",
        "required_tables": {
            "products",
        },
    },
    {
        "question": "Which buyers placed transactions?",
        "required_tables": {
            "customers",
            "orders",
        },
    },
    {
        "question": "Which items produced the highest sales value?",
        "required_tables": {
            "products",
            "order_items",
        },
    },
]


# ==========================================================
# METRICS
# ==========================================================

def calculate_metrics(
    required_tables: set[str],
    retrieved_tables: set[str],
) -> tuple[float, float, bool]:
    """
    Calculate precision, recall and pass/fail.

    Pass means every required table was retrieved.
    """

    if retrieved_tables:
        precision = (
            len(
                required_tables
                & retrieved_tables
            )
            / len(retrieved_tables)
        )
    else:
        precision = 0.0

    if required_tables:
        recall = (
            len(
                required_tables
                & retrieved_tables
            )
            / len(required_tables)
        )
    else:
        recall = 1.0

    passed = (
        required_tables
        <= retrieved_tables
    )

    return (
        precision,
        recall,
        passed,
    )


# ==========================================================
# RESULT PRINTER
# ==========================================================

def print_result(
    retriever_name: str,
    required_tables: set[str],
    retrieved_tables: set[str],
) -> tuple[float, float, bool]:

    precision, recall, passed = (
        calculate_metrics(
            required_tables,
            retrieved_tables,
        )
    )

    print()
    print(
        f"[{retriever_name}]"
    )

    print(
        "Required:",
        sorted(required_tables),
    )

    print(
        "Retrieved:",
        sorted(retrieved_tables),
    )

    print(
        f"Precision: {precision * 100:.2f}%"
    )

    print(
        f"Recall:    {recall * 100:.2f}%"
    )

    print(
        "Status:",
        "PASS" if passed else "FAIL",
    )

    return (
        precision,
        recall,
        passed,
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 80)
    print("SCHEMA RETRIEVAL ROBUSTNESS TEST")
    print("=" * 80)

    # ------------------------------------------------------
    # Initialize service
    # ------------------------------------------------------

    service = QueryService()

    # ------------------------------------------------------
    # Load schema
    # ------------------------------------------------------

    schema = (
        service.schema_loader.load_schema()
    )

    print()
    print(
        "TABLES:",
        list(schema.keys()),
    )

    # ------------------------------------------------------
    # Build schema documents
    # ------------------------------------------------------

    documents = (
        service.schema_document_builder.build(
            schema
        )
    )

    print(
        "SCHEMA DOCUMENTS:",
        len(documents),
    )

    # ------------------------------------------------------
    # Initialize / load FAISS index
    # ------------------------------------------------------

    service.schema_index_service.initialize(
        documents
    )

    print(
        "SCHEMA INDEX: READY"
    )

    # ======================================================
    # TOTALS
    # ======================================================

    total = len(TEST_CASES)

    keyword_passed = 0
    semantic_passed = 0
    hybrid_passed = 0

    keyword_precision_total = 0.0
    keyword_recall_total = 0.0

    semantic_precision_total = 0.0
    semantic_recall_total = 0.0

    hybrid_precision_total = 0.0
    hybrid_recall_total = 0.0

    # ======================================================
    # TEST LOOP
    # ======================================================

    for index, test in enumerate(
        TEST_CASES,
        start=1,
    ):

        question = test["question"]

        required_tables = set(
            test["required_tables"]
        )

        print()
        print("=" * 80)
        print(
            f"TEST {index}: {question}"
        )
        print("=" * 80)

        # ==================================================
        # KEYWORD
        # ==================================================

        keyword_result = (
            service.keyword_retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )
        )

        keyword_tables = set(
            keyword_result.schema.keys()
        )

        (
            keyword_precision,
            keyword_recall,
            keyword_ok,
        ) = print_result(
            "KEYWORD",
            required_tables,
            keyword_tables,
        )

        keyword_precision_total += (
            keyword_precision
        )

        keyword_recall_total += (
            keyword_recall
        )

        if keyword_ok:
            keyword_passed += 1

        # ==================================================
        # SEMANTIC
        # ==================================================

        semantic_result = (
            service.semantic_retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )
        )

        semantic_tables = set(
            semantic_result.schema.keys()
        )

        (
            semantic_precision,
            semantic_recall,
            semantic_ok,
        ) = print_result(
            "SEMANTIC",
            required_tables,
            semantic_tables,
        )

        semantic_precision_total += (
            semantic_precision
        )

        semantic_recall_total += (
            semantic_recall
        )

        if semantic_ok:
            semantic_passed += 1

        # ==================================================
        # HYBRID
        # ==================================================

        hybrid_schema = (
            service.schema_retriever.retrieve(
                schema=schema,
                question=question,
                documents=documents,
            )
        )

        hybrid_tables = set(
            hybrid_schema.keys()
        )

        (
            hybrid_precision,
            hybrid_recall,
            hybrid_ok,
        ) = print_result(
            "HYBRID",
            required_tables,
            hybrid_tables,
        )

        hybrid_precision_total += (
            hybrid_precision
        )

        hybrid_recall_total += (
            hybrid_recall
        )

        if hybrid_ok:
            hybrid_passed += 1

    # ======================================================
    # SUMMARY
    # ======================================================

    print()
    print("=" * 80)
    print("ROBUSTNESS TEST SUMMARY")
    print("=" * 80)

    print()
    print("KEYWORD RETRIEVER")
    print("-" * 80)

    print(
        f"Passed: {keyword_passed}/{total}"
    )

    print(
        "Success Rate: "
        f"{keyword_passed / total * 100:.2f}%"
    )

    print(
        "Average Precision: "
        f"{keyword_precision_total / total * 100:.2f}%"
    )

    print(
        "Average Recall: "
        f"{keyword_recall_total / total * 100:.2f}%"
    )

    print()

    print("SEMANTIC RETRIEVER")
    print("-" * 80)

    print(
        f"Passed: {semantic_passed}/{total}"
    )

    print(
        "Success Rate: "
        f"{semantic_passed / total * 100:.2f}%"
    )

    print(
        "Average Precision: "
        f"{semantic_precision_total / total * 100:.2f}%"
    )

    print(
        "Average Recall: "
        f"{semantic_recall_total / total * 100:.2f}%"
    )

    print()

    print("HYBRID RETRIEVER")
    print("-" * 80)

    print(
        f"Passed: {hybrid_passed}/{total}"
    )

    print(
        "Success Rate: "
        f"{hybrid_passed / total * 100:.2f}%"
    )

    print(
        "Average Precision: "
        f"{hybrid_precision_total / total * 100:.2f}%"
    )

    print(
        "Average Recall: "
        f"{hybrid_recall_total / total * 100:.2f}%"
    )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()