from app.services.query_service import QueryService


# ==========================================================
# BENCHMARK CASES
# ==========================================================

TEST_CASES = [
    {
        "question": "Show customer contact details",
        "required_tables": {
            "customers",
        },
    },
    {
        "question": "Which products were ordered?",
        "required_tables": {
            "products",
            "order_items",
        },
    },
    {
        "question": "Show total order amount per customer",
        "required_tables": {
            "orders",
            "customers",
        },
    },
    {
        "question": "Show monthly order trends",
        "required_tables": {
            "orders",
        },
    },
    {
        "question": "Which customers spent the most money?",
        "required_tables": {
            "customers",
            "orders",
        },
    },
    {
        "question": "Which products generated the most revenue?",
        "required_tables": {
            "products",
            "order_items",
        },
    },
    {
        "question": "What items have actually been purchased?",
        "required_tables": {
            "products",
            "order_items",
        },
    },
    {
        "question": "Show purchasing activity over time",
        "required_tables": {
            "orders",
        },
    },
    {
        "question": "Which customers buy the most products?",
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
    },
    {
        "question": "Show product categories and prices",
        "required_tables": {
            "products",
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
    Calculate retrieval precision and recall.

    Precision:
        How many retrieved tables were actually required?

    Recall:
        How many required tables were successfully retrieved?

    Pass:
        Every required table was retrieved.
    """

    if not retrieved_tables:
        precision = 0.0
    else:
        precision = (
            len(
                required_tables
                & retrieved_tables
            )
            / len(retrieved_tables)
        )

    if not required_tables:
        recall = 1.0
    else:
        recall = (
            len(
                required_tables
                & retrieved_tables
            )
            / len(required_tables)
        )

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
) -> bool:

    precision, recall, passed = (
        calculate_metrics(
            required_tables=required_tables,
            retrieved_tables=retrieved_tables,
        )
    )

    print()
    print(f"[{retriever_name}]")
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

    return passed


# ==========================================================
# MAIN BENCHMARK
# ==========================================================

def main():

    print("=" * 80)
    print("SCHEMA RETRIEVAL BENCHMARK")
    print("=" * 80)

    # ------------------------------------------------------
    # Create service
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
    # Build semantic documents
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
    # Initialize/load persisted FAISS index
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
    # RUN TEST CASES
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

        # --------------------------------------------------
        # KEYWORD RETRIEVAL
        # --------------------------------------------------

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
        ) = calculate_metrics(
            required_tables,
            keyword_tables,
        )

        keyword_precision_total += (
            keyword_precision
        )

        keyword_recall_total += (
            keyword_recall
        )

        if print_result(
            "KEYWORD",
            required_tables,
            keyword_tables,
        ):
            keyword_passed += 1

        # --------------------------------------------------
        # SEMANTIC RETRIEVAL
        # --------------------------------------------------

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
        ) = calculate_metrics(
            required_tables,
            semantic_tables,
        )

        semantic_precision_total += (
            semantic_precision
        )

        semantic_recall_total += (
            semantic_recall
        )

        if print_result(
            "SEMANTIC",
            required_tables,
            semantic_tables,
        ):
            semantic_passed += 1

        # --------------------------------------------------
        # HYBRID RETRIEVAL
        # --------------------------------------------------

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
        ) = calculate_metrics(
            required_tables,
            hybrid_tables,
        )

        hybrid_precision_total += (
            hybrid_precision
        )

        hybrid_recall_total += (
            hybrid_recall
        )

        if print_result(
            "HYBRID",
            required_tables,
            hybrid_tables,
        ):
            hybrid_passed += 1

    # ======================================================
    # FINAL SUMMARY
    # ======================================================

    total = len(TEST_CASES)

    print()
    print("=" * 80)
    print("RETRIEVAL BENCHMARK SUMMARY")
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