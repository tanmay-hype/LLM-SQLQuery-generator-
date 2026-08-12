from app.core.database import engine

from app.schema.schema_loader import SchemaLoader
from app.schema.schema_document_builder import SchemaDocumentBuilder
from app.schema.schema_retriever import SchemaRetriever
from app.schema.compression.schema_compressor import SchemaCompressor
from app.schema.schema_formatter import SchemaFormatter

from app.schema.embeddings.gemini_embedding_service import (
    GeminiEmbeddingService,
)
from app.schema.vector_store.faiss_store import FAISSVectorStore
from app.schema.indexing.schema_index_service import (
    SchemaIndexService,
)

from app.schema.retrievers.keywords_retriever import (
    KeywordRetriever,
)
from app.schema.retrievers.semantic_retriever import (
    SemanticRetriever,
)

from app.services.intent_detector import IntentDetector

from app.llm.prompt_builder import PromptBuilder
from app.llm.prompt_examples.repository import ExampleRepository
from app.llm.prompt_examples.retriever import ExampleRetriever


QUESTIONS = [
    "Show customer names and email addresses",
    "Which products were ordered?",
    "Show total order amount per customer",
    "Show monthly order trends",
]


def main():

    print("=" * 60)
    print("PROMPT PIPELINE TEST")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Load database schema
    # --------------------------------------------------

    print("\n[1] Loading database schema...")

    loader = SchemaLoader(engine)

    schema = loader.load_schema()

    print(
        f"Tables found: {list(schema.keys())}"
    )

    # --------------------------------------------------
    # 2. Build schema documents
    # --------------------------------------------------

    print("\n[2] Building schema documents...")

    document_builder = SchemaDocumentBuilder()

    documents = document_builder.build(schema)

    print(
        f"Documents created: {len(documents)}"
    )

    # --------------------------------------------------
    # 3. Initialize Gemini embedding service
    # --------------------------------------------------

    print(
        "\n[3] Initializing Gemini embedding service..."
    )

    embedding_service = GeminiEmbeddingService()

    print("Embedding service: OK")

    # --------------------------------------------------
    # 4. Initialize FAISS
    # --------------------------------------------------

    print(
        "\n[4] Initializing FAISS vector store..."
    )

    vector_store = FAISSVectorStore()

    print("FAISS vector store: OK")

    # --------------------------------------------------
    # 5. Initialize schema index
    # --------------------------------------------------

    print(
        "\n[5] Initializing schema index service..."
    )

    schema_index_service = SchemaIndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    schema_index_service.initialize(documents)

    print("Semantic index: OK")

    # --------------------------------------------------
    # 6. Create individual retrievers
    # --------------------------------------------------

    print(
        "\n[6] Creating schema retrievers..."
    )

    keyword_retriever = KeywordRetriever()

    semantic_retriever = SemanticRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    print("Keyword retriever: OK")
    print("Semantic retriever: OK")

    # --------------------------------------------------
    # 7. Create hybrid SchemaRetriever
    # --------------------------------------------------

    schema_retriever = SchemaRetriever(
        retrievers=[
            keyword_retriever,
            semantic_retriever,
        ]
    )

    print("Hybrid schema retriever: OK")
    print("RRF fusion: OK")

    # --------------------------------------------------
    # 8. Create intent detector
    # --------------------------------------------------

    print(
        "\n[7] Creating intent detector..."
    )

    intent_detector = IntentDetector()

    print("Intent detector: OK")

    # --------------------------------------------------
    # 9. Create compressor
    # --------------------------------------------------

    print(
        "\n[8] Creating schema compressor..."
    )

    compressor = SchemaCompressor()

    print("Schema compressor: OK")

    # --------------------------------------------------
    # 10. Create formatter
    # --------------------------------------------------

    print(
        "\n[9] Creating schema formatter..."
    )

    formatter = SchemaFormatter()

    print("Schema formatter: OK")

    # --------------------------------------------------
    # 11. Create example retriever
    # --------------------------------------------------

    print(
        "\n[10] Creating example retriever..."
    )

    repository = ExampleRepository()

    example_retriever = ExampleRetriever(
        repository
    )

    print("Example retriever: OK")

    # --------------------------------------------------
    # 12. Create PromptBuilder
    # --------------------------------------------------

    print(
        "\n[11] Creating prompt builder..."
    )

    prompt_builder = PromptBuilder()

    print("Prompt builder: OK")

    # --------------------------------------------------
    # 13. Run prompt pipeline
    # --------------------------------------------------

    for question in QUESTIONS:

        print("\n")
        print("=" * 60)
        print(f"QUESTION: {question}")
        print("=" * 60)

        # --------------------------------------------------
        # Intent
        # --------------------------------------------------

        intent = intent_detector.detect(question)

        print("\n[Intent]")
        print(
            f"Primary: {intent.primary}"
        )
        print(
            f"Secondary: {intent.secondary}"
        )

        # --------------------------------------------------
        # Hybrid retrieval
        # --------------------------------------------------

        retrieved_schema = schema_retriever.retrieve(
            schema=schema,
            question=question,
            documents=documents,
        )

        print("\n[Retrieved Tables]")

        if not retrieved_schema:
            print("No tables retrieved.")
        else:
            for table_name in retrieved_schema:
                print(f"- {table_name}")

        # --------------------------------------------------
        # Schema compression
        # --------------------------------------------------

        compressed_schema = compressor.compress(
            schema=retrieved_schema,
            question=question,
            intent=intent,
        )

        print("\n[Compressed Schema]")

        for table_name, table in compressed_schema.items():

            columns = [
                column["name"]
                for column in table.get(
                    "columns",
                    [],
                )
            ]

            print(
                f"- {table_name}: {columns}"
            )

        # --------------------------------------------------
        # Schema formatting
        # --------------------------------------------------

        formatted_schema = formatter.format(
            compressed_schema
        )

        print("\n[Formatted Schema]")
        print(formatted_schema)

        # --------------------------------------------------
        # Example retrieval
        # --------------------------------------------------

        examples = example_retriever.retrieve(
            analysis=intent
        )

        print("\n[Examples]")

        if not examples:
            print("No examples retrieved.")

        else:
            for example in examples:
                print(
                    f"- {example.question}"
                )

        # --------------------------------------------------
        # Prompt construction
        # --------------------------------------------------

        prompt = prompt_builder.build_prompt(
            schema=formatted_schema,
            user_question=question,
            intent=intent,
            examples=examples,
        )

        # --------------------------------------------------
        # Final prompt
        # --------------------------------------------------

        print("\n")
        print("=" * 60)
        print("FINAL PROMPT")
        print("=" * 60)

        print(prompt)

    print("\n")
    print("=" * 60)
    print("PROMPT PIPELINE TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()