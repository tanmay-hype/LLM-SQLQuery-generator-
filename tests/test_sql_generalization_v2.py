import argparse
import json
from pathlib import Path

from app.services.query_service import QueryService
from tests.sql_benchmark_evaluator import evaluate_case

V2_TEST_CASES = [
    # =====================================================
    # A. NATURAL-LANGUAGE PARAPHRASES
    # =====================================================

    {
        "id": 1,
        "question": "Give me the names of everyone in the customer list",
        "category": "paraphrase",
    },
    {
        "id": 2,
        "question": "What items do we currently sell?",
        "category": "paraphrase",
    },
    {
        "id": 3,
        "question": "Give me every purchase order in the system",
        "category": "paraphrase",
    },
    {
        "id": 4,
        "question": "Who are our buyers?",
        "category": "paraphrase",
    },
    {
        "id": 5,
        "question": "What does each product cost?",
        "category": "paraphrase",
    },

    # =====================================================
    # B. FILTERS / COMPOUND CONDITIONS
    # =====================================================

    {
        "id": 6,
        "question": "Show customers from Mumbai",
        "category": "filter",
    },
    {
        "id": 7,
        "question": "Show Electronics products costing more than 1000",
        "category": "compound_filter",
    },
    {
        "id": 8,
        "question": "Find products priced between 500 and 2000",
        "category": "compound_filter",
    },
    {
        "id": 9,
        "question": "Show orders with a total amount greater than 5000",
        "category": "filter",
    },
    {
        "id": 10,
        "question": "List customers who are not from Delhi",
        "category": "filter",
    },

    # =====================================================
    # C. AGGREGATION / GROUPING
    # =====================================================

    {
        "id": 11,
        "question": "How many products are in each category?",
        "category": "aggregation",
    },
    {
        "id": 12,
        "question": "What is the average product price by category?",
        "category": "aggregation",
    },
    {
        "id": 13,
        "question": "How many orders has each customer placed?",
        "category": "aggregation_join",
    },
    {
        "id": 14,
        "question": "What quantity of each product has been sold?",
        "category": "aggregation_join",
    },
    {
        "id": 15,
        "question": "What is the average amount spent per order by each customer?",
        "category": "aggregation_join",
    },

    # =====================================================
    # D. RANKING / SUPERLATIVES
    # =====================================================

    {
        "id": 16,
        "question": "Which customer has spent the most money?",
        "category": "ranking",
    },
    {
        "id": 17,
        "question": "Which product has sold the greatest quantity?",
        "category": "ranking",
    },
    {
        "id": 18,
        "question": "Show the 5 cheapest products",
        "category": "ranking",
    },
    {
        "id": 19,
        "question": "Show the 2 most expensive Electronics products",
        "category": "ranking_filter",
    },

    # =====================================================
    # E. MULTI-HOP RELATIONSHIPS
    # =====================================================

    {
        "id": 20,
        "question": "Show each customer together with every product they ordered",
        "category": "multi_hop_join",
    },
    {
        "id": 21,
        "question": "How many different products has each customer purchased?",
        "category": "multi_hop_join",
    },
    {
        "id": 22,
        "question": "How much revenue has each product generated?",
        "category": "multi_hop_join",
    },
    {
        "id": 23,
        "question": "Show the total quantity purchased by each customer",
        "category": "multi_hop_join",
    },

    # =====================================================
    # F. TIME / DATE
    # =====================================================

    {
        "id": 24,
        "question": "How many orders were placed each month?",
        "category": "time_series",
    },
    {
        "id": 25,
        "question": "Show total order revenue for each day",
        "category": "time_series",
    },
    {
        "id": 26,
        "question": "Show orders placed after January 1, 2025",
        "category": "date_filter",
    },
    {
        "id": 27,
        "question": "Show the most recent 5 orders",
        "category": "time_sort",
    },

    # =====================================================
    # G. COMBINED MULTI-INTENT
    # =====================================================

    {
        "id": 28,
        "question": "Show the top 3 products by total sales revenue",
        "category": "multi_intent",
    },
    {
        "id": 29,
        "question": "Show the top 5 customers by total quantity purchased",
        "category": "multi_intent",
    },
    {
        "id": 30,
        "question": "Show total spending by customer from highest to lowest",
        "category": "multi_intent",
    },
    {
        "id": 31,
        "question": "Show monthly revenue ordered from newest month to oldest",
        "category": "multi_intent",
    },

    # =====================================================
    # H. AMBIGUOUS / UNDERSPECIFIED
    # =====================================================

    {
        "id": 32,
        "question": "Show totals",
        "category": "ambiguous",
    },
    {
        "id": 33,
        "question": "Show activity",
        "category": "ambiguous",
    },
    {
        "id": 34,
        "question": "Show the best customers",
        "category": "ambiguous",
    },

    # =====================================================
    # I. UNSUPPORTED SCHEMA
    # =====================================================

    {
        "id": 35,
        "question": "Show customer phone numbers and addresses",
        "category": "unsupported_schema",
    },
    {
        "id": 36,
        "question": "Which supplier provides each product?",
        "category": "unsupported_schema",
    },
    {
        "id": 37,
        "question": "Show payment methods used for each order",
        "category": "unsupported_schema",
    },

    # =====================================================
    # J. ADVERSARIAL / SCHEMA GROUNDING
    # =====================================================

    {
        "id": 38,
        "question": "Show customers with their loyalty points",
        "category": "hallucination_resistance",
    },
    {
        "id": 39,
        "question": "List orders and their shipping status",
        "category": "hallucination_resistance",
    },
    {
        "id": 40,
        "question": "Show product inventory levels by warehouse",
        "category": "hallucination_resistance",
    },
]


# =========================================================
# V2 EXPECTED SEMANTICS
# =========================================================
#
# These expectations describe semantic requirements rather
# than exact SQL strings.
#
# IMPORTANT:
#
# They are defined before running the benchmark against the
# LLM so that evaluation is not fitted to generated output.
#
# =========================================================


V2_EXPECTATIONS = {

    # -----------------------------------------------------
    # A. NATURAL-LANGUAGE PARAPHRASES
    # -----------------------------------------------------

    1: {
        "required_tables": {
            "customers",
        },
        "required_columns": {
            "name",
        },
    },

    2: {
        "required_tables": {
            "products",
        },
    },

    3: {
        "required_tables": {
            "orders",
        },
    },

    4: {
        "required_tables": {
            "customers",
        },
    },

    5: {
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
    },

    # -----------------------------------------------------
    # B. FILTERS / COMPOUND CONDITIONS
    # -----------------------------------------------------

    6: {
        "required_tables": {
            "customers",
        },
        "required_columns": {
            "city",
        },
        "requires_where": True,
        "required_literals": {
            "Mumbai",
        },
        "required_comparisons": {
            "=",
        },
    },

    7: {
        "required_tables": {
            "products",
        },
        "required_columns": {
            "category",
            "price",
        },
        "requires_where": True,
        "required_literals": {
            "Electronics",
            "1000",
        },
        "required_comparisons": {
            ">",
            "=",
        },
    },

    8: {
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
        "requires_where": True,
        "required_literals": {
            "500",
            "2000",
        },
        "required_comparisons": {
            "BETWEEN",
        },
    },

    9: {
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "total_amount",
        },
        "requires_where": True,
        "required_literals": {
            "5000",
        },
        "required_comparisons": {
            ">",
        },
    },

    10: {
        "required_tables": {
            "customers",
        },
        "required_columns": {
            "city",
        },
        "requires_where": True,
        "required_literals": {
            "Delhi",
        },
        "required_comparisons": {
            "!=",
        },
    },

    # -----------------------------------------------------
    # C. AGGREGATION / GROUPING
    # -----------------------------------------------------

    11: {
        "required_tables": {
            "products",
        },
        "required_columns": {
            "category",
        },
        "required_aggregates": {
            "COUNT",
        },
        "requires_group_by": True,
    },

    12: {
        "required_tables": {
            "products",
        },
        "required_columns": {
            "category",
            "price",
        },
        "required_aggregates": {
            "AVG",
        },
        "requires_group_by": True,
    },

    13: {
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "customer_id",
        },
        "requires_join": True,
        "required_aggregates": {
            "COUNT",
        },
        "requires_group_by": True,
    },

    14: {
        "required_tables": {
            "products",
            "order_items",
        },
        "required_columns": {
            "product_id",
            "quantity",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
    },

    15: {
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "customer_id",
            "total_amount",
        },
        "requires_join": True,
        "required_aggregates": {
            "AVG",
        },
        "requires_group_by": True,
    },

    # -----------------------------------------------------
    # D. RANKING / SUPERLATIVES
    # -----------------------------------------------------

    16: {
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "customer_id",
            "total_amount",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
        "expected_limit": 1,
    },

    17: {
        "required_tables": {
            "products",
            "order_items",
        },
        "required_columns": {
            "product_id",
            "quantity",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
        "expected_limit": 1,
    },

    18: {
        "required_tables": {
            "products",
        },
        "required_columns": {
            "price",
        },
        "requires_order_by": True,
        "order_direction": "ASC",
        "expected_limit": 5,
    },

    19: {
        "required_tables": {
            "products",
        },
        "required_columns": {
            "category",
            "price",
        },
        "requires_where": True,
        "required_literals": {
            "Electronics",
        },
        "required_comparisons": {
            "=",
        },
        "requires_order_by": True,
        "order_direction": "DESC",
        "expected_limit": 2,
    },

    # -----------------------------------------------------
    # E. MULTI-HOP RELATIONSHIPS
    # -----------------------------------------------------

    20: {
        "required_tables": {
            "customers",
            "orders",
            "order_items",
            "products",
        },
        "requires_join": True,
    },

    21: {
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
        "required_columns": {
            "customer_id",
            "order_id",
            "product_id",
        },
        "requires_join": True,
        "required_aggregates": {
            "COUNT",
        },
        "requires_distinct_aggregate": True,
        "requires_group_by": True,
    },

    22: {
        "required_tables": {
            "products",
            "order_items",
        },
        "required_columns": {
            "product_id",
            "quantity",
            "unit_price",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_revenue_expression": True,
    },

    23: {
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
        "required_columns": {
            "customer_id",
            "order_id",
            "quantity",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
    },

    # -----------------------------------------------------
    # F. TIME / DATE
    # -----------------------------------------------------

    24: {
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
        },
        "required_aggregates": {
            "COUNT",
        },
        "requires_group_by": True,
        "required_date_granularity": "month",
    },

    25: {
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "required_date_granularity": "day",
    },

    26: {
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
        },
        "requires_where": True,
        "required_literals": {
            "2025-01-01",
        },
        "required_comparisons": {
            ">",
        },
    },

    27: {
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
        },
        "requires_order_by": True,
        "order_direction": "DESC",
        "expected_limit": 5,
    },

    # -----------------------------------------------------
    # G. COMBINED MULTI-INTENT
    # -----------------------------------------------------

    28: {
        "required_tables": {
            "products",
            "order_items",
        },
        "required_columns": {
            "product_id",
            "quantity",
            "unit_price",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_revenue_expression": True,
        "requires_order_by": True,
        "order_direction": "DESC",
        "expected_limit": 3,
    },

    29: {
        "required_tables": {
            "customers",
            "orders",
            "order_items",
        },
        "required_columns": {
            "customer_id",
            "order_id",
            "quantity",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
        "expected_limit": 5,
    },

    30: {
        "required_tables": {
            "customers",
            "orders",
        },
        "required_columns": {
            "customer_id",
            "total_amount",
        },
        "requires_join": True,
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "requires_order_by": True,
        "order_direction": "DESC",
    },

    31: {
        "required_tables": {
            "orders",
        },
        "required_columns": {
            "order_date",
            "total_amount",
        },
        "required_aggregates": {
            "SUM",
        },
        "requires_group_by": True,
        "required_date_granularity": "month",
        "requires_order_by": True,
        "order_direction": "DESC",
    },

    # -----------------------------------------------------
    # H. AMBIGUOUS / UNDERSPECIFIED
    # -----------------------------------------------------
    #
    # V2 policy:
    #
    # These questions do not contain enough information to
    # determine one reliable SQL interpretation.
    #
    # Therefore they should NOT silently invent semantics.
    # -----------------------------------------------------

    32: {
        "expected_insufficient": True,
    },

    33: {
        "expected_insufficient": True,
    },

    34: {
        "expected_insufficient": True,
    },

    # -----------------------------------------------------
    # I. UNSUPPORTED SCHEMA
    # -----------------------------------------------------

    35: {
        "expected_insufficient": True,
    },

    36: {
        "expected_insufficient": True,
    },

    37: {
        "expected_insufficient": True,
    },

    # -----------------------------------------------------
    # J. ADVERSARIAL / SCHEMA GROUNDING
    # -----------------------------------------------------

    38: {
        "expected_insufficient": True,
    },

    39: {
        "expected_insufficient": True,
    },

    40: {
        "expected_insufficient": True,
    },
}


# =========================================================
# BENCHMARK CONFIGURATION
# =========================================================


CACHE_PATH = Path(
    "tests/benchmark_cache/sql_generalization_v2.json"
)


# =========================================================
# DEFINITION VALIDATION
# =========================================================


def validate_definition() -> None:
    """
    Validate the benchmark definition without invoking
    QueryService or making any LLM/API calls.
    """

    test_ids = {
        case["id"]
        for case in V2_TEST_CASES
    }

    expectation_ids = set(
        V2_EXPECTATIONS
    )

    assert len(V2_TEST_CASES) == 40, (
        "V2 must contain exactly 40 test cases."
    )

    assert len(test_ids) == 40, (
        "V2 test IDs must be unique."
    )

    assert test_ids == expectation_ids, (
        f"ID mismatch. "
        f"Missing expectations: "
        f"{test_ids - expectation_ids}; "
        f"Missing tests: "
        f"{expectation_ids - test_ids}"
    )


# =========================================================
# BENCHMARK CACHE
# =========================================================


def load_benchmark_cache() -> dict:
    """
    Load previously generated V2 SQL.

    This cache is benchmark-only and is separate from the
    production SQL cache.
    """

    if not CACHE_PATH.exists():
        return {}

    try:
        payload = json.loads(
            CACHE_PATH.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(
        payload,
        dict,
    ):
        return {}

    return payload


def save_benchmark_cache(
    cache: dict,
) -> None:
    """
    Persist generated V2 SQL.
    """

    CACHE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    CACHE_PATH.write_text(
        json.dumps(
            cache,
            indent=4,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def get_cached_sql(
    cache: dict,
    test_id: int,
    question: str,
) -> str | None:
    """
    Return cached SQL only when the cached question still
    matches the current frozen benchmark question.
    """

    entry = cache.get(
        str(test_id)
    )

    if not isinstance(
        entry,
        dict,
    ):
        return None

    if (
        entry.get("question")
        != question
    ):
        return None

    sql = entry.get(
        "sql"
    )

    if not isinstance(
        sql,
        str,
    ):
        return None

    sql = sql.strip()

    if not sql:
        return None

    return sql


def store_cached_sql(
    cache: dict,
    test_id: int,
    question: str,
    sql: str,
) -> None:
    """
    Store generated SQL for one benchmark case.
    """

    cache[
        str(test_id)
    ] = {
        "question": question,
        "sql": sql,
    }


# =========================================================
# TEST SELECTION
# =========================================================


def parse_test_numbers(
    value: str,
) -> list[int]:
    """
    Parse:

        --tests 7,10,21

    into:

        [7, 10, 21]
    """

    values: list[int] = []

    for item in value.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            number = int(
                item
            )
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"Invalid test number: {item}"
            ) from exc

        values.append(
            number
        )

    if not values:
        raise argparse.ArgumentTypeError(
            "At least one test number is required."
        )

    return values


def get_selected_tests(
    single_test: int | None,
    multiple_tests: list[int] | None,
    run_all: bool,
) -> list[dict]:
    """
    Select benchmark cases.

    No selection means no LLM execution.
    """

    if run_all:
        return list(
            V2_TEST_CASES
        )

    requested: list[int] = []

    if single_test is not None:
        requested.append(
            single_test
        )

    if multiple_tests:
        requested.extend(
            multiple_tests
        )

    requested = list(
        dict.fromkeys(
            requested
        )
    )

    if not requested:
        return []

    valid_ids = {
        case["id"]
        for case in V2_TEST_CASES
    }

    invalid = [
        test_id
        for test_id in requested
        if test_id not in valid_ids
    ]

    if invalid:
        raise ValueError(
            "Invalid test number(s): "
            + ", ".join(
                str(test_id)
                for test_id in invalid
            )
            + ". Valid range is 1-40."
        )

    cases_by_id = {
        case["id"]: case
        for case in V2_TEST_CASES
    }

    return [
        cases_by_id[
            test_id
        ]
        for test_id in requested
    ]


# =========================================================
# DISPLAY
# =========================================================


def list_tests() -> None:
    """
    Display the V2 benchmark without invoking QueryService.
    """

    print(
        "=" * 80
    )

    print(
        "SQL GENERALIZATION BENCHMARK V2"
    )

    print(
        "=" * 80
    )

    for case in V2_TEST_CASES:
        print(
            f"{case['id']:>2}: "
            f"[{case['category']}] "
            f"{case['question']}"
        )

    print(
        "=" * 80
    )


# =========================================================
# QUERY SERVICE RESULT
# =========================================================


def extract_sql(
    result,
) -> str:
    """
    QueryService currently returns SQLResponse in production,
    but keeping this small adapter makes the benchmark tolerant
    of a plain-string result during isolated testing.
    """

    if isinstance(
        result,
        str,
    ):
        return result.strip()

    sql = getattr(
        result,
        "sql",
        None,
    )

    if not isinstance(
        sql,
        str,
    ):
        raise TypeError(
            "QueryService.generate_sql() did not return "
            "a SQL string or an object with a string "
            "'sql' attribute."
        )

    return sql.strip()


# =========================================================
# BENCHMARK EXECUTION
# =========================================================


def run_benchmark(
    selected_cases: list[dict],
    *,
    cached_only: bool,
    refresh: bool,
) -> int:
    """
    Execute selected V2 benchmark cases.

    Important:

    --cached
        Never invokes QueryService.

    --refresh
        Forces benchmark-level fresh generation.

    Default
        Uses benchmark cache when available and generates only
        missing cases.
    """

    cache = load_benchmark_cache()

    service = None

    passed = 0
    failed = 0
    errors = 0

    cache_hits = 0
    fresh_generations = 0

    total = len(
        selected_cases
    )

    print(
        "=" * 80
    )

    print(
        "SQL GENERALIZATION BENCHMARK V2"
    )

    print(
        "=" * 80
    )

    for case in selected_cases:
        test_id = case[
            "id"
        ]

        question = case[
            "question"
        ]

        category = case[
            "category"
        ]

        expectations = V2_EXPECTATIONS[
            test_id
        ]

        print()

        print(
            "-" * 80
        )

        print(
            f"TEST {test_id}"
        )

        print(
            f"Category: {category}"
        )

        print(
            f"Question: {question}"
        )

        print(
            "-" * 80
        )

        try:
            sql = None
            source = None

            if not refresh:
                sql = get_cached_sql(
                    cache=cache,
                    test_id=test_id,
                    question=question,
                )

            if sql is not None:
                source = (
                    "BENCHMARK CACHE"
                )

                cache_hits += 1

            elif cached_only:
                print(
                    "[ERROR] No cached SQL available."
                )

                errors += 1

                continue

            else:
                if service is None:
                    service = QueryService()

                result = service.generate_sql(
                    question
                )

                sql = extract_sql(
                    result
                )

                source = (
                    "FRESH QUERY SERVICE"
                )

                fresh_generations += 1

                store_cached_sql(
                    cache=cache,
                    test_id=test_id,
                    question=question,
                    sql=sql,
                )

                save_benchmark_cache(
                    cache
                )

            print(
                f"Source: {source}"
            )

            print(
                "SQL:"
            )

            print(
                sql
            )

            success, evaluation_errors = (
                evaluate_case(
                    sql,
                    expectations,
                )
            )

            if success:
                print(
                    "[PASS]"
                )

                passed += 1

            else:
                print(
                    "[FAIL]"
                )

                for error in evaluation_errors:
                    print(
                        f"  - {error}"
                    )

                failed += 1

        except Exception as exc:
            print(
                "[ERROR]"
            )

            print(
                f"  - {type(exc).__name__}: {exc}"
            )

            errors += 1

    print()

    print(
        "=" * 80
    )

    print(
        "V2 BENCHMARK SUMMARY"
    )

    print(
        "=" * 80
    )

    print(
        f"PASSED: {passed}"
    )

    print(
        f"FAILED: {failed}"
    )

    print(
        f"ERRORS: {errors}"
    )

    print(
        f"TOTAL: {total}"
    )

    print(
        f"CACHE HITS: {cache_hits}"
    )

    print(
        "FRESH QUERY SERVICE GENERATIONS: "
        f"{fresh_generations}"
    )

    if total:
        accuracy = (
            passed
            / total
        ) * 100

        print(
            f"SEMANTIC ACCURACY: "
            f"{accuracy:.2f}%"
        )

    print(
        "=" * 80
    )

    if (
        failed == 0
        and errors == 0
    ):
        return 0

    return 1


# =========================================================
# CLI
# =========================================================


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "SQL generalization benchmark V2. "
            "No LLM call is made unless --test, --tests, "
            "or --all is explicitly selected."
        )
    )

    selection = parser.add_mutually_exclusive_group()

    selection.add_argument(
        "--test",
        type=int,
        help=(
            "Run one benchmark test."
        ),
    )

    selection.add_argument(
        "--tests",
        type=parse_test_numbers,
        help=(
            "Run selected tests, for example "
            "--tests 7,10,21."
        ),
    )

    selection.add_argument(
        "--all",
        action="store_true",
        help=(
            "Run all 40 V2 tests."
        ),
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help=(
            "List all benchmark cases. "
            "Does not invoke QueryService."
        ),
    )

    cache_mode = parser.add_mutually_exclusive_group()

    cache_mode.add_argument(
        "--cached",
        action="store_true",
        help=(
            "Use benchmark-cached SQL only. "
            "Never invoke QueryService."
        ),
    )

    cache_mode.add_argument(
        "--refresh",
        action="store_true",
        help=(
            "Ignore benchmark cache and generate fresh SQL "
            "for selected cases."
        ),
    )

    return parser


def main() -> int:
    validate_definition()

    parser = build_argument_parser()

    args = parser.parse_args()

    if args.list:
        list_tests()

        return 0

    try:
        selected_cases = get_selected_tests(
            single_test=args.test,
            multiple_tests=args.tests,
            run_all=args.all,
        )

    except ValueError as exc:
        parser.error(
            str(exc)
        )

    if not selected_cases:
        print(
            "V2 benchmark definition valid."
        )

        print(
            f"Tests: {len(V2_TEST_CASES)}"
        )

        print(
            f"Expectations: {len(V2_EXPECTATIONS)}"
        )

        print()

        print(
            "No benchmark tests selected."
        )

        print(
            "Use --list, --test N, --tests N,N,..., "
            "or --all."
        )

        print(
            "No QueryService/LLM call was made."
        )

        return 0

    return run_benchmark(
        selected_cases=selected_cases,
        cached_only=args.cached,
        refresh=args.refresh,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )