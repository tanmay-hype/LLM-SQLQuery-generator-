from app.core.database import engine

from app.schema.schema_loader import SchemaLoader
from app.schema.models.schema_document import SchemaDocumentBuilder

from app.services.intent_detector import IntentDetector


QUESTIONS = [
    "List customer names and emails",
    "Show customers from Delhi",
    "Show customers and the products they purchased",
]


def main():

    loader = SchemaLoader(
        engine
    )

    schema = loader.load_schema()

    document_builder = (
        SchemaDocumentBuilder()
    )

    documents = (
        document_builder.build_documents(
            schema
        )
    )

    intent_detector = (
        IntentDetector()
    )

    print("=" * 80)
    print("GENERALIZATION FAILURE TRACE")
    print("=" * 80)

    for question in QUESTIONS:

        print()
        print("=" * 80)
        print("QUESTION:", question)
        print("=" * 80)

        intent = intent_detector.detect(
            question
        )

        print()
        print("INTENT")
        print("-" * 80)

        print(
            "PRIMARY:",
            intent.primary,
        )

        print(
            "SECONDARY:",
            intent.secondary,
        )

        print(
            "SCORES:",
            intent.scores,
        )

        print(
            "CONFIDENCE:",
            intent.confidence,
        )

        print()
        print("SCHEMA DOCUMENTS")
        print("-" * 80)

        for document in documents:

            print()
            print(
                "TABLE:",
                document.table_name,
            )

            print(
                document.content
            )


if __name__ == "__main__":
    main()