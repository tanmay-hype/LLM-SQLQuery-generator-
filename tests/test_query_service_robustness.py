from sqlglot import exp, parse_one

from app.services.query_service import QueryService


# ==========================================================
# ROBUSTNESS CASES
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
        "question": (
            "Which people bought the greatest "
            "number of items?"
        ),
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
    },
    {
        "question": (
            "Show the value of purchases "
            "for each buyer"
        ),
        "required_tables": {
            "customers",
            "orders",
        },
    },
    {
        "question": (
            "Which merchandise has actually "
            "been purchased?"
        ),
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
        "question": (
            "Which buyers purchased the largest "
            "number of products?"
        ),
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
    },
    {
        "question": (
            "Show item categories and their prices"
        ),
        "required_tables": {
            "products",
        },
    },
    {
        "question": (
            "Which buyers placed transactions?"
        ),
        "required_tables": {
            "customers",
            "orders",
        },
    },
    {
        "question": (
            "Which items produced the highest "
            "sales value?"
        ),
        "required_tables": {
            "products",
            "order_items",
        },
    },
]


# ==========================================================
# SQL TABLE EXTRACTION
# ==========================================================

def extract_tables(
    sql: str,
) -> set[str]:
    """
    Extract physical table names from generated SQL.
    """

    statement = parse_one(
        sql,
        read="postgres",
    )

    cte_names = {
        cte.alias_or_name
        for cte in statement.find_all(
            exp.CTE
        )
        if cte.alias_or_name
    }

    tables: set[str] = set()

    for table in statement.find_all(
        exp.Table
    ):

        table_name = table.name

        if not table_name:
            continue

        if table_name in cte_names:
            continue

        tables.add(
            table_name
        )

    return tables


# ==========================================================
# MAIN TEST
# ==========================================================

def main():

    print("=" * 80)
    print("QUERY SERVICE ROBUSTNESS TEST")
    print("=" * 80)

    service = QueryService()

    passed = 0
    failed = 0

    table_recall_total = 0.0

    # ======================================================
    # RUN CASES
    # ======================================================

    for index, test in enumerate(
        TEST_CASES,
        start=1,
    ):

        question = test[
            "question"
        ]

        required_tables = set(
            test[
                "required_tables"
            ]
        )

        print()
        print("=" * 80)
        print(
            f"TEST {index}: {question}"
        )
        print("=" * 80)

        try:

            # ----------------------------------------------
            # Run complete application pipeline
            # ----------------------------------------------

            response = (
                service.generate_sql(
                    question
                )
            )

            sql = response.sql

            # ----------------------------------------------
            # Extract physical tables used by final SQL
            # ----------------------------------------------

            sql_tables = extract_tables(
                sql
            )

            # ----------------------------------------------
            # Calculate table recall
            # ----------------------------------------------

            matched_tables = (
                required_tables
                & sql_tables
            )

            table_recall = (
                len(matched_tables)
                / len(required_tables)
                if required_tables
                else 1.0
            )

            table_recall_total += (
                table_recall
            )

            missing_tables = (
                required_tables
                - sql_tables
            )

            case_passed = (
                not missing_tables
            )

            # ----------------------------------------------
            # Output
            # ----------------------------------------------

            print()
            print("GENERATED SQL:")
            print("-" * 80)
            print(sql)

            print()
            print(
                "REQUIRED TABLES:",
                sorted(
                    required_tables
                ),
            )

            print(
                "SQL TABLES:",
                sorted(
                    sql_tables
                ),
            )

            print(
                "TABLE RECALL:",
                f"{table_recall * 100:.2f}%",
            )

            print(
                "MISSING TABLES:",
                sorted(
                    missing_tables
                ),
            )

            print()

            if case_passed:

                print(
                    "STATUS: PASS"
                )

                passed += 1

            else:

                print(
                    "STATUS: FAIL"
                )

                failed += 1

        except Exception as exc:

            failed += 1

            print()
            print(
                "STATUS: EXCEPTION"
            )

            print(
                "EXCEPTION:",
                type(exc).__name__,
            )

            print(
                "MESSAGE:",
                str(exc),
            )

    # ======================================================
    # SUMMARY
    # ======================================================

    total = len(
        TEST_CASES
    )

    success_rate = (
        passed
        / total
        * 100
    )

    average_table_recall = (
        table_recall_total
        / total
        * 100
    )

    print()
    print("=" * 80)
    print(
        "QUERY SERVICE ROBUSTNESS SUMMARY"
    )
    print("=" * 80)

    print(
        f"PASSED: {passed}"
    )

    print(
        f"FAILED: {failed}"
    )

    print(
        f"TOTAL:  {total}"
    )

    print(
        "SUCCESS RATE: "
        f"{success_rate:.2f}%"
    )

    print(
        "AVERAGE SQL TABLE RECALL: "
        f"{average_table_recall:.2f}%"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()