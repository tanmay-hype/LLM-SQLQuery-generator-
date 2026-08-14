from app.services.query_service import QueryService


def main():
    service = QueryService()

    questions = [
        "Show all customers",
        "Which customers have placed orders?",
        "Show total order amount per customer",
        "Show monthly order trends",
        "Show the most recent orders",
        "Show top customers",
        "Compare customer spending",
    ]

    print("\n" + "=" * 80)
    print("FULL QUERY SERVICE PIPELINE TEST")
    print("=" * 80)

    for question in questions:

        print("\n" + "=" * 80)
        print(f"QUESTION: {question}")
        print("=" * 80)

        try:
            response = service.generate_sql(question)

            print("\nGENERATED SQL:")
            print("-" * 80)
            print(response.sql)

            print("\nRESULTS:")
            print("-" * 80)

            if response.results:
                for row in response.results:
                    print(row)
            else:
                print("No results returned.")

        except Exception as exc:
            print("\nERROR:")
            print("-" * 80)
            print(type(exc).__name__)
            print(exc)


if __name__ == "__main__":
    main()