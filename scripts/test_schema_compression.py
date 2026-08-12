from app.core.database import engine
from app.schema.schema_loader import SchemaLoader
from app.schema.compression.schema_compressor import SchemaCompressor
from app.services.intent_detector import IntentDetector


def main():
    print("\n" + "=" * 60)
    print("SCHEMA COMPRESSION TEST")
    print("=" * 60)

    print("\n[1] Loading database schema...")
    loader = SchemaLoader(engine)
    schema = loader.load_schema()

    print(f"Tables found: {list(schema.keys())}")

    compressor = SchemaCompressor()
    intent_detector = IntentDetector()

    questions = [
        "Show customer names and email addresses",
        "Which products were ordered?",
        "Show total order amount per customer",
        "Show monthly order trends",
    ]

    for question in questions:
        print("\n" + "-" * 60)
        print(f"Question: {question}")
        print("-" * 60)

        intent = intent_detector.detect(question)

        print(f"Intent: {intent.primary}")

        compressed = compressor.compress(
            schema=schema,
            question=question,
            intent=intent,
        )

        for table_name, table in compressed.items():
            columns = [
                column["name"]
                for column in table.get("columns", [])
            ]

            print(f"\nTable: {table_name}")
            print(f"Columns kept: {columns}")
            print(f"Primary keys: {table.get('primary_keys')}")
            print(f"Foreign keys: {table.get('foreign_keys')}")

    print("\n" + "=" * 60)
    print("SCHEMA COMPRESSION TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()