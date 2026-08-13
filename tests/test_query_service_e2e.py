import logging

from app.services.query_service import QueryService


logging.basicConfig(
    level=logging.INFO,
)


def run_test(service: QueryService, question: str) -> None:
    print("\n" + "=" * 70)
    print(f"QUESTION: {question}")
    print("=" * 70)

    try:
        response = service.generate_sql(question)

        print("\nGENERATED SQL:")
        print(response.sql)

        print("\nRESULTS:")
        print(response.results)

        print("\nSTATUS: PASSED")

    except Exception as exc:
        print("\nSTATUS: FAILED")
        print(f"ERROR: {type(exc).__name__}: {exc}")


def main() -> None:
    print("=" * 70)
    print("QUERY SERVICE END-TO-END TEST")
    print("=" * 70)

    service = QueryService()

    questions = [
        "Show all customers",
        "Show customer names and email addresses",
        "Which products were ordered?",
        "Show total order amount per customer",
        "Show monthly order trends",
        "Show the most recent orders",
        "Which customers have placed orders?",
    ]

    for question in questions:
        run_test(
            service=service,
            question=question,
        )


if __name__ == "__main__":
    main()